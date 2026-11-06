import {Hardware,Mirror} from './pages/Hardware'
import {isVisualRequest} from './realtime/visualCommand'
import {SectionBackground} from './visual/SectionBackground'
import {MakeupDigitalTwin,AccessibilityControls,ParticleBackground} from './visual/BeautyVisuals'
import {BilingualLabel} from './visual/BilingualHeading'

import {Entry} from './pages/Entry'
import {VoiceAccessBar} from './components/VoiceAccessBar'
import {FullLook} from './pages/FullLook'
import {BilingualText} from './components/BilingualText'
import {humanError} from './content/errors'
import {useEffect,useRef,useState,type FormEvent} from 'react'
import {api} from './api/client'
import {
  expectedPlan, forgetPendingCommand, readCommittedCommand, readPendingCommand,
  rememberPendingCommand, replyFromSnapshot,
} from './api/sessionCommands'
import {ReadingControls} from './components/ReadingControls'
import {streamChat} from './api/stream'
import type {Health,Reply,Session as SessionModel,Step,VisionReply,ExperienceMode} from './types'
import {VoiceCall} from './pages/VoiceCall'
import {VideoCall} from './pages/VideoCall'
import {RealtimeCallController,type CallSnapshot} from './realtime/callController'
import {BrowserTTSProvider} from './realtime/voice'
import {LocalRecognitionProvider} from './realtime/localVoice'
import {routeVoice,normalizeVoice} from './realtime/voiceCommands'
import {returnGreeting,type RecollectionView} from './realtime/recollection'
import {LookRecollection} from './pages/LookRecollection'
import {Session} from './pages/Session'
import {CameraCheck} from './pages/CameraCheck'
import {BeautyMemory} from './pages/BeautyMemory'
import {DebugPanel} from './components/DebugPanel'
import {PushToTalkProvider} from './realtime/voice'
import {Reading} from './pages/Reading'
import {Pair} from './pages/Pair'
import {Story} from './pages/Story'
import {Demo} from './pages/Demo'


import {useArtMotion} from './accessibility/useArtMotion'
import {Journal,type JournalDraft} from './pages/Journal'
import {AppleMark} from './components/AppleMark'
import {TraceMark} from './components/TraceMark'
import {TraceDotGrid} from './components/TraceDotGrid'
import {useTrace,bilingual} from './content/Locale'
import {modules,type ModuleKey} from './content/traceBrand'
import {pageFromPath,pageUrl,initialPage,resolvePage,type Page} from './state/routes'
import {useSpeech} from './accessibility/useSpeech'

type Message={role:'user'|'agent';text:string}
export default function App(){
  const {locale,c,t,d}=useTrace()
  const [demoMode,setDemoMode]=useState(()=>window.location.pathname==='/demo'||new URLSearchParams(window.location.search).get('demo')==='true')
  const [page,setPage]=useState<Page>(()=>initialPage(window.location.pathname,window.location.search))
  const [session,setSession]=useState<SessionModel|null>(null)
  const [step,setStep]=useState<Step|null>(null)
  const [health,setHealth]=useState<Health|null>(null)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [text,setText]=useState('')
  const [messages,setMessages]=useState<Message[]>([])
  const [journalDraft,setJournalDraft]=useState<JournalDraft|null>(null)
  const [draftStatus,setDraftStatus]=useState('')
  const reviewedJournal=useRef<JournalDraft|null>(null)
  const [streamingText,setStreamingText]=useState('')
  const historyRef=useRef<HTMLDivElement>(null),followHistory=useRef(true)
  useEffect(()=>{const view=historyRef.current;if(view&&followHistory.current)view.scrollTop=view.scrollHeight},[messages,streamingText,page])
  const requestAbort=useRef<AbortController|null>(null)
  const [experienceMode,setExperienceMode]=useState<ExperienceMode>(()=>window.location.pathname==='/voice'?'voice':window.location.pathname==='/explore'?'visual':'text')
  const [debug,setDebug]=useState(false)
  const [artMotion,setArtMotion]=useState(true)
  const [audioReactive,setAudioReactive]=useState(false)
  const [previewRegion,setPreviewRegion]=useState('')
  useEffect(()=>setPreviewRegion(''),[step?.step_id])
  useArtMotion(page,artMotion&&page!=='story')
  const [autoSpeak,setAutoSpeak]=useState(false)
  const [listening,setListening]=useState(false)
  const [voiceConsent,setVoiceConsent]=useState(false)
  const voice=useRef(new PushToTalkProvider())
  const tts=useSpeech()
  const latest=useRef(0)
  const titleRef=useRef<HTMLDivElement>(null)
  const sessionRef=useRef<SessionModel|null>(null)
  sessionRef.current=session
  const pageRef=useRef(page);pageRef.current=page
  const cameraConsentGeneration=useRef(0)
  const cameraControls=useRef<{open:()=>Promise<void>;close:()=>void;allowLocal:()=>boolean}|null>(null)
  const [cameraPanel,setCameraPanel]=useState(false)
  const pendingCameraOpen=useRef(false)
  const localCheck=useRef<((target?:'blush'|'lips',signal?:AbortSignal)=>Promise<Reply>)|null>(null)
  const call=useRef<RealtimeCallController|null>(null)
  const recollection=useRef<RecollectionView|null>(null),recallOffered=useRef(false),reusePrevious=useRef(false),lastSpoken=useRef('')
  const [callSnapshot,setCallSnapshot]=useState<CallSnapshot>({state:'idle',transcript:'',reply:'',error:''})
  const callSend=useRef<(value:string,onDelta?:(part:string)=>void,signal?:AbortSignal)=>Promise<string>>(async()=> '')
  if(!call.current)call.current=new RealtimeCallController(new LocalRecognitionProvider(),new BrowserTTSProvider(),(value,onDelta,signal)=>callSend.current(value,onDelta,signal))
  callSend.current=(value,onDelta,signal)=>voiceTurn(value,onDelta,signal)
  if(call.current)call.current.onReady=()=>{localStorage.setItem('trace.voice-enabled','on');void greetVoice()}
  useEffect(()=>{++latest.current;requestAbort.current?.abort();setStreamingText('' );setBusy(false);voice.current.setLocale(locale);setListening(false);tts.stop();call.current?.setLocale(locale)},[locale])
  function observeCall(snapshot:CallSnapshot){if(snapshot.reply)lastSpoken.current=snapshot.reply;if(snapshot.state==='ended'){++latest.current;setBusy(false);revokeCamera()}setCallSnapshot(snapshot)}
  useEffect(()=>call.current!.subscribe(observeCall),[])
  useEffect(()=>{call.current?.setBounded(['voice','speak','explore'].includes(page))},[page])
  function stopCall(){localStorage.setItem('trace.voice-enabled','off');tts.stop();++latest.current;requestAbort.current?.abort();setStreamingText('');setBusy(false);call.current?.end();if(cameraControls.current)cameraControls.current.close();else revokeCamera()}
  function startCall(){manualInputRequested.current=false;if(call.current?.state==='ended'){call.current=new RealtimeCallController(new LocalRecognitionProvider(),new BrowserTTSProvider(),(value,onDelta,signal)=>callSend.current(value,onDelta,signal));call.current.subscribe(observeCall);call.current.setLocale(locale)}if(call.current)call.current.onReady=()=>{localStorage.setItem('trace.voice-enabled','on');void greetVoice()};call.current?.setBounded(['voice','speak','explore'].includes(page));call.current?.start()}
  const manualInputRequested=useRef(false)
  function beginVoicePhrase(){
    manualInputRequested.current=true
    if(call.current?.state==='ended'){call.current=new RealtimeCallController(new LocalRecognitionProvider(),new BrowserTTSProvider(),(value,onDelta,signal)=>callSend.current(value,onDelta,signal));call.current.subscribe(observeCall);call.current.setLocale(locale)}
    localStorage.setItem('trace.voice-enabled','on');call.current?.setBounded(true);call.current?.beginCapture()
  }
  function enterReflect(){
    if(busy||call.current?.state==='thinking'||call.current?.snapshot.recording)return
    if(['idle','ended','paused','error'].includes(call.current?.state??'idle')){setBusy(true);void voiceTurn('进入映照').catch(e=>setError(String(e))).finally(()=>setBusy(false))}
    else submitStoryText('进入映照')
  }
  function submitStoryText(value:string){if(call.current?.state==='ended'){call.current=new RealtimeCallController(new LocalRecognitionProvider(),new BrowserTTSProvider(),(text,onDelta,signal)=>callSend.current(text,onDelta,signal));call.current.subscribe(observeCall);call.current.setLocale(locale)}call.current?.submit(value)}
  function revokeCamera(){++cameraConsentGeneration.current;const sid=sessionRef.current?.session_id;if(sid)void api<Reply>('/chat',{session_id:sid,message:'',action:'camera_consent',consent:false}).then(r=>{if(sessionRef.current?.session_id===sid)setSession(current=>current?{...current,camera_consent:false}:current)}).catch(()=>{})}
  async function grantCamera(){const sid=sessionRef.current?.session_id;if(!sid)return false;const generation=latest.current;const cameraGeneration=cameraConsentGeneration.current;const requested=await api<Reply>('/chat',{session_id:sid,message:'check this'});if(cameraGeneration!==cameraConsentGeneration.current||generation!==latest.current||sessionRef.current?.session_id!==sid){void api('/chat',{session_id:sid,message:'',action:'camera_consent',consent:false});return false}apply(requested);const granted=await api<Reply>('/chat',{session_id:sid,message:'',action:'camera_consent',consent:true});if(cameraGeneration!==cameraConsentGeneration.current||generation!==latest.current||sessionRef.current?.session_id!==sid){void api('/chat',{session_id:sid,message:'',action:'camera_consent',consent:false});return false}apply(granted);return granted.session.camera_consent}
  useEffect(()=>{const release=()=>{++latest.current;requestAbort.current?.abort();call.current?.end();tts.stop();revokeCamera()};const hide=()=>{if(document.hidden)release()};window.addEventListener('pagehide',release);document.addEventListener('visibilitychange',hide);return()=>{window.removeEventListener('pagehide',release);document.removeEventListener('visibilitychange',hide);call.current?.end();revokeCamera()}},[])
  useEffect(()=>{api<Health>('/health').then(setHealth).catch(()=>setError(c.connectionError))},[])
  useEffect(()=>()=>{voice.current.abort()},[])
  useEffect(()=>{
    let active=true
    const generation=latest.current
    const id=sessionStorage.getItem('trace.session_id')
    if(id)api<SessionModel>('/session/'+encodeURIComponent(id)+'/restore',undefined,'POST').then(snapshot=>{
      if(!active||generation!==latest.current)return
      acceptSnapshot(snapshot,snapshot.current_step??null)
      if(snapshot.last_response)setMessages([{role:'agent',text:snapshot.last_response}])
      if(snapshot.experience_mode)setExperienceMode(snapshot.experience_mode)
      void recoverPendingCommand()
    }).catch(()=>{
      if(active&&generation===latest.current)setError(t('上次会话暂时无法恢复','Could not restore previous session'))
    })
    return ()=>{active=false}
  },[])
  useEffect(()=>{
    const online=()=>void recoverPendingCommand()
    window.addEventListener('online',online)
    return ()=>window.removeEventListener('online',online)
  },[locale])
  useEffect(()=>{if(session)sessionStorage.setItem('trace.session_id',session.session_id)},[session?.session_id])
  useEffect(()=>{const url=pageUrl(page,demoMode);if(window.location.pathname+window.location.search!==url)window.history.replaceState({},'',url)},[page,demoMode])
  useEffect(()=>{if(page==='home')document.querySelector<HTMLButtonElement>('[data-primary-voice]')?.focus();else titleRef.current?.focus();document.title='TRACE · '+(page==='voice'?t("语音陪伴","Voice Companion"):page==='explore'?t("视觉探索","Visual Experience"):page==='full-look'?t("今日造型","Today's Look"):page==='home'?c.home:page==='session'?bilingual(modules.thread.label['zh-CN'],modules.thread.label.en,locale):page==='camera'?bilingual(modules.echo.label['zh-CN'],modules.echo.label.en,locale):page==='memory'?bilingual(modules.imprint.label['zh-CN'],modules.imprint.label.en,locale):page==='dot'?bilingual(modules.dot.label['zh-CN'],modules.dot.label.en,locale):page==='pair'?bilingual(modules.pair.label['zh-CN'],modules.pair.label.en,locale):page==='story'?c.story:page==='demo'?c.demo:c.intro);document.documentElement.lang=locale},[page,locale])
  const welcomeText=t('欢迎来到TRACE。首次使用请完成麦克风设置，可借助Apple旁白与语音控制。语音就绪后说可以开始；说请终止对话安静等待，再说重新启动语音交流功能继续。','Welcome to TRACE. Complete microphone setup for first use. Say let’s begin when voice is ready. Say pause replies to wait quietly, and resume voice to continue.')
  useEffect(()=>{
    let active=true
    void api<RecollectionView>('/recollection').then(value=>{if(active)recollection.current=value}).catch(()=>{})
    if(localStorage.getItem('trace.voice-enabled')==='on'&&navigator.permissions?.query)void navigator.permissions.query({name:'microphone' as PermissionName}).then(permission=>{if(active&&permission.state==='granted')startCall()}).catch(()=>{})
    else if(pageRef.current==='home')tts.speak(welcomeText)
    return()=>{active=false}
  },[])
  async function greetVoice(){
    const current=call.current
    try{recollection.current=await api<RecollectionView>('/recollection')}catch{/* First visits can continue without a previous look. */}
    if(manualInputRequested.current||current!==call.current||!['listening','requesting_permission'].includes(current?.state??''))return
    let greeting=pageRef.current==='home'?returnGreeting(null,locale):pageRef.current==='voice'?t('现在是倾听。点击开始说话，告诉我场合和妆容需求，说完点击提交。聊好后，点击进入映照。','Step two, Listen. Tell me about today’s occasion and look. Say done to enter Reflect.'):t('语音陪伴已就绪。你可以说帮助，听取当前操作说明。','Voice is ready. Say help for the current controls.')
    if(!recallOffered.current){if(recollection.current?.enabled&&recollection.current.latest)greeting=returnGreeting(recollection.current,locale,pageRef.current==='home');recallOffered.current=true;greeting+=t('需要安静时，说请终止对话；说重新启动语音交流功能后继续。','Say pause replies to wait quietly, and resume voice to continue.')}
    if(['voice','speak','explore'].includes(pageRef.current))greeting+=t('也可以先说开始，表达需求后说结束。','You can also use the start and end keywords.')
    current?.announce(greeting)
  }
  async function voiceTurn(value:string,onDelta?:(part:string)=>void,signal?:AbortSignal):Promise<string>{
    const command=routeVoice(value,pageRef.current)
    const normalized=normalizeVoice(value)
    if(['沿用','继续上次','延续上次','和上次一样','keeppreviouslook','keeplastlook','sameaslasttime','keepthatfeeling'].includes(normalized)&&recollection.current?.enabled&&recollection.current.latest){reusePrevious.current=true;if(pageRef.current==='home'){setExperienceMode('voice');await navigate('voice',true,true);await ensureVisualSession()}return t('好，我们延续上次的妆容方向。你可以补充今天的场合，或说完成进入映照。','We will keep the previous look direction. Tell me today’s occasion, or say done to enter Reflect.')}
    if(['换一个','换个风格','重新开始','不要提上次','tryanewlook','trynewlook','newlook','trysomethingnew','startfresh'].includes(normalized)){reusePrevious.current=false;if(pageRef.current==='home'){setExperienceMode('voice');await navigate('voice',true,true);await ensureVisualSession()}return t('好，今天从新的需求开始。你想要怎样的感觉？','Let’s begin fresh. What feeling would you like today?')}
    if(command?.command==='begin'){
      if(sessionRef.current?.makeup_plan?.status==='completed'){sessionRef.current=null;setSession(null);setStep(null);sessionStorage.removeItem('trace.session_id');setMessages([]);recallOffered.current=false}
      setExperienceMode('voice');await navigate('voice',true,true);await ensureVisualSession()
      if(!recallOffered.current&&recollection.current?.enabled&&recollection.current.latest){recallOffered.current=true;return t('现在是第二步，倾听。','Step two, Listen. ')+returnGreeting(recollection.current,locale,false)+t('说完成进入映照。',' Say done to enter Reflect.')}
      return t('现在是第二步，倾听。请先说开始，再告诉我今天的场合和妆容需求，最后说结束。要进入映照，请说开始、完成、结束。','Step two, Listen. What is today’s occasion and desired look? Say done to enter Reflect.')
    }
    if(command?.command==='reflect'||(command?.command==='next'&&pageRef.current==='voice')){
      const sid=await ensureVisualSession()
      const reply=await api<Reply>('/experience/reflect',{session_id:sid,locale,reuse_previous:reusePrevious.current},undefined,signal)
      if(signal?.aborted)return ''
      apply(reply,false,true);setExperienceMode('voice');await navigate('explore',true,true);return reply.message
    }
    if(command?.command==='finish'){
      const current=sessionRef.current
      const requestId=++latest.current
      const eventId=crypto.randomUUID()
      const body={session_id:current?.session_id,locale,event_id:eventId,...expectedPlan(current?.makeup_plan)}
      if(current?.makeup_plan)rememberPendingCommand({sessionId:current.session_id,eventId})
      let reply:Reply
      try{
        reply=await api<Reply>('/recollection/finish',body,undefined,signal)
      }catch(error){
        if(!current||requestId!==latest.current||signal?.aborted)throw error
        const result=await readCommittedCommand(current.session_id,eventId,signal)
        if(!result)throw error
        reply=replyFromSnapshot(result.session,t('本次装扮体验已结束。','This look experience has ended.'))
      }
      forgetPendingCommand(eventId)
      if(requestId!==latest.current||signal?.aborted||sessionRef.current?.session_id!==current?.session_id)return ''
      apply(reply,false,true);return reply.message
    }
    if(command?.command==='help')return pageRef.current==='home'?t('说可以开始，进入倾听。需要安静说请终止对话，恢复说重新启动语音交流功能。','Say let’s begin to enter Listen. Say pause replies to wait quietly, and resume voice to continue.'):pageRef.current==='voice'?t('请先说开始，再告诉我场合和妆容需求，最后说结束。要进入映照，请说开始、完成、结束。','Tell me the occasion and look. Say done to enter Reflect, repeat, or use page navigation.'):t('请先说开始，再说下一步、上一步、再说一次、跳过或帮我看看，最后说结束。每次只提交起止词之间的内容。','Say next, previous, repeat, skip, or check my blush. Say finish this look to finish. Say pause replies to pause.')
    if(command?.command==='repeat')return sessionRef.current?.current_step?.instruction??step?.instruction??(lastSpoken.current||welcomeText)
    if(command?.command==='clearRecall'||command?.command==='disableRecall'||command?.command==='enableRecall'){
      recollection.current=command.command==='clearRecall'?await api<RecollectionView>('/recollection',undefined,'DELETE',signal):await api<RecollectionView>('/recollection/settings',{enabled:command.command==='enableRecall'},undefined,signal)
      reusePrevious.current=false;return command.command==='clearRecall'?t('妆容摘要已清除。今天仍可正常继续。','Look summaries cleared. You can continue today.'):command.command==='disableRecall'?t('以后不再主动提起上次妆容。今天我们照常继续。','I will stop bringing up previous looks. Let’s continue today.'):t('已开启下次妆容回忆。','Next-visit look recollection enabled.')
    }
    if(command?.page){await navigate(command.page,true,true);return ({home:t('已进入首页。说可以开始进入倾听。','Home. Say let’s begin to enter Listen.'),voice:t('已进入倾听。请先说开始，表达需求后说结束。要进入映照，请说开始、完成、结束。','Listen. Say done to enter Reflect.'),memory:t('已进入拾光。可以说关闭拾光回忆、清除拾光记忆，或回首页。','Memory. Say disable recollection, clear look memory, or go home.'),'full-look':t('已进入今天的你。你可以查看当前造型建议，或回到倾听。','Today’s Look. Explore your current look, or return to Listen.'),story:t('已进入故事。你可以说回首页。','Story. Say go home to return.')} as Record<string,string>)[command.page]}
    const message=command?.command==='next'?'下一步':command?.command==='previous'?'上一步':command?.command==='skip'?'跳过':value
    return send(message,'message',undefined,false,true,onDelta,signal)
  }
  useEffect(()=>{const pop=()=>void navigate(pageFromPath(window.location.pathname),false);window.addEventListener('popstate',pop);return ()=>window.removeEventListener('popstate',pop)},[page,demoMode])
  async function recoverPendingCommand(){
    const pending=readPendingCommand()
    const requestId=latest.current
    if(!pending||pending.sessionId!==sessionRef.current?.session_id)return
    try{
      const known=await readCommittedCommand(pending.sessionId,pending.eventId)
      if(!known||requestId!==latest.current||sessionRef.current?.session_id!==pending.sessionId)return
      const message=t('操作已提交。已同步当前进度。','Your command was applied. Current progress was restored.')
      setError('')
      apply(replyFromSnapshot(known.session,message),false,true)
      forgetPendingCommand(pending.eventId)
    }catch{/* Keep the event ID for the next reconnect. */}
  }
  function acceptSnapshot(incomingSession:SessionModel,incomingStep:Step|null){
    const previous=sessionRef.current?.makeup_plan
    const incoming=incomingSession.makeup_plan
    if(previous&&incoming&&previous.id===incoming.id&&incoming.revision<previous.revision)return false
    const closeMedia=incoming&&previous?.workflow!==incoming.workflow
      &&(incoming.workflow==='PAUSED'||incoming.status==='completed')
    sessionRef.current=incomingSession;setSession(incomingSession);setStep(incomingStep)
    if(closeMedia){cameraControls.current?.close();setCameraPanel(false)}
    return true
  }
  function apply(reply:Reply,slow=false,silent=false){
    reply=reply.canonical?{...reply,...reply.canonical}:reply
    if(!acceptSnapshot(reply.session,reply.step))return
    setMessages(m=>[...m,{role:'agent' as const,text:reply.message}].slice(-30))
    if(autoSpeak&&!silent)tts.speak(d(reply.message),slow)
    if(!['voice','explore','speak'].includes(pageRef.current)&&reply.session.stage==='CAMERA_CONSENT')setPage('camera')
    if(!['voice','explore','speak'].includes(pageRef.current)&&reply.session.stage==='MEMORY_CONSENT')setPage('memory')
    if(['GUIDE','LOOK_SELECTED'].includes(reply.session.stage))setPage(current=>current==='camera'?'session':current)
    if(reply.session.stage==='COMPLETE'){voice.current.abort();setListening(false)}
  }
  function applyLocal(reply:Reply){if(reply.session.session_id!==sessionRef.current?.session_id)return;apply(reply,false,true);if(call.current?.state==='quiet_wake')return;if(call.current?.state==='listening')call.current.announce(reply.message);else if(autoSpeak)tts.speak(d(reply.message))}
  async function send(message:string,action='message',consent?:boolean,newSession=false,silent=false,onDelta?:(part:string)=>void,signal?:AbortSignal){
    const sessionId=sessionRef.current?.session_id
    const requestId=++latest.current
    requestAbort.current?.abort();const abort=new AbortController();requestAbort.current=abort;setStreamingText('')
    setBusy(true);setError('')
    if(message)followHistory.current=true
    if(message)setMessages(m=>[...m,{role:'user' as const,text:message}].slice(-30))
    if(message==='stop'){tts.stop();voice.current.abort();setListening(false)}
    try{
      const command=message.trim().toLowerCase().replace(/[。.!！?？]+$/,'')
      if(['开启摄像头','open camera','关闭摄像头','close camera','同意本地检查','allow local checks'].includes(command)){
        let reply=''
        if(command==='开启摄像头'||command==='open camera'){
          if(cameraControls.current)await cameraControls.current.open()
          else {pendingCameraOpen.current=true;if(['voice','speak'].includes(pageRef.current))setCameraPanel(true);else{setExperienceMode('visual');setPage('explore');window.history.pushState({},'',pageUrl('explore',demoMode))}}
          reply=t('已请求本地摄像头预览。若浏览器询问权限，请自行确认；还没有分析或外发画面。','Local camera preview requested. Confirm browser permission if prompted; no frame has been analyzed or sent remotely.')
        }else if(command==='关闭摄像头'||command==='close camera'){
          pendingCameraOpen.current=false;cameraControls.current?.close();setCameraPanel(false);reply=t('已关闭摄像头，本地检查已停止。','Camera closed; local checks stopped.')
        }else{
          const allowed=cameraControls.current?.allowLocal();reply=allowed?t('已同意本应用的本地单帧检查。说“帮我看看”会获取新画面；不会调用远程视觉服务。','Local single-frame checks allowed. Say check my blush for a fresh frame; no remote vision service is used.'):t('摄像头尚未就绪。先说“开启摄像头”，待预览就绪后再同意本地检查。','Camera is not ready. Say open camera, wait for preview, then allow local checks.')
        }
        setMessages(rows=>[...rows,{role:'agent' as const,text:reply}].slice(-30));return reply
      }
      if(['读日志草稿','朗读日志草稿','read journal draft'].includes(command)){
        if(!journalDraft)throw new Error(t('日志草稿还未就绪，请稍后再试。','Journal draft is not ready. Try again shortly.'))
        const draft={...journalDraft,look:journalDraft.look.trim()||t('今日片刻','Today’s moment')};reviewedJournal.current=draft
        const preview=[draft.look,draft.feeling,draft.reflection,draft.traits].filter(Boolean).join('。 ')
        const reply=t('这是待确认的私人日志草稿：','This is your private journal draft: ')+preview+t('。若内容准确，可以说“确认保存这份私人日志”。聊天原文不会一并保存。',' If accurate, say “confirm save private journal”. The full transcript will not be saved.')
        setMessages(rows=>[...rows,{role:'agent' as const,text:reply}].slice(-30));return reply
      }
      if(['确认保存这份私人日志','confirm save private journal'].includes(command)){
        const draft=reviewedJournal.current;if(!draft)throw new Error(t('请先说“读日志草稿”，审阅后再确认保存。','Say “read journal draft” and review it before confirming.'))
        const now=new Date(),date=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`
        await api('/journal',{...draft,date,session_id:sessionRef.current?.session_id,explicit_consent:true,save_transcript:false},undefined,abort.signal)
        reviewedJournal.current=null
        const reply=t('你确认的私人日志已保存，可以在拾光日历中查看。没有保存录音、照片或聊天原文。','Your confirmed private journal was saved to your calendar. Audio, photos and full chat were not saved.')
        setMessages(rows=>[...rows,{role:'agent' as const,text:reply}].slice(-30));return reply
      }
      let recoveredSession=false
      const plan=sessionRef.current?.makeup_plan
      const requestBody={session_id:newSession?undefined:sessionRef.current?.session_id,user_id:'demo',message,action,consent,locale,experience_mode:experienceMode,event_id:crypto.randomUUID(),...expectedPlan(newSession?null:plan)}
      const delta=(part:string)=>{if(requestId===latest.current){setStreamingText(value=>value+part);onDelta?.(part)}}
      const received=(incoming:SessionModel)=>{if(requestId===latest.current&&(!sessionRef.current||sessionRef.current.session_id===incoming.session_id))acceptSnapshot(incoming,incoming.current_step??null)}
      const requestSignal=signal?AbortSignal.any([signal,abort.signal]):abort.signal
      async function requestText(){
        if(plan&&requestBody.session_id&&action==='message'){
          rememberPendingCommand({sessionId:requestBody.session_id,eventId:requestBody.event_id})
        }
        try{
          const reply=await streamChat(requestBody,delta,requestSignal,received)
          forgetPendingCommand(requestBody.event_id)
          return reply
        }catch(failure){
          if(plan&&requestBody.session_id&&action==='message'&&requestId===latest.current&&!requestSignal.aborted){
            const known=await readCommittedCommand(requestBody.session_id,requestBody.event_id,requestSignal).catch(()=>null)
            if(known){
              forgetPendingCommand(requestBody.event_id)
              const fallback=t('操作已提交。已同步当前进度。','Your command was applied. Current progress was restored.')
              const instruction=known.session.current_step?.instruction
              return replyFromSnapshot(known.session,instruction?fallback+' '+instruction:fallback)
            }
            if((failure as {code?:string}).code==='STALE_PLAN'){
              forgetPendingCommand(requestBody.event_id)
              const snapshot=await api<SessionModel>('/session/'+encodeURIComponent(requestBody.session_id),undefined,'GET',requestSignal)
              received(snapshot)
            }
            throw failure
          }
          // HTTP 404 happens before any SSE delta/tool. Retry only ordinary text,
          // never consent/local frames or a partially generated stream.
          if((failure as {status?:number}).status!==404||!requestBody.session_id||action!=='message'||consent!==undefined||requestId!==latest.current||requestSignal.aborted)throw failure
          recoveredSession=true;sessionRef.current=null;setSession(null);setStep(null);sessionStorage.removeItem('trace.session_id')
          reviewedJournal.current=null;setJournalDraft(null);setDraftStatus('');setMessages(message?[{role:'user',text:message}]:[])
          return streamChat({...requestBody,session_id:undefined},delta,requestSignal,received)
        }
      }
      const visualRequested=isVisualRequest(message)
      if(visualRequested&&!localCheck.current&&['voice','speak'].includes(pageRef.current))setCameraPanel(true)
      const result=visualRequested&&localCheck.current ? await localCheck.current(/唇|lips/i.test(message)?'lips':undefined,requestSignal) : await requestText()
      if(requestId===latest.current&&(sessionRef.current?.session_id===sessionId||sessionRef.current?.session_id===result.session.session_id||(recoveredSession&&!sessionRef.current))){apply(result,message==='slow down',silent);return result.message}
      return ''
    }catch(e){if(requestId===latest.current)setError(e instanceof Error?e.message:'请求失败');if(silent)throw e;return ''}
    finally{if(requestId===latest.current){setBusy(false);setStreamingText('')}}
  }
  const visualSessionRequest=useRef<Promise<string>|null>(null)
  async function ensureVisualSession():Promise<string>{
    if(sessionRef.current?.session_id)return sessionRef.current.session_id
    if(visualSessionRequest.current)return visualSessionRequest.current
    const version=latest.current
    const pending=api<SessionModel>('/session',{locale,experience_mode:'visual'}).then(incoming=>{
      if(version!==latest.current||!incoming.session_id)throw new Error(t('检查会话未准备好，请重试。','Analysis session is not ready. Retry.'))
      sessionRef.current=incoming;setSession(incoming);setStep(incoming.current_step??null);setError('');return incoming.session_id
    })
    visualSessionRequest.current=pending
    try{return await pending}finally{if(visualSessionRequest.current===pending)visualSessionRequest.current=null}
  }
  async function start(scenario=''){
    call.current?.pause();const previous=sessionRef.current;++latest.current;sessionRef.current=null
    tts.stop();voice.current.abort();setListening(false);setBusy(true);setError('');setPage(experienceMode==='voice'?'voice':'session')
    if(previous&&previous.stage!=='COMPLETE'){
      try{await api<Reply>('/chat',{session_id:previous.session_id,message:'stop'})}
      catch(e){if((e as {status?:number}).status!==404){setBusy(false);setError(c.oldSessionError);return}}
    }
    setMessages([]);setJournalDraft(null);setDraftStatus('');reviewedJournal.current=null
    window.history.pushState({},'',pageUrl(experienceMode==='voice'?'voice':'session',demoMode))
    await send(scenario,'message',undefined,true)
  }
  async function navigate(next:Page,push=true,preserveCall=false){
    const keepCall=preserveCall||!!call.current&&['requesting_permission','listening','thinking','speaking','quiet_wake'].includes(call.current.state)
    if(!keepCall)stopCall()
    voice.current.abort();setListening(false);if(!keepCall)tts.stop()
    if(page==='camera'&&sessionRef.current?.camera_consent)await send('stop camera')
    const keepDemo=demoMode||next==='demo';setDemoMode(keepDemo);pageRef.current=next;setPage(next);setCameraPanel(false);setError('');if(push)window.history.pushState({},'',pageUrl(next,keepDemo))
  }
  async function check(images:string[],demo:boolean,status:string,task:string){
    if(!sessionRef.current)return
    const id=++latest.current
    setBusy(true);setError('')
    try{const result=await api<VisionReply>('/vision/check',{session_id:sessionRef.current.session_id,images,demo,mock_status:status,task});if(id===latest.current)apply(result)}
    catch(e){
      if(id===latest.current){setError(e instanceof Error?e.message:'检查失败');try{const s=await api<SessionModel>('/session/'+sessionRef.current.session_id);setSession(s)}catch{/* Keep the original actionable error when backend is unavailable. */}}
    }finally{if(id===latest.current)setBusy(false)}
  }
  function talk(){if(['listening','thinking','speaking','quiet_wake'].includes(call.current?.state??''))call.current?.pause();else startCall()}
  function submit(event:FormEvent){event.preventDefault();const value=text.trim();if(!value)return;call.current?.pause();++latest.current;setText('');void voiceTurn(value).catch(e=>setError(String(e)))}
  useEffect(()=>{
    if(!messages.some(m=>m.role==='user')||messages.at(-1)?.role!=='agent')return
    let active=true
    const timer=setTimeout(()=>{
      const bounded:Message[]=[];let length=0
      for(const m of [...messages].reverse()){const text=m.text.slice(0,2000);if(length+text.length>12000)break;bounded.unshift({...m,text});length+=text.length}
      setDraftStatus(t('正在整理本次对话草稿。','Preparing this conversation draft.'))
      api<JournalDraft>('/journal/draft',{messages:bounded,locale}).then(draft=>{if(active){setJournalDraft(draft);setDraftStatus(t('本次对话草稿已就绪，尚未保存。','Conversation draft ready, not saved.'))}}).catch(()=>{if(active){setJournalDraft({look:t('今日片刻','Today’s moment'),feeling:'',reflection:bounded.filter(m=>m.role==='user').map(m=>m.text).join('\n').slice(0,2000),traits:''});setDraftStatus(t('摘要暂时不可用，已保留你的话作为待编辑草稿。','Summary unavailable. Your words are available as an editable draft.'))}})
    },1500)
    return()=>{active=false;clearTimeout(timer)}
  },[messages,locale])
  const last=messages.filter(m=>m.role==='agent').at(-1)?.text??''
  const openModule=(key:string)=>{const target=resolvePage(key);if(target==='session'&&!session)void start();else if(target==='camera'&&session&&['LOOK_SELECTED','GUIDE','VERIFY'].includes(session.stage))void send('check this');else void navigate(target)}
  async function chooseMode(mode:ExperienceMode){
    if(busy)return
    if(mode==='visual'&&(pageRef.current==='home'||['voice','speak'].includes(pageRef.current)&&(!sessionRef.current||sessionRef.current.stage==='INTENT'))){
      if(pageRef.current==='home')startCall()
      enterReflect();return
    }
    if(page==='home'&&mode!=='text')startCall()
    setExperienceMode(mode)
    await navigate(mode==='voice'?'voice':mode==='visual'?'explore':'session',true,mode!=='text')
    const current=sessionRef.current
    if(current){const id=++latest.current;setBusy(true);try{const r=await api<Reply>('/chat',{session_id:current.session_id,message:'',experience_mode:mode});if(id===latest.current&&sessionRef.current?.session_id===r.session.session_id){setSession(r.canonical?.session??r.session);setStep(r.canonical?.step??r.step)}}catch(e){if(id===latest.current)setError(e instanceof Error?e.message:c.requestError)}finally{if(id===latest.current)setBusy(false)}}
  }
  function applyPlan(reply:Reply){if(sessionRef.current?.session_id!==reply.session.session_id)return;const currentVersion=sessionRef.current?.todays_look?.version??0;const incoming=reply.session.todays_look?.version??0;if(incoming>=currentVersion)apply(reply)}
  const showConversation=['session','speak','voice','explore','full-look','camera','memory'].includes(page)
  const conversation=showConversation?<section className="conversation" aria-label={c.conversation}><div className="controls mode-switch" aria-label={t("切换体验方式","Switch experience")}><button aria-pressed={experienceMode==='voice'} disabled={busy} onClick={()=>chooseMode('voice')}>{t("语音陪伴","Voice")}</button><button aria-pressed={experienceMode==='visual'} disabled={busy} onClick={()=>chooseMode('visual')}>{t("视觉探索","Visual")}</button><button aria-pressed={experienceMode==='text'} disabled={busy} onClick={()=>chooseMode('text')}>{t("文字","Text")}</button><button disabled={busy} onClick={()=>void navigate('full-look')}>{t("今日造型","Today's Look")}</button></div><div className="conversation-top"><h2><BilingualText text={c.conversation}/></h2><button disabled={busy} onClick={()=>void start()}><BilingualText text={c.newSession}/></button></div>{streamingText?<p className="agent streaming-reply" aria-label={t("正在回复","Reply in progress")}>{streamingText}</p>:null}<div ref={historyRef} onScroll={e=>{const view=e.currentTarget;followHistory.current=view.scrollHeight-view.scrollTop-view.clientHeight<48}} className="messages" aria-label={c.history}>{!messages.length?<p className="conversation-invitation">{t("从今天的故事开始。说说你的场合、感受，或想要怎样的自己。","Begin with your day. Tell me about the occasion, how you feel, or how you want to feel.")}</p>:null}{messages.map((m,i)=><p key={i} className={m.role}><span className="speaker">{m.role==='user'?c.you:c.agent}</span>{m.role==='agent'?d(m.text):m.text}</p>)}</div><p role="status" aria-live={callSnapshot.state==='quiet_wake'?'off':'polite'} aria-atomic="true" className="sr-only">{busy?c.working:d(last)}</p><form onSubmit={submit}><label htmlFor="message"><BilingualText text={c.input}/></label><div className="input-row"><input id="message" value={text} onChange={e=>setText(e.target.value)} maxLength={2000} placeholder={c.dinner} disabled={false}/><button className="primary" disabled={!text.trim()}>{busy?c.working:c.send}</button></div></form>{!['voice','explore','speak'].includes(page)?<div className="voice-controls"><button disabled={busy||session?.stage==='COMPLETE'||!call.current?.available} onClick={talk}>{listening?c.listening:c.talk}</button>{listening||busy?<TraceDotGrid animationMode={listening?'listening':'processing'} activeDots={[1,3,5]}/>:null}<button disabled={!last} onClick={()=>tts.speak(d(last))}><BilingualText text={c.readReply}/></button><button onClick={()=>tts.state==='paused'?tts.resume():tts.pause()} disabled={tts.state!=='speaking'&&tts.state!=='paused'}>{tts.state==='paused'?t("继续朗读","Resume"):t("暂停朗读","Pause")}</button><button onClick={()=>tts.stop()}><BilingualText text={c.stopRead}/></button><label><input type="checkbox" checked={autoSpeak} onChange={e=>setAutoSpeak(e.target.checked)}/> {c.autoRead}</label></div>:null}{voiceConsent?<details className="notice" open><summary><BilingualText text={c.voiceInfo}/></summary><p><BilingualText text={c.voicePrivacy}/></p><button onClick={()=>{voice.current.abort();setListening(false);setVoiceConsent(false)}}><BilingualText text={c.revokeVoice}/></button></details>:null}</section>:null
  const callProps={navigationBusy:busy,beginCapture:beginVoicePhrase,finishCapture:()=>call.current?.finishCapture(),conversation,motion:artMotion,audioReactive,onAudioError:()=>setAudioReactive(false),openLook:()=>void navigate('full-look'),openMemory:()=>void navigate('memory'),snapshot:callSnapshot,session,step,start:startCall,pause:()=>{++latest.current;requestAbort.current?.abort();setStreamingText('' );setBusy(false);call.current?.pause()},resume:()=>call.current?.resume(),end:stopCall,interrupt:()=>{++latest.current;requestAbort.current?.abort();setStreamingText('' );setBusy(false);call.current?.interrupt()},send:submitStoryText,memoryConsent:(yes:boolean)=>{void send('','memory_consent',yes,false,true).catch(()=>{})}}
  return <div className={"trace-app trace-sculpture"+(page==='story'?" story-page":"")} data-art-motion={artMotion?'on':'off'}><a className="skip-link" href="#main-content"><BilingualText text={c.skip}/></a><header className="trace-header"><a className="brand" href="/" aria-label="TRACE" onClick={e=>{e.preventDefault();void navigate('home')}}><TraceMark/></a><span className="release-label">{t('交付版 · 2026.10.20','Release · 2026.10.20')}</span><nav aria-label={c.nav}>{([['home',c.home],['voice',t('倾听 · 美学对话','Listen · Beauty Conversation')],['explore',t('映照 · 实时妆教','Reflect · Makeup Guidance')],['memory',t('拾光 · 美的记忆','Trace · Beauty Memory')],['full-look',t('今天的你','Full Look')],['story',t('故事','Story')]] as const).map(([key,label],index)=><span className="step-nav-item" key={key}><button aria-label={(index+1)+' '+label} title={label} aria-current={page===key?'page':undefined} onClick={()=>key==='voice'?void chooseMode('voice'):key==='explore'?(['voice','speak'].includes(pageRef.current)&&!sessionRef.current?.makeup_plan?enterReflect():void chooseMode('visual')):void navigate(key)}><span className="nav-number" aria-hidden="true">{index+1}</span><BilingualLabel zh={key==='home'?'首页':key==='voice'?'倾听':key==='explore'?'映照':key==='full-look'?'今天的你':key==='story'?'故事':'拾光'} en={key==='home'?'Home':key==='voice'?'Listen · Beauty Conversation':key==='explore'?'Reflect · Makeup Guidance':key==='full-look'?'Full Look':key==='story'?'Story':'Trace · Beauty Memory'}/></button>{index<5?<span className="nav-arrow" aria-hidden="true">→</span>:null}</span>)}</nav><button className="motion-toggle" aria-pressed={artMotion} onClick={()=>setArtMotion(v=>!v)}>{artMotion?t("暂停动态","Pause motion"):t("开启动效","Enable motion")}</button><ReadingControls/><AccessibilityControls/></header><VoiceAccessBar snapshot={callSnapshot} start={startCall} pause={()=>{++latest.current;requestAbort.current?.abort();setBusy(false);call.current?.pause()}} resume={()=>call.current?.resume()} end={stopCall}/><div className={'layout'+(debug&&!demoMode?' with-debug':'')}><main id="main-content" aria-busy={busy}><section className={'visual-page visual-page-'+page}>{!['home','story','voice','speak','explore','full-look','devices','mirror'].includes(page)?<>{page==='explore'||page==='camera'?<MakeupDigitalTwin regionOverride={previewRegion} audioReactive={audioReactive} onAudioError={()=>setAudioReactive(false)} step={step} session={session} enabled={artMotion} state={callSnapshot.state}/>:<SectionBackground audioReactive={audioReactive&&['voice','speak'].includes(page)} onAudioError={()=>{setAudioReactive(false);setError(t('声音粒子暂不可用，可以继续对话。','Audio particles unavailable. Conversation can continue.'))}} view={page==='dot'?'left':page==='pair'?'right':page==='session'?'down':page==='memory'?'up':undefined} variant={page==='full-look'?'full-look':page==='voice'||page==='speak'?'voice':page==='memory'?'memory':'sculpture'} enabled={artMotion} state={callSnapshot.state} settled={session?.stage==='COMPLETE'}/>}<ParticleBackground/></>:null}<div ref={titleRef} tabIndex={-1} className="page-focus" aria-label={c.switched}/>{page==='devices'?<Hardware session={session}/>:null}{page==='mirror'?<Mirror/>:null}{page==='home'?<><Entry openStory={()=>void navigate('story')} openLook={()=>void navigate('full-look')} openMemory={()=>void navigate('memory')} motion={artMotion} choose={chooseMode} busy={busy} welcome={()=>tts.speak(welcomeText)}/>{health?.provider_mode==='mock'?<p className="notice">{t("当前为本地演示：辅导文字为预设内容，尚未连接真实对话模型。","Local demo: guidance is preset text. A live conversation model is not connected.")}</p>:health?<p className="notice">{t("文字辅导服务已连接。摄像头预览不代表 AI 已观察你的脸。","Text guidance is connected. Camera preview does not mean AI has observed your face.")}</p>:null}</>:null}{['voice','speak','explore'].includes(page)?<p role="status" className="notice">{callSnapshot.progress||t('点击“开始说话”录入需求，说完点击提交；也可使用“开始—结束”的语音方式。','Click to speak, then submit when finished. You can also use the start and end keywords.')}</p>:null}{page==='explore'?<VideoCall ensureSession={ensureVisualSession} region={previewRegion} previewRegion={setPreviewRegion} {...callProps} registerLocalCheck={fn=>{localCheck.current=fn}} registerCameraControls={controls=>{cameraControls.current=controls;if(controls&&pendingCameraOpen.current){pendingCameraOpen.current=false;void controls.open().catch(e=>setError(String(e)))}}} health={health} grant={grantCamera} revoke={revokeCamera} apply={applyLocal}/>:null}{page==='full-look'?<FullLook motion={artMotion} openConversation={()=>void chooseMode('voice')} openMemory={()=>void navigate('memory')} session={session} busy={busy} apply={applyPlan} startCafe={()=>void chooseMode('text')} onError={setError}/>:null}{page==='demo'?<Demo start={()=>void start(c.dinner)} busy={busy}/>:null}{page==='story'?<Story start={()=>void start()} navigate={openModule} motion={artMotion} snapshot={callSnapshot} startVoice={startCall} pauseVoice={callProps.pause} endVoice={stopCall} submitVoice={submitStoryText} audioReactive={audioReactive} setAudioReactive={setAudioReactive}/>:null}{page==='session'?<Session session={session} step={step} busy={busy} send={value=>void send(value)} compare={()=>void navigate('pair')}/>:null}{page==='speak'||page==='voice'?<><VoiceCall {...callProps} openReflect={enterReflect} openCamera={()=>void send('open camera')}/>{cameraPanel?<VideoCall ensureSession={ensureVisualSession} cameraOnly {...callProps} region={previewRegion} previewRegion={setPreviewRegion} registerLocalCheck={fn=>{localCheck.current=fn}} registerCameraControls={controls=>{cameraControls.current=controls;if(controls&&pendingCameraOpen.current){pendingCameraOpen.current=false;void controls.open().catch(e=>setError(String(e)))}}} health={health} grant={grantCamera} revoke={revokeCamera} apply={applyLocal}/>:null}</>:null}{['voice','speak','explore'].includes(page)?<div className="audio-wave-control"><button aria-pressed={audioReactive} onClick={()=>setAudioReactive(v=>!v)}>{audioReactive?t("关闭本地声音粒子","Disable local audio particles"):t("启用本地声音粒子","Enable local audio particles")}</button><p>{t("开启后在聆听时本地读取麦克风音量，不录制、不上传。AI 朗读使用状态脉动，不是真实音量。","When enabled, microphone levels are measured locally while listening, without recording or upload. AI playback uses a state pulse, not measured volume.")}</p></div>:null}{['voice','speak','explore'].includes(page)?<details className="call-utilities"><summary>{t('通话辅助：读标签、比较产品、我的记录','Call tools: labels, products and my records')}</summary><button onClick={()=>void navigate('dot')}>{t('读标签','Read label')}</button><button onClick={()=>void navigate('pair')}>{t('比较产品','Compare products')}</button><button onClick={()=>void navigate('memory')}>{t('记录感受','Record feelings')}</button><p>{t('尚未提供已核验的商品购买链接。','Verified product purchase links are not available yet.')}</p></details>:null}{page==='dot'?<Reading health={health} onError={setError}/>:null}{page==='pair'?<Pair session={session} start={()=>void start()} onError={setError}/>:null}{page==='camera'?<CameraCheck session={session} step={step} health={health} busy={busy} consent={async yes=>{await send('','camera_consent',yes)}} check={check} stop={()=>void send('stop camera')} send={value=>void send(value)} onError={setError} developerTools={debug&&!demoMode}/>:null}{page==='memory'?<><LookRecollection onChange={view=>{recollection.current=view}} onError={setError}/><details><summary>{t('私人日志与已有偏好 · 自行编辑','Private journal and existing preferences · Optional')}</summary><p role="status">{draftStatus}</p><Journal seed={last} draft={journalDraft} sessionId={session?.session_id}/><BeautyMemory session={session} busy={busy} consent={async yes=>{await send('','memory_consent',yes)}} onError={setError}/></details></>:null}{!['voice','speak','explore'].includes(page)?conversation:null}{error?<p role="alert" className="error"><BilingualText text={bilingual(humanError(error,'zh-CN'),humanError(error,'en'),locale)}/></p>:null}</section></main>{debug&&!demoMode?<DebugPanel session={session} health={health} error={error}/>:null}</div><footer className="trace-footer"><AppleMark/><a href="/visuals/CHARACTER-SOURCE.txt" target="_blank" rel="noreferrer">{t("人物临时预览 · 高清待替换","Character preview · awaiting HD asset")}</a><a href="/devices" onClick={e=>{e.preventDefault();void navigate('devices')}}>{t('设备连接','Devices')}</a><p><BilingualText text={c.footer}/></p><a href="/story" onClick={e=>{e.preventDefault();void navigate('story')}}><BilingualText text={c.story}/></a><a href="/demo" onClick={e=>{e.preventDefault();void navigate('demo')}}><BilingualText text={c.demo}/></a>{health?.developer_mode&&new URLSearchParams(window.location.search).get('developer')==='true'&&!demoMode?<details className="developer-tools"><summary><BilingualText text={c.dev}/></summary><button aria-pressed={debug} onClick={()=>setDebug(!debug)}>{debug?c.hideDev:c.showDev}</button><a href="/admin/knowledge"><BilingualText text={c.kb}/></a></details>:null}</footer></div>
}
