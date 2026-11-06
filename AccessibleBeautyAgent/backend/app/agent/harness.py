from app.content.locale import localize_view
from app.schemas.models import Stage,Intent
from app.schemas.full_look import RevisionRequest
from app.full_look.service import FullLookService
from app.policies.registry import PolicyRegistry
from app.agent.coaching import CoachingController, RoutineUnavailable
from app.agent.providers import MockLanguageProvider, QwenLanguageProvider,DeepSeekLanguageProvider,OpenAICompatibleLanguageProvider

class AgentHarness:
    """Deterministic orchestrator. Models parse intention and explain current steps.

    All consent comes from dedicated actions, never model interpretation.
    Trace records exclude image bytes and persist nowhere.
    """
    def __init__(self, settings, sessions, store, retriever, looks, products, memory, vision):
        self.settings, self.sessions, self.store = settings, sessions, store
        self.retriever, self.looks, self.products = retriever, looks, products
        self.memory, self.vision = memory, vision
        self.policies=PolicyRegistry()
        self.coaching=CoachingController(self)
        self.full_look=FullLookService(self)
        providers={'mock':MockLanguageProvider,'deepseek':DeepSeekLanguageProvider,'qwen':QwenLanguageProvider,'openai_compatible':OpenAICompatibleLanguageProvider}
        self.language=providers[settings.model_provider]() if settings.model_provider=='mock' else providers[settings.model_provider](settings)

    def record(self, s, tool, args, result):
        trace = {'tool':tool,'arguments':args,'result':result}
        s.last_tool_call = trace
        s.tool_calls.append(trace)
        s.tool_calls = s.tool_calls[-30:]
        return result

    def get_user_profile(self, user_id):
        return self.memory.profile(user_id)
    def retrieve_look(self, scene, desired_impression, avoid, preferences):
        return self.looks.search(scene, desired_impression, avoid, preferences)
    def retrieve_products(self, look_id, scene, preferences):
        return self.products.search(look_id, scene, preferences)
    def compare_products(self, product_ids):
        return self.products.compare(product_ids)

    def disable_routine(self, session):
        session.routine_unavailable = True
        self.sessions.stop(session)
        raise RoutineUnavailable('知识或流程已更新/停用，请重新开始会话并选择妆容。')

    def require_available_routine(self, routine_id, session, *, expected_version=None, expected_look=None):
        from app.knowledge.policy import eligible
        routine = self.store.routine_map.get(routine_id)
        look = self.store.look_map.get(expected_look or session.selected_look)
        if (not routine or not look or routine['look_id'] != look['look_id'] or not eligible(routine, self.settings)
                or not eligible(look, self.settings) or routine_id not in look['routine_ids']
                or (expected_version is not None and routine['version'] != expected_version)):
            self.disable_routine(session)
        return routine

    def routine_command(self, session, action, request, *, routine_id=None, compatible_next=False):
        """Translate catalogue entry points into the shared command transaction."""
        with self.sessions.lock:
            if routine_id and routine_id not in self.store.routine_map:
                raise KeyError('Routine not found')
            initial = None
            if not session.makeup_plan:
                if action != 'start' and not (action == 'advance' and compatible_next):
                    raise ValueError('请先开始步骤。')
                if session.stage not in (Stage.LOOK_SELECTED, Stage.VERIFY):
                    raise ValueError('当前阶段不能开始流程。')
                chosen_id = routine_id or session.routine_id
                if chosen_id and chosen_id in self.store.routine_map:
                    if self.store.routine_map[chosen_id]['look_id'] != session.selected_look:
                        raise ValueError('Routine does not match selected look')
                initial = self.coaching.legacy_plan(session, chosen_id)
            elif routine_id and routine_id != session.routine_id:
                raise ValueError('Routine does not match active plan')
            return self.coaching.act(
                session, action, request.event_id, request.expected_step_id,
                expected_plan_id=request.expected_plan_id, expected_revision=request.expected_revision,
                compatible_next=compatible_next, initial_plan=initial,
            )

    def start_routine(self, routine_id, session):
        # Internal compatibility entry used by catalogue tooling.
        from app.schemas.models import RoutineRequest
        request = RoutineRequest(session_id=session.session_id)
        return self.routine_command(session, 'start', request, routine_id=routine_id)['step']

    def select_routine(self, session, look):
        session.selected_look = look['look_id']
        session.routine_id = look['routine_id']
        session.proposed_routine_step_count = len(self.store.routine_map.get(session.routine_id, {}).get('steps', ()))

    def current_step(self, session):
        return self.coaching.current(session)

    def run_visual_check(self, task, images, session_context, demo=False):
        s = self.sessions.get(session_context['session_id'])
        if not s.camera_consent:
            raise PermissionError('请先明确同意相机检查。')
        if s.stage not in (Stage.VISION_GATE,Stage.VERIFY):
            raise ValueError('请先请求视觉检查并确认相机同意。')
        if s.stage == Stage.VERIFY:
            self.sessions.transition(s,Stage.CHECK_REQUESTED)
            self.sessions.transition(s,Stage.CAMERA_CONSENT)
            self.sessions.transition(s,Stage.VISION_GATE)
        try:
            result = self.vision.check(task,images,session_context,demo)
        except Exception:
            # Retry after provider failure requires fresh consent.
            s.camera_consent = False
            self.sessions.transition(s,Stage.CAMERA_CONSENT)
            raise
        if result['visual']:
            self.sessions.transition(s,Stage.VISION_CHECK)
            s.visual_state = result['visual']
            s.confidence = result['visual']['confidence']
            self.sessions.transition(s,Stage.VERIFY)
        else:
            s.visual_state = None
            s.confidence = 0
            self.sessions.transition(s,Stage.CAMERA_CONSENT)
        # Active video consent lasts until explicit stop; failures always require fresh consent.
        s.camera_consent = session_context.get("capture_kind") == "video_sample" and result["visual"] is not None
        s.last_response = result['message']
        return self.record(s,'run_visual_check',{'task':task,'frame_count':len(images) if session_context.get('capture_kind')=='video_sample' else 3,'demo':demo},result)

    def log_feedback(self, user_id, session_id, feedback):
        s = self.sessions.get(session_id)
        if s.user_id != user_id:
            raise PermissionError('User does not own session')
        if s.stage != Stage.FEEDBACK:
            raise ValueError('请先完成或跳过流程，再提供偏好反馈。')
        candidate = self.propose_memory_update(feedback)
        candidate['context'] = s.scene or 'unspecified'
        self.prepare_session_preference(s,candidate)
        self.sessions.transition(s,Stage.MEMORY_CONSENT)
        return self.record(s,'log_feedback',{'session_id':session_id},candidate)

    def propose_memory_update(self, feedback):
        candidate = {'feedback':feedback,'preferred_finish':[],'avoid':[]}
        if any(x in feedback.lower() for x in ('太强','淡一点','too strong','低饱和')):
            candidate['preferred_saturation'] = 'low'
        if any(x in feedback.lower() for x in ('自然','natural')):
            candidate['preferred_finish'] = ['natural']
        if 'heavy_gloss' in feedback or '太亮' in feedback:
            candidate['avoid'] = ['heavy_gloss']
        return candidate
    def prepare_session_preference(self,s,candidate):
        preview=self.memory.prepare(s.user_id,candidate,scope=f'session:{s.session_id}')
        s.memory_candidate=preview['candidate']
        s.memory_candidate_id=preview['candidate_id']
        s.memory_candidate_version=preview['candidate_version']

    def delete_memory(self, user_id, memory_id, explicit_consent):
        with self.sessions.lock:
            result=self.memory.delete(user_id,memory_id,explicit_consent)
            callback=getattr(self,'on_preferences_deleted',None)
            if callback:
                callback(user_id)
            return result

    def respond(self, s, message, *, remember=True):
        step = self.current_step(s)
        if remember:
            s.last_response = message
        canonical={'message':message,'session':s.model_dump(),'step':step}
        return {**localize_view({**canonical,'mode':self.settings.model_provider},s.locale),'canonical':canonical}

    def duplicate_reply(self, session, result):
        if result.get('saved'):
            message = '这份私人日志已保存。' if session.locale == 'zh-CN' else 'This private journal entry was already saved.'
            return {**self.respond(session, message, remember=False), 'saved':True,
                    'record_id':result['id'], 'duplicate':True}
        message = '这项操作已提交。' if session.locale == 'zh-CN' else 'This command was already applied.'
        reply = self.respond(session, message, remember=False)
        if session.makeup_plan and session.makeup_plan.status == 'completed':
            reply['summary'] = self.coaching.summary(session)
        return {**reply, 'event':result['event'], 'duplicate':True}

    def chat(self, request):
        s = self.sessions.get(request.session_id) if request.session_id else self.sessions.create(request.user_id)
        if request.experience_mode is not None:s.experience_mode=request.experience_mode
        if request.locale is not None:s.locale=request.locale
        text = request.message.strip()
        if text:s.story_context=(s.story_context+[text[:1000]])[-10:]
        command = text.lower()
        from app.agent.coaching_intents import coaching_intent
        normalized=coaching_intent(text)
        ending = command in ('stop','停止','stop session','停止会话')
        if s.stage == Stage.COMPLETE and request.action=='message' and not ending:
            return self.respond(s,'本次会话已经结束。可以开始新会话。' if s.locale=='zh-CN' else 'This session has ended. You can start a new session.')
        legacy = bool(s.makeup_plan and s.makeup_plan.legacy_routine)
        if s.makeup_plan and not legacy and text and request.action=='message' and command not in ('stop','停止','stop session','停止会话','stop camera','停止相机','关闭相机','check this','check with camera'):
            import json
            result=self.coaching.handle(s,request)
            if result and result.get('duplicate'):
                return self.duplicate_reply(s, result)
            if self.settings.model_provider == 'mock' or result.get('clarification_required'):
                message = self.coaching.reply_text(s, result, normalized, text)
            else:
                message = self.language.companion(text, json.dumps(result, ensure_ascii=False), s.locale)
            if result.get('summary'):
                self.coaching.mark_summary_presented(s, result['plan']['revision'])
            reply = self.respond(s, message)
            if result.get('event'):
                reply['event'] = result['event']
            if result.get('summary'):
                reply['summary'] = result['summary']
            return reply
        if not s.makeup_plan or legacy:
            command = {'repeat':'重复', 'visual':'check this'}.get(normalized, command)
        if request.action == 'camera_consent':
            if s.stage != Stage.CAMERA_CONSENT and not (request.consent is False and s.camera_consent):
                raise ValueError('当前没有待确认的相机请求。')
            if request.consent is None:
                raise ValueError('请明确选择同意或拒绝。')
            s.camera_consent = request.consent
            self.sessions.transition(s,Stage.VISION_GATE if request.consent else (Stage.GUIDE if s.routine_started else Stage.LOOK_SELECTED))
            return self.respond(s,'已允许本次本地演示检查。' if request.consent else '已拒绝检查，可以继续步骤。')
        if request.action == 'memory_consent':
            if request.consent is None:
                raise ValueError('请明确选择保存或不保存。')
            scope=f'session:{s.session_id}'
            if s.stage != Stage.MEMORY_CONSENT or not s.memory_candidate:
                if request.consent and self.memory.replay(
                    s.user_id,request.memory_candidate_id,request.memory_candidate_version,scope,
                ):
                    return self.respond(s,'已保存你同意的偏好。')
                raise ValueError('当前没有待确认的记忆候选。')
            if request.consent:
                if (request.memory_candidate_id!=s.memory_candidate_id
                        or request.memory_candidate_version!=s.memory_candidate_version):
                    raise ValueError('偏好候选已变更，请重新审阅。')
                saved=self.memory.save(s.user_id,s.memory_candidate,True,scope=scope,
                                       candidate_id=request.memory_candidate_id,
                                       candidate_version=request.memory_candidate_version)
                self.record(s,'save_memory',{'explicit_consent':True},saved)
            s.memory_consent=request.consent
            s.memory_candidate=None
            s.memory_candidate_id=None
            s.memory_candidate_version=None
            self.sessions.stop(s)
            return self.respond(s,'已保存你同意的偏好。今天的流程结束了。' if request.consent else '未保存长期偏好。今天的流程结束了。')
        if ending:
            operation = None
            if s.makeup_plan:
                operation = self.routine_command(s, 'end_session', request)
            elif s.stage != Stage.COMPLETE:
                self.sessions.stop(s)
            duplicate = bool(operation and operation.get('duplicate'))
            message = '会话已停止，相机已关闭。' if s.locale=='zh-CN' else 'The session has ended and camera access was revoked.'
            reply = self.respond(s, message, remember=not duplicate)
            if operation:
                reply.update(event=operation['event'], duplicate=duplicate)
            return reply
        if command in ('stop camera','停止相机','关闭相机'):
            s.camera_consent=False
            if s.stage in (Stage.CAMERA_CONSENT,Stage.VISION_GATE,Stage.VISION_CHECK,Stage.VERIFY):
                self.sessions.transition(s,Stage.GUIDE if s.routine_started else Stage.LOOK_SELECTED)
            return self.respond(s,'相机同意已撤回，摄像头关闭。')
        if s.stage == Stage.COMPLETE:
            return self.respond(s,'本次会话已经结束。可以开始新会话。')
        if command in ('check this','检查','相机检查','check','帮我看看','check with camera'):
            if s.stage not in (Stage.GUIDE,Stage.LOOK_SELECTED,Stage.VERIFY):
                return self.respond(s,'请先选择妆容方向，或处理当前同意请求。')
            if self.settings.vision_provider!='mock' or not self.settings.developer_mode:
                return self.respond(s,'请进入映照，明确允许本地单帧检查。' if s.locale=='zh-CN' else 'Open Reflect and allow a local single-frame check.')
            self.sessions.transition(s,Stage.CHECK_REQUESTED)
            self.sessions.transition(s,Stage.CAMERA_CONSENT)
            return self.respond(s,'是否体验一次本地模拟检查？演示不使用真实照片。' if s.locale=='zh-CN' else 'Would you like a local simulated check? This demo uses no real photos.')
        if request.experience_mode is not None and not text and s.last_response:
            return self.respond(s,s.last_response or self.full_look.summary(s))
        names={'cotton':('棉','cotton'),'linen':('亚麻','linen'),'wool':('羊毛','wool'),'silk':('丝绸','silk'),'satin':('缎面','satin'),'polyester':('聚酯','polyester'),'viscose':('粘胶','viscose','rayon'),'knit':('针织','knit')}
        material_ids=[key for key,words in names.items() if any(word in command for word in words)]
        if material_ids and any(word in command for word in ('比较','区别','解释','是什么','详细','compare','explain')):
            return self.respond(s,self.full_look.materials.explain(material_ids[:2])['message'])
        if s.todays_look and command in ('今日造型','整体造型','full look','today look','概览造型','把刚才的穿搭讲一遍','再讲穿搭','outfit summary'):
            return self.respond(s,self.full_look.summary(s,'outfit' if '穿搭' in command or command=='outfit summary' else None))
        if s.todays_look and any(x in command for x in ('不扎','发型','头发','黑色连衣裙','black dress','耳环','耳饰','配饰','项链','甜香','香水','香氛','透气','材质','棉质衬衫','棉衬衫','只要妆容','只做妆容','makeup only','缎面')):
            if any(x in command for x in ('什么材质','是什么面料','读吊牌','读一下这件衣服吊牌')):
                return self.respond(s,'目前无法从衣服照片确定纤维成分。可以在 DOT 读取成分/洗护标签；看不清百分比时会保持未知。')
            if any(x in command for x in ('记住','保存偏好')):
                self.full_look.memory_candidate(s,text)
                return self.respond(s,'请先查看这些偏好候选，再明确选择保存或不保存。')
            r=self.full_look.revise(s,RevisionRequest(session_id=s.session_id,user_request=text))
            message=' '.join(r['reasons'])+' '+' '.join(s.todays_look.pending_coordination)
            if s.todays_look.sections['outfit'].materials and any(x in command for x in ('透气','材质','缎面')):
                message+='\n'+self.full_look.materials.explain(s.todays_look.sections['outfit'].materials[:2])['message']
            return self.respond(s,message)
        step = self.current_step(s)
        if command in ('这一步做不了','替代方法','fallback') and step:return self.respond(s,self.policies.guidance(step,'fallback'))
        if command in ('概览所有步骤','概览','所有步骤','overview','summary'):
            if not s.routine_id:return self.respond(s,'请先选择妆容方向。')
            routine=self.require_available_routine(s.routine_id,s)
            return self.respond(s,'你可以一次听完概览，也可以每次只做一步。\n'+'\n'.join(str(i+1)+'. '+row['name']+'：'+row['instruction'] for i,row in enumerate(routine['steps'])))
        if command in ('repeat','重复','slow down','慢一点','why','为什么','详细一点'):
            if not step:
                return self.respond(s,s.last_response or '请先说明今天的使用场景。')
            field = 'instruction_repeat' if command in ('repeat','重复') else ('instruction_slow' if command in ('slow down','慢一点','详细一点') else 'explanation_why')
            return self.respond(s,self.policies.guidance(step,{'instruction_repeat':'repeat','instruction_slow':'expanded','explanation_why':'why'}[field]))
        if text and s.stage not in (Stage.MEMORY_CONSENT,Stage.COMPLETE) and any(word in command for word in ('全品类','欧莱雅','整套建议','full look recommendations','loreal','l’oréal')):
            return self.respond(s,self.language.companion(text,s.last_response+'\n'+'\n'.join(s.story_context)[-2000:],s.locale))
        if legacy and normalized == 'ambiguous':
            return self.respond(s, self.coaching.reply_text(s, {'clarification_required': True}, normalized, text))
        if legacy and normalized == 'save':
            saved = self.coaching.save(s, text)
            return {**self.respond(s, '私人记录已保存。' if s.locale == 'zh-CN' else 'Your private record was saved.'),
                    'saved': saved}
        if normalized in ('start', 'advance', 'skip', 'pause', 'resume', 'finish', 'previous', 'blush'):
            prefix = ''
            if not s.makeup_plan and s.stage in (Stage.INTENT, Stage.CLARIFY) and normalized in ('start', 'advance'):
                if not s.routine_id:
                    rows = self.retrieve_look('daily', ['natural'], [], self.get_user_profile(s.user_id)['profile'])
                    if not rows:
                        return self.respond(s, '暂时没有可用的基础流程。' if s.locale == 'zh-CN' else 'No basic routine is currently available.')
                    look = rows[0]['look']
                    self.select_routine(s, look)
                    s.scene = 'daily'
                self.sessions.transition(s, Stage.LOOK_SELECTED)
                prefix = ('先从简单的日常流程开始，你可以随时换方向或停止。\n' if s.locale == 'zh-CN'
                          else 'We can start with a simple everyday routine. Change direction or stop whenever you like.\n')
            if s.makeup_plan or s.stage in (Stage.LOOK_SELECTED, Stage.VERIFY):
                result = self.routine_command(s, normalized, request, compatible_next=True)
                if result.get('duplicate'):
                    return self.duplicate_reply(s, result)
                step = result['step']
                if s.makeup_plan.status == 'completed':
                    message = '流程结束。你希望下次保留或调整什么？' if s.locale == 'zh-CN' else 'Guidance has ended. What would you keep or change?'
                elif s.makeup_plan.workflow == 'PAUSED':
                    message = '已暂停，步骤保留。' if s.locale == 'zh-CN' else 'Paused. Your step is preserved.'
                else:
                    message = prefix + step['instruction']
                if s.makeup_plan.status == 'completed':
                    self.coaching.mark_summary_presented(s, s.makeup_plan.revision)
                reply = {**self.respond(s, message), 'event':result['event'], 'duplicate':False}
                if s.makeup_plan.status == 'completed':
                    reply['summary'] = self.coaching.summary(s)
                return reply
        if s.stage == Stage.FEEDBACK:
            if not text:
                return self.respond(s,'这次体验中，你希望下次保留或调整什么？')
            self.log_feedback(s.user_id,s.session_id,text)
            return self.respond(s,'我整理了下面的偏好候选。是否同意保存用于下次建议？你可以选择不保存。')
        if s.stage == Stage.MEMORY_CONSENT:
            return self.respond(s,'请使用“同意保存”或“不保存”按钮明确选择。')
        if s.stage in (Stage.INTENT,Stage.CLARIFY,Stage.LOOK_SELECTED):
            if not text:
                return self.respond(s,'欢迎。可以先聊聊今天的故事，或你希望拥有的感觉。' if s.locale=='zh-CN' else 'Welcome. Tell me about your day, or how you would like to feel.')
            if s.stage==Stage.LOOK_SELECTED:
                self.sessions.transition(s,Stage.INTENT)
            cafe=any(x in command for x in ('咖啡馆','咖啡店','cafe','café'))
            try:intent=self.language.understand(text)
            except RuntimeError:
                if not cafe:raise
                intent=Intent(scene='cafe_meeting',desired_impression=['natural','warm','refined'])
                self.record(s,'language_fallback',{'reason':'provider_unavailable'},{'status':'CURATED_DEMO'})
            if cafe:
                intent.scene='cafe_meeting'
                s.mood=[value for value,words in [('natural',('自然','natural')),('warm',('温暖','warm')),('refined',('正式','精致','精神','refined'))] if any(word in command for word in words)];s.formality='semi_formal' if any(word in command for word in ('正式','formal')) else None
                intent.desired_impression=list(dict.fromkeys(intent.desired_impression+['natural','warm','refined']))

            if not intent.scene:
                self.sessions.transition(s,Stage.CLARIFY)
                return self.respond(s,self.language.companion(text,s.last_response,s.locale))
            profile = self.record(s,'get_user_profile',{'user_id':s.user_id},self.get_user_profile(s.user_id))['profile']
            s.scene,s.desired_impression,s.avoid = intent.scene,intent.desired_impression,intent.avoid
            rows = self.record(s,'retrieve_look',intent.model_dump(),self.retrieve_look('dinner' if s.scene=='cafe_meeting' else s.scene,s.desired_impression,s.avoid,profile))
            if not rows:
                self.sessions.transition(s,Stage.CLARIFY)
                return self.respond(s,'目前没有匹配的妆容知识，暂时无法提供可靠建议。')
            look = next((row['look'] for row in rows if row['look']['look_id']=='soft_formal'),rows[0]['look']) if cafe else rows[0]['look']
            self.select_routine(s, look)
            s.selected_products = self.record(s,'retrieve_products',{'look_id':look['look_id']},self.retrieve_products(look['look_id'],s.scene,profile))
            rag = self.retriever.search(text+' '+s.scene,{'look_id':look['look_id']})
            s.rag_documents = rag['results']
            self.record(s,'rag_search',{'query':text,'look_id':look['look_id']},rag)
            self.sessions.transition(s,Stage.LOOK_SELECTED)
            if cafe:self.full_look.plan(s)
            label = '示例知识建议：' if look['source_type']=='sample' else '知识库建议：'
            conversation=self.language.companion(text,s.last_response,s.locale) if self.settings.model_provider!='mock' or any(word in command for word in ('树林','森林','forest')) else ''
            return self.respond(s,(conversation+'\n' if conversation else '')+label+look['name']+'。这是可选方向，最终由你决定。选择“开始步骤”来试做。'+('\n'+self.full_look.summary(s) if cafe else ''))
        if text and s.stage==Stage.GUIDE and step:
            return self.respond(s,self.language.guide(text,{**step,"previous_reply":s.last_response[-1200:],"story_context":'\n'.join(s.story_context)[-2000:]},s.locale))
        return self.respond(s,s.last_response or '你可以选择重复、慢一点、为什么、下一步、相机检查或停止。')
