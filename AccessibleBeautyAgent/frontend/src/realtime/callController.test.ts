import {afterEach,expect,it,vi} from 'vitest'
import {BrowserTTSProvider,ContinuousRecognitionProvider} from './voice'
import {RealtimeCallController} from './callController'
afterEach(()=>vi.unstubAllGlobals())
function setup(send=(t:string)=>Promise.resolve('reply '+t),available=true){
 const rs:any[]=[],us:any[]=[]
 class Recognition {onresult:any;onerror:any;onend:any;start(){}stop(){}abort(){}constructor(){rs.push(this)}}
 vi.stubGlobal('window',{SpeechRecognition:Recognition,...(available?{speechSynthesis:{cancel(){},speak:(u:any)=>us.push(u)}}:{})})
 vi.stubGlobal('SpeechSynthesisUtterance',class {constructor(public text:string){}})
 const call=new RealtimeCallController(new ContinuousRecognitionProvider(),new BrowserTTSProvider(),send)
 const text=(t:string)=>rs.at(-1).onresult({results:[{isFinal:true,0:{transcript:t}}]})
 return {call,rs,us,text}
}
const flush=async()=>{await Promise.resolve();await Promise.resolve()}
it('replacing or interrupting text-only speech never starts recognition',async()=>{const {call,rs,us}=setup();call.submit('start');await flush();call.submit('repeat');await flush();us[1].onend();expect(rs).toHaveLength(0);expect(call.state).toBe('paused');call.submit('why');await flush();call.interrupt();expect(rs).toHaveLength(0);expect(call.state).toBe('paused')})
it('announces an actual visual observation without another API turn and ignores late speech after end',()=>{const send=vi.fn(async()=> 'unused');const {call,rs,us}=setup(send);call.start();call.announce('Uncalibrated cheek color observation');expect(call.state).toBe('speaking');expect(send).not.toHaveBeenCalled();const completed=us[0].onend;call.end();completed();expect(call.state).toBe('ended');expect(rs.length).toBe(1)})
it('TTS failure preserves the complete streaming text and does not abort transport',async()=>{
 let finish!:(value:string)=>void;let push!:(part:string)=>void;let signal:AbortSignal|undefined
 const {call,text}=setup(((value:string,onDelta:(part:string)=>void,abort:AbortSignal)=>{push=onDelta;signal=abort;onDelta('第一句。');return new Promise<string>(r=>finish=r)}) as any,false)
 call.start();text('下一步');await flush();expect(signal?.aborted).toBe(false)
 push('第二句完整文字。');finish('第一句。第二句完整文字。');await flush();await flush()
 expect(call.snapshot.reply).toBe('第一句。第二句完整文字。');expect(call.state).toBe('error')
})
it('speaks the first complete streamed sentence before the response ends and cancels transport',async()=>{
 let finish!:(value:string)=>void;let signal:AbortSignal|undefined
 const {call,us,text}=setup(((value:string,onDelta?:(part:string)=>void,abort?:AbortSignal)=>{signal=abort;onDelta?.('第一句。');return new Promise<string>(r=>finish=r)}) as any)
 call.start();text('hello');await flush();expect(us[0]?.text).toBe('第一句。');expect(call.state).toBe('speaking')
 call.interrupt();expect(signal?.aborted).toBe(true);finish('第一句。第二句。');await flush();expect(us.length).toBe(1)
})
it('one click starts synchronously and notifies subscribers',()=>{const {call,rs}=setup();const states:string[]=[];const off=call.subscribe(s=>states.push(s.state));call.start();expect(rs.length).toBe(1);expect(call.state).toBe('listening');expect(states).toContain('requesting_permission');off()})
it('thinking speaking listening and no self echo',async()=>{const {call,rs,us,text}=setup();call.start();const late=rs[0].onresult;text('hello');expect(call.state).toBe('thinking');await flush();expect(call.state).toBe('speaking');late({results:[{isFinal:true,0:{transcript:'echo'}}]});expect(rs.length).toBe(1);expect(us.length).toBe(1);us[0].onend();expect(call.state).toBe('listening');expect(rs.length).toBe(2)})
it('manual interrupt ignores old speech end',async()=>{const {call,rs,us,text}=setup();call.start();text('hi');await flush();const end=us[0].onend;call.interrupt();end();expect(call.state).toBe('listening');expect(rs.length).toBe(2)})
it('pause resume ignores old recognition',()=>{const {call,rs}=setup();call.start();const late=rs[0].onresult;call.pause();late({results:[{isFinal:true,0:{transcript:'late'}}]});expect(call.state).toBe('paused');call.resume();expect(call.state).toBe('listening');expect(rs.length).toBe(2)})
it('network error falls back to text until manual restart',async()=>{const {call,rs,text}=setup(()=>Promise.reject(new Error('offline')));call.start();text('hi');await flush();expect(call.state).toBe('error');expect(call.snapshot.error).toContain('文字');expect(rs.length).toBe(1);call.start();expect(call.state).toBe('listening')})
it.each(['end','pause'])('%s invalidates pending chat',async action=>{let resolve!:(t:string)=>void;const {call,rs,us,text}=setup(()=>new Promise(r=>resolve=r));call.start();text('hi');call[action as 'end'|'pause']();resolve('late');await flush();expect(us.length).toBe(0);expect(call.state).toBe(action==='end'?'ended':'paused');if(action==='end'){call.start();call.resume();call.interrupt();expect(call.state).toBe('ended');expect(rs.length).toBe(1)}})
it.each(['stop','停止'])('spoken %s pauses replies without ending the call',command=>{const send=vi.fn(async()=> 'reply');const {call,text}=setup(send);call.start();text(command);expect(call.state).toBe('paused');expect(send).not.toHaveBeenCalled()})
it('terminal ASR errors do not restart on end',()=>{const {call,rs}=setup();call.start();const end=rs[0].onend;rs[0].onerror({error:'not-allowed'});end();expect(call.state).toBe('error');expect(rs.length).toBe(1)})
it('natural no speech end pauses without looping',()=>{const {call,rs}=setup();call.start();rs[0].onend();expect(call.state).toBe('paused');expect(rs.length).toBe(1)})
it.each([true,false])('TTS error fallback available=%s',async available=>{const {call,rs,us,text}=setup(undefined,available);call.start();text('hi');await flush();if(available)us[0].onerror();expect(call.state).toBe('error');expect(call.snapshot.reply).toBe('reply hi');expect(rs.length).toBe(1)})
it('end ignores late TTS completion',async()=>{const {call,rs,us,text}=setup();call.start();text('hi');await flush();const end=us[0].onend;call.end();end();expect(call.state).toBe('ended');expect(rs.length).toBe(1)})
it.each(['end','pause'])('subscriber %s during permission prevents recognition',action=>{const {call,rs}=setup();call.subscribe(s=>{if(s.state==='requesting_permission')call[action as 'end'|'pause']()});call.start();expect(call.state).toBe(action==='end'?'ended':'paused');expect(rs.length).toBe(0)})
it.each(['end','pause'])('subscriber %s during thinking prevents chat',async action=>{const send=vi.fn(async()=> 'reply');const {call,text}=setup(send);call.subscribe(s=>{if(s.state==='thinking')call[action as 'end'|'pause']()});call.start();text('hi');await flush();expect(call.state).toBe(action==='end'?'ended':'paused');expect(send).not.toHaveBeenCalled()})
it('speaks a button command and resumes only if the call was already live',async()=>{const {call,rs,us}=setup();call.start();call.submit('repeat');await flush();expect(call.state).toBe('speaking');expect(rs.length).toBe(1);us[0].onend();expect(call.state).toBe('listening');call.pause();call.submit('why');await flush();us[1].onend();expect(call.state).toBe('paused');expect(rs.length).toBe(2)})
