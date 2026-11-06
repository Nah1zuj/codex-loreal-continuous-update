import {it,expect,vi,afterEach} from 'vitest'
import {RealtimeCallController} from './callController'
import {BrowserTTSProvider,type RecognitionHandlers} from './voice'
import {routeVoice,wakeInput} from './voiceCommands'
import {returnGreeting} from './recollection'
class LocalInput{
 readonly local=true;readonly available=true;handlers:RecognitionHandlers|null=null;mode='active';stop=vi.fn();abort=vi.fn(()=>{this.handlers=null})
 setLocale(){}setMode(mode:string){this.mode=mode}startCycle(handlers:RecognitionHandlers){this.handlers=handlers;handlers.onReady?.()}
 text(value:string){this.handlers?.onText(value)}
}
function setup(send=vi.fn(async(text:string)=>'reply '+text)){
 const utterances:any[]=[]
 vi.stubGlobal('window',{speechSynthesis:{cancel:vi.fn(),speak:(u:any)=>utterances.push(u)}})
 vi.stubGlobal('SpeechSynthesisUtterance',class{constructor(public text:string){}})
 const input=new LocalInput(),call=new RealtimeCallController(input,new BrowserTTSProvider(),send)
 return {input,call,send,utterances}
}
afterEach(()=>vi.unstubAllGlobals())
it('quiet mode ignores all ordinary speech, then dispatches only the wake tail once',async()=>{
 const {input,call,send}=setup();call.start();input.text('请终止对话')
 expect(call.state).toBe('quiet_wake');expect(input.mode).toBe('quiet');expect(input.stop).not.toHaveBeenCalled()
 input.text('下一步');input.text('今天要去聚会');input.text('不要重新开启语音功能');expect(send).not.toHaveBeenCalled()
 input.text('重新启动语音交流功能，进入映照。');await Promise.resolve()
 expect(send).toHaveBeenCalledTimes(1);expect(send.mock.calls[0][0]).toBe('进入映照。')
})
it('speech can pause output; a late model or TTS callback cannot resume it',async()=>{
 let finish!:(text:string)=>void;const {input,call,utterances}=setup(vi.fn(()=>new Promise<string>(resolve=>{finish=resolve})))
 call.start();input.text('今天想要淡妆');input.text('暂停回应');finish('late');await Promise.resolve();await Promise.resolve()
 expect(call.state).toBe('quiet_wake');expect(utterances).toHaveLength(0)
 input.text('重新开启语音功能');const late=utterances.at(-1).onend;call.pause();late();expect(call.state).toBe('quiet_wake')
})
it('spoken microphone-close phrases never release the device; button end does',()=>{
 const {input,call}=setup();call.start();input.text('关闭麦克风');expect(input.stop).not.toHaveBeenCalled();call.end();expect(input.stop).toHaveBeenCalledTimes(1);expect(call.state).toBe('ended')
})
it('a reentrant pause during thinking cannot restore ordinary input or send a request',()=>{
 const {input,call,send}=setup();call.start();call.subscribe(snapshot=>{if(snapshot.state==='thinking')call.pause()});input.text('hello')
 expect(call.state).toBe('quiet_wake');expect(input.mode).toBe('quiet');expect(send).not.toHaveBeenCalled()
})
it('uses stage context and observed ASR homophones for deterministic navigation',()=>{
 expect(routeVoice('完成','voice')).toEqual({command:'reflect'})
 expect(routeVoice('完成','explore')).toEqual({command:'next'})
 expect(routeVoice('进入应照','home')).toEqual({command:'reflect'})
 expect(routeVoice('2','voice')).toBeNull();expect(wakeInput('不要重新开启语音功能')).toBeNull()
})
it('return greetings distinguish discussed looks from confirmed completed steps',()=>{
 const item={session_id:'old',name:'自然日常',date:'2026-10-17',occasion:'daily',style:'natural',completed_steps:[],all_steps_completed:false}
 const view={enabled:true,latest:item,entries:[item],retention_days:30}
 expect(returnGreeting(view,'zh-CN')).toContain('聊到了');expect(returnGreeting({...view,latest:{...item,completed_steps:['底妆']}},'zh-CN')).toContain('一起尝试了')
 expect(returnGreeting({...view,enabled:false},'zh-CN')).not.toContain('上次')
})

it('never claims wake listening while the browser is still withholding the microphone',()=>{
 const {input,call}=setup();input.startCycle=(handlers:RecognitionHandlers)=>{input.handlers=handlers}
 call.start();expect(call.state).toBe('requesting_permission');const late=input.handlers?.onReady
 call.pause();expect(call.state).toBe('paused');expect(input.stop).toHaveBeenCalledTimes(1)
 late?.();expect(call.state).toBe('paused')
})

it('bounded mode is used only on listening and suppresses response audio echo',async()=>{
 const {input,call,send,utterances}=setup();call.setBounded(true);call.start();expect(input.mode).toBe('bounded')
 input.handlers?.onProgress?.('正在收集本段内容，说结束后提交。');expect(call.snapshot.progress).toContain('收集')
 input.text('我想要自然的腮红');await Promise.resolve();await Promise.resolve()
 expect(send).toHaveBeenCalledTimes(1);expect(input.mode).toBe('quiet')
 input.text('重新开启语音功能，下一步');expect(send).toHaveBeenCalledTimes(1)
 utterances.at(-1).onend();expect(input.mode).toBe('bounded');call.end();expect(input.stop).toHaveBeenCalled()
})
it('entering a bounded page during an in-flight reply preserves that reply',async()=>{
 let finish!:(text:string)=>void;const {input,call,utterances}=setup(vi.fn(()=>new Promise<string>(resolve=>{finish=resolve})))
 call.start();input.text('可以开始');call.setBounded(true);finish('请先说开始，最后说结束。');await Promise.resolve();await Promise.resolve()
 expect(utterances.at(-1).text).toContain('最后说结束');utterances.at(-1).onend();expect(input.mode).toBe('bounded')
})
it('resuming a bounded page discards unframed wake tails',()=>{
 const {input,call,send}=setup();call.setBounded(true);call.start();call.pause();input.text('重新开启语音功能，我想要浓妆')
 expect(send).not.toHaveBeenCalled()
})

it('announces a speech service failure without blaming microphone permission',()=>{
 const {input,call,utterances}=setup();call.start()
 input.handlers?.onError('本地语音服务未确认就绪。请重新开启语音引导。')
 expect(call.state).toBe('error');expect(utterances.at(-1).text).toContain('本地语音服务连接失败')
 expect(utterances.at(-1).text).not.toContain('麦克风暂时未能连接')
})

it('accepts common explicit Listen completion phrases without treating unfinished input as completion',()=>{
 for(const text of ['好了','我说完了','进入映照环节','可以进入映照了','开始化妆','进入硬照完完成'])expect(routeVoice(text,'voice')).toEqual({command:'reflect'})
 expect(routeVoice('我还没有完成','voice')).toBeNull()
 expect(routeVoice('好了','explore')).toBeNull()
})

it('click recording starts without a spoken delimiter, then finishes explicitly',()=>{
 const {input,call,send}=setup();const begin=vi.fn(()=>input.handlers?.onCapture?.(true)),finish=vi.fn()
 ;(input as any).beginCapture=begin;(input as any).finishCapture=finish
 const greeting=vi.fn();call.onReady=greeting;call.setBounded(true);call.beginCapture()
 expect(begin).toHaveBeenCalledTimes(1);expect(greeting).not.toHaveBeenCalled();expect(call.snapshot.recording).toBe(true);expect(send).not.toHaveBeenCalled()
 call.finishCapture();expect(finish).toHaveBeenCalledTimes(1);expect(call.snapshot.recording).toBe(false)
 input.text('需求内容');expect(send).toHaveBeenCalledWith('需求内容',expect.any(Function),expect.any(AbortSignal))
 call.end()
})
