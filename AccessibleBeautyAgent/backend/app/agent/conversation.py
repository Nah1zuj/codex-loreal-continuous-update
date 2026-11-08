"""Ephemeral bounded context and real OpenAI-compatible streaming orchestration."""
import asyncio,hashlib,json,time,uuid
from collections import deque
from weakref import WeakValueDictionary
from datetime import datetime,timezone
from urllib.parse import urlsplit
from app.agent.tools import ToolRegistry
from app.agent.coaching import CommandConflict
from app.agent.coaching_intents import coaching_intent
from app.content.beauty_companion import STREAM_POLICY
from app.services.model_client import RemoteModelClient,ModelServiceError
from app.vision.evidence import fresh_visual_summary

SESSION_CONTROLS={'stop','停止','stop session','停止会话','stop camera','停止相机','关闭相机'}
COMMANDS={'','next','下一步','继续','skip','跳过','开始步骤','start routine','开始','我想开始步骤','开始化妆吧','请带我一步一步做','i want to start the steps','开始化妆','开始辅导','带我开始步骤','我想开始下一步','我做好了','我完成了','停止','stop','stop camera','停止相机','关闭相机','check this','检查','相机检查','check','帮我看看','check with camera','repeat','重复','slow down','慢一点','why','为什么','详细一点','概览','overview','summary'}

def _text_route(settings):
    provider = settings.model_provider
    if provider == 'deepseek':
        model, endpoint, key = settings.deepseek_model, settings.deepseek_base_url, settings.deepseek_api_key
    elif provider == 'openai_compatible':
        model, endpoint, key = settings.compatible_model, settings.compatible_base_url, settings.compatible_api_key
    elif provider == 'qwen':
        model, endpoint, key = settings.chat_model, settings.base_url, settings.api_key
    else:
        return provider, '', None
    fingerprint = None
    if settings.allow_remote_ai and model and endpoint and key:
        try:
            url = urlsplit(endpoint)
            if url.scheme in ('http', 'https') and url.hostname:
                fingerprint = hashlib.sha256(json.dumps((provider, model, endpoint, key)).encode()).digest()
        except ValueError:
            pass
    return provider, model, fingerprint

class ConversationService:
    def __init__(self,agent):
        self.agent=agent;self.turns={};self.locks=WeakValueDictionary()
        self.metrics=deque(maxlen=200);self.tools=ToolRegistry(agent)
        self._verified_text_route = None
        agent.on_preferences_deleted=self.clear_owner_context

    def remote_text_readiness(self):
        _, _, configured = _text_route(self.agent.settings)
        return configured is not None, configured is not None and configured == self._verified_text_route

    def clear_owner_context(self,user_id):
        for session in self.agent.sessions.sessions.values():
            if session.user_id==user_id:
                self.turns.pop(session.session_id,None)
                session.story_context=[]
                session.last_response=''
                session.last_tool_call=None
                session.tool_calls=[]
                session.memory_context_generation+=1

    def history(self,sid):
        session = self.agent.sessions.sessions.get(sid)
        if session and session.makeup_plan and self.agent.coaching.visible_plan(session) is None:
            return []
        return list(self.turns.get(sid,[]))
    def append(self,sid,role,text,locale):
        rows=self.turns.setdefault(sid,[])
        rows.append({'id':str(uuid.uuid4()),'session_id':sid,'role':role,'text':text[:4000],'language':locale,'timestamp':datetime.now(timezone.utc).isoformat()})
        while len(rows)>30 or sum(len(r['text']) for r in rows)>16000:rows.pop(0)
        # Bound inactive sessions as well; no implicit durable transcript.
        while len(self.turns)>200:self.turns.pop(next(iter(self.turns)))
    async def stream(self,body,request):
        s=self.agent.sessions.get(body.session_id) if body.session_id else self.agent.sessions.create(body.user_id)
        if body.locale:s.locale=body.locale
        if body.experience_mode:s.experience_mode=body.experience_mode
        lock = self.locks.get(s.session_id)
        if lock is None:
            lock = self.locks[s.session_id] = asyncio.Lock()
        async with lock:
            started=time.monotonic();first=None;usage=None;outcome='cancelled'
            diagnostics = {'provider': 'mock' if self.agent.settings.model_provider == 'mock' else 'local',
                           'remote_response_verified': False}
            remote_route = None
            remote_finished = False
            memory_generation=s.memory_context_generation
            yield {'type':'session','session_id':s.session_id,'session':{**self.agent.session_snapshot(s),'current_step':self.agent.current_step(s)}}
            text=body.message.strip()
            event_id=body.event_id or str(uuid.uuid4())
            body=body.model_copy(update={'event_id':event_id})
            try:
                if await request.is_disconnected():return
                if memory_generation!=s.memory_context_generation:
                    raise CommandConflict('MEMORY_CONTEXT_CHANGED','记忆已更新，请重新发送。 / Memory changed. Please retry.')
                legacy = bool(s.makeup_plan and s.makeup_plan.legacy_routine)
                intent = coaching_intent(text)
                session_control=(text.lower() in SESSION_CONTROLS or s.stage.value=='COMPLETE'
                                 or (intent=='finish' and s.makeup_plan and self.agent.coaching.visible_plan(s) is None))
                legacy_command = legacy and intent in ('start','advance','skip','pause','resume','finish','previous','blush','save')
                catalogue_start = s.makeup_plan is None and s.routine_id and intent in ('start','advance')
                with self.agent.sessions.lock:
                    coaching_result=self.agent.coaching.handle(s,body) if body.action=='message' and not (session_control or legacy or catalogue_start) else None
                    plan_version=(s.makeup_plan.id,s.makeup_plan.revision) if s.makeup_plan else None
                duplicate=bool(coaching_result and coaching_result.get('duplicate'))
                deferred_history = bool(session_control or legacy_command or catalogue_start)
                if text and not duplicate and not deferred_history:self.append(s.session_id,'user',text,s.locale)
                if coaching_result:
                    yield {'type':'session','session_id':s.session_id,'session':{**self.agent.session_snapshot(s),'current_step':self.agent.current_step(s)}}
                    if coaching_result.get('event'):
                        yield {'type':'committed','event':coaching_result['event'],'generation':'in_progress'}
                if intent=='ambiguous' and (s.makeup_plan or s.routine_id):
                    message=self.agent.coaching.reply_text(s,{'clarification_required':True},intent,text)
                    reply=self.agent.respond(s,message)
                    first=time.monotonic();yield {'type':'delta','text':message}
                elif session_control or legacy_command or catalogue_start or body.action!='message' or (not coaching_result and (self.agent.settings.model_provider=='mock' or text.lower().rstrip('。.!！?？') in COMMANDS or s.stage.value in ('MEMORY_CONSENT','COMPLETE'))):
                    reply=await asyncio.to_thread(self.agent.chat,body.model_copy(update={'session_id':s.session_id}))
                    duplicate = bool(reply.get('duplicate'))
                    if text and deferred_history and not duplicate:
                        self.append(s.session_id,'user',text,s.locale)
                    if reply.get('event'):
                        yield {'type':'committed','event':reply['event'],'generation':'in_progress'}
                        yield {'type':'session','session_id':s.session_id,'session':{**reply['session'],'current_step':reply['step']}}
                    first=time.monotonic();yield {'type':'delta','text':reply['message']}
                else:
                    if self.agent.settings.model_provider=='mock':
                        data=coaching_result
                        p=s.makeup_plan
                        message=self.agent.coaching.reply_text(s,data,intent,text)
                        reply=self.agent.respond(s,message);first=time.monotonic();yield {'type':'delta','text':message}
                        if data.get('summary'):
                            self.agent.coaching.mark_summary_presented(s,p.revision)
                            reply=self.agent.respond(s,message)
                        if not duplicate:self.append(s.session_id,'agent',message,s.locale)
                        outcome='complete';yield {'type':'final','reply':reply,'diagnostics':diagnostics};return
                    step=self.agent.current_step(s) or {}
                    evidence=fresh_visual_summary(s.visual_state)
                    context={
                        'scene':s.scene,'selected_look':s.selected_look,
                        'current_step':{key:step[key] for key in ('name','instruction','review_status') if key in step},
                        'visual_observation':(
                            {'available':True,'scope':'local_only'}
                            if evidence and s.visual_state.get('task')=='local_region_measurement'
                            else evidence
                        ),
                        'confirmed_preferences':self.agent.memory.profile(s.user_id)['profile'],
                    }
                    policy=STREAM_POLICY+'\nReply as plain text entirely in '+('Chinese' if s.locale=='zh-CN' else 'English')+'.'
                    proposal_version=None
                    if coaching_result:
                        operation={key:coaching_result[key] for key in (
                            'state_unchanged','needs_start_confirmation','clarification','visual_request',
                        ) if key in coaching_result}
                        if s.makeup_plan:
                            operation.update(status=s.makeup_plan.status,workflow=s.makeup_plan.workflow,
                                             name=s.makeup_plan.name,knowledge_status=s.makeup_plan.knowledge_status)
                        if summary:=coaching_result.get('summary'):
                            operation['completed_steps']=summary['completed_steps']
                        if coaching_result.get('saved'):
                            operation['journal_saved']=True
                        if coaching_result.get('needs_start_confirmation'):
                            proposal_version=plan_version
                            operation['lesson_ids_by_step']=self.agent.coaching.proposal_options(s)
                        policy+='\nCOACHING_OPERATION='+json.dumps(operation,ensure_ascii=False)
                    policy+='\nCURRENT_CONTEXT='+json.dumps(context,ensure_ascii=False)
                    canonical_narration=bool(coaching_result and not coaching_result.get('state_unchanged'))
                    messages=[{'role':'system','content':policy}]+[{'role':'assistant' if r['role']=='agent' else 'user','content':r['text']} for r in self.history(s.session_id)]
                    settings = self.agent.settings.model_copy()
                    provider, model, remote_route = _text_route(settings)
                    if not canonical_narration:
                        diagnostics['provider'] = provider
                    client = RemoteModelClient(settings, provider)
                    answer=''
                    for round_id in range(3):
                        calls={};round_text='';round_usage=None;finish_reason=None
                        async for chunk in client.stream_chat(model,messages,self.tools.definitions(proposal_version is not None) if round_id<2 else None):
                            if await request.is_disconnected():return
                            if memory_generation!=s.memory_context_generation:
                                raise CommandConflict('MEMORY_CONTEXT_CHANGED','记忆已更新，请重新发送。 / Memory changed. Please retry.')
                            if chunk.get('usage'):round_usage=chunk['usage']
                            choices=chunk.get('choices',[])
                            delta=choices[0].get('delta',{}) if choices else {}
                            if choices and choices[0].get('finish_reason'):
                                finish_reason=choices[0]['finish_reason']
                            part=delta.get('content') or ''
                            if part:
                                answer+=part;round_text+=part
                                if len(answer)>6000:raise RuntimeError('Reply exceeded safety limit')
                                if not canonical_narration:
                                    if first is None:first=time.monotonic()
                                    yield {'type':'delta','text':part}
                            for call in delta.get('tool_calls',[]):
                                if len(calls)>=4 and call['index'] not in calls:raise RuntimeError('Too many tool calls')
                                item=calls.setdefault(call['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
                                if call.get('id'):item['id']=call['id']
                                for field in ('name','arguments'):item['function'][field]+=call.get('function',{}).get(field,'')
                                if len(item['function']['arguments'])>4000:raise RuntimeError('Tool arguments too long')
                        if round_usage:
                            if usage is None:usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'rounds':[]}
                            usage['rounds'].append(round_usage)
                            for key in ('prompt_tokens','completion_tokens','total_tokens'):
                                usage[key]+=round_usage.get(key,0)
                        if not calls:
                            # A clean EOF alone can leave an incomplete provider answer.
                            remote_finished = not canonical_narration and finish_reason == 'stop' and bool(round_text.strip())
                            break
                        messages.append({'role':'assistant','content':round_text or None,'tool_calls':list(calls.values())})
                        for call in calls.values():
                            try:args=json.loads(call['function']['arguments'])
                            except ValueError:args=None
                            # Only retrieval can involve remote embeddings. Mutable local
                            # tools execute synchronously, so cancellation cannot leave a
                            # background thread advancing a session after interruption.
                            if call['function']['name']=='search_knowledge':
                                try:result=await asyncio.wait_for(asyncio.to_thread(self.tools.execute,s,call['function']['name'],args,text,model_call=True),timeout=self.agent.settings.remote_timeout)
                                except TimeoutError:result={'ok':False,'error':'tool_timeout'}
                            else:result=self.tools.execute(s,call['function']['name'],args,user_text=text,event_id=event_id,
                                                           expected_step_id=body.expected_step_id,
                                                           expected_plan_id=body.expected_plan_id,expected_revision=body.expected_revision,
                                                           model_call=True,proposal_version=proposal_version)
                            if call['function']['name']=='propose_makeup_course':
                                proposal_version=None
                                if result['ok']:
                                    new_version=(s.makeup_plan.id,s.makeup_plan.revision)
                                    if new_version!=plan_version:
                                        plan_version=new_version
                                        yield {'type':'session','session_id':s.session_id,
                                               'session':{**self.agent.session_snapshot(s),'current_step':self.agent.current_step(s)}}
                            yield {'type':'tool','name':call['function']['name'],'ok':result['ok']}
                            messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result,ensure_ascii=False)})
                    if not answer.strip() and not canonical_narration:raise RuntimeError('Text service returned no answer')
                    with self.agent.sessions.lock:
                        if memory_generation!=s.memory_context_generation:
                            raise CommandConflict('MEMORY_CONTEXT_CHANGED','记忆已更新，请重新发送。 / Memory changed. Please retry.')
                        if plan_version and (
                            s.makeup_plan is None or (s.makeup_plan.id,s.makeup_plan.revision)!=plan_version
                        ):
                            raise CommandConflict('STALE_REPLY','教学进度已变化。请读取最新步骤。')
                        if canonical_narration:
                            answer=self.agent.coaching.reply_text(s,coaching_result,intent,text)
                        reply=self.agent.respond(s,answer)
                    if canonical_narration:
                        if first is None:first=time.monotonic()
                        yield {'type':'delta','text':answer}
                if await request.is_disconnected():return
                with self.agent.sessions.lock:
                    if memory_generation!=s.memory_context_generation:
                        raise CommandConflict('MEMORY_CONTEXT_CHANGED','记忆已更新，请重新发送。 / Memory changed. Please retry.')
                    if coaching_result and coaching_result.get('summary'):
                        self.agent.coaching.mark_summary_presented(s,coaching_result['plan']['revision'])
                        reply=self.agent.respond(s,reply['message'])
                    if not duplicate:self.append(s.session_id,'agent',reply['message'],s.locale)
                if remote_route is not None and remote_finished:
                    diagnostics['remote_response_verified'] = True
                    if remote_route == _text_route(self.agent.settings)[2]:
                        self._verified_text_route = remote_route
                outcome='complete';yield {'type':'final','reply':reply,'diagnostics':diagnostics}
            except CommandConflict as error:
                outcome='failed';yield {'type':'error','code':error.code,'message':str(error)}
            except (RuntimeError,PermissionError,ValueError,KeyError) as error:
                message=error.public_message if isinstance(error,ModelServiceError) and s.locale=='zh-CN' else ('对话暂时不可用，请重试。已有步骤仍可阅读。' if s.locale=='zh-CN' else 'Conversation unavailable. Retry; existing steps remain readable.')
                outcome='failed';yield {'type':'error','message':message}
            finally:
                self.metrics.append({'session_id':s.session_id,'first_token_ms':round((first-started)*1000) if first else None,'total_ms':round((time.monotonic()-started)*1000),'outcome':outcome,'usage':usage,**diagnostics})
