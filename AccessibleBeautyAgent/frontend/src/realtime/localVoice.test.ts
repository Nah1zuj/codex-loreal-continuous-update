import {beforeEach,afterEach,it,expect,vi} from 'vitest'
import {LocalRecognitionProvider} from './localVoice'
import type {RecognitionHandlers} from './voice'
let capture:any,track:any,stream:any,sockets:Socket[],nodes:any[]
class Socket{
 static OPEN=1;readyState=0;bufferedAmount=0;onopen:any;onerror:any;onclose:any;onmessage:any;sent:any[]=[]
 constructor(){sockets.push(this);queueMicrotask(()=>{this.readyState=1;this.onopen?.()})}
 send(value:any){this.sent.push(value);if(typeof value==='string'){const mode=JSON.parse(value);if(mode.type==='mode')queueMicrotask(()=>this.onmessage?.({data:JSON.stringify(mode)}))}}
 close=vi.fn(()=>{this.readyState=3})
}
function handlers(){return {onText:vi.fn(),onError:vi.fn(),onEnd:vi.fn(),onReady:vi.fn(),onProgress:vi.fn()} satisfies RecognitionHandlers}
async function settle(){for(let i=0;i<25;i++)await Promise.resolve()}
beforeEach(()=>{
 sockets=[];nodes=[];track={stop:vi.fn(),onended:null};stream={getTracks:()=>[track],getAudioTracks:()=>[track]};capture=vi.fn(async()=>stream)
 vi.stubGlobal('navigator',{mediaDevices:{getUserMedia:capture}})
 vi.stubGlobal('location',{protocol:'http:',host:'127.0.0.1:5174'})
 vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({ready:true})})))
 vi.stubGlobal('WebSocket',Socket)
 vi.stubGlobal('AudioWorkletNode',class{port={onmessage:null};disconnect=vi.fn();connect=vi.fn();constructor(){nodes.push(this)}})
 vi.stubGlobal('AudioContext',class{state='running';destination={};audioWorklet={addModule:vi.fn(async()=>{})};resume=vi.fn(async()=>{});close=vi.fn(async()=>{});createMediaStreamSource(){return {connect:vi.fn(),disconnect:vi.fn()}}createGain(){return {gain:{value:1},connect:vi.fn(),disconnect:vi.fn()}}})
})
afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers()})
it('reuses one capture across soft pause and wake, filters stale epoch callbacks, and closes on button end',async()=>{
 const provider=new LocalRecognitionProvider(),first=handlers();provider.startCycle(first);await settle()
 expect(first.onReady).toHaveBeenCalledTimes(1);expect(capture).toHaveBeenCalledTimes(1)
 const socket=sockets[0];const oldEpoch=JSON.parse(socket.sent.at(-1)).epoch
 provider.abort();provider.setMode('quiet');const quiet=handlers();provider.startCycle(quiet);await settle()
 expect(track.stop).not.toHaveBeenCalled();expect(capture).toHaveBeenCalledTimes(1)
 socket.onmessage({data:JSON.stringify({type:'transcript',text:'stale',epoch:oldEpoch})});expect(quiet.onText).not.toHaveBeenCalled()
 const epoch=JSON.parse(socket.sent.at(-1)).epoch;socket.onmessage({data:JSON.stringify({type:'transcript',text:'wake',epoch})});expect(quiet.onText).toHaveBeenCalledWith('wake')
 provider.stop();expect(track.stop).toHaveBeenCalledTimes(1);expect(socket.close).toHaveBeenCalledTimes(1)
})
it('closes a microphone returned after cancellation, without announcing ready',async()=>{
 let grant!:(stream:any)=>void;capture.mockImplementation(()=>new Promise(resolve=>{grant=resolve}));const provider=new LocalRecognitionProvider(),input=handlers()
 provider.startCycle(input);await settle();provider.stop();grant(stream);await settle()
 expect(track.stop).toHaveBeenCalled();expect(input.onReady).not.toHaveBeenCalled();expect(sockets).toHaveLength(0)
})
it('ignores an obsolete permission rejection while a replacement capture is listening',async()=>{
 let reject!:(error:Error)=>void;capture.mockImplementationOnce(()=>new Promise((_resolve,rejecter)=>{reject=rejecter}))
 const provider=new LocalRecognitionProvider(),old=handlers();provider.startCycle(old);await settle();provider.stop()
 const replacement=handlers();provider.startCycle(replacement);await settle();reject(new Error('old request'));await settle()
 expect(replacement.onReady).toHaveBeenCalledTimes(1);expect(replacement.onError).not.toHaveBeenCalled();expect(track.stop).not.toHaveBeenCalled();provider.stop()
})
it('releases late permission after the bounded startup wait fails',async()=>{
 vi.useFakeTimers();let grant!:(stream:any)=>void;capture.mockImplementation(()=>new Promise(resolve=>{grant=resolve}));const provider=new LocalRecognitionProvider(),input=handlers()
 provider.startCycle(input);await settle();await vi.advanceTimersByTimeAsync(45000);expect(input.onError).toHaveBeenCalledTimes(1)
 grant(stream);await settle();expect(track.stop).toHaveBeenCalled();expect(input.onReady).not.toHaveBeenCalled()
})

it('button capture controls use the acknowledged mode and report recording state',async()=>{
 const provider=new LocalRecognitionProvider(),input={...handlers(),onCapture:vi.fn()};provider.setMode('bounded');provider.startCycle(input);await settle()
 provider.beginCapture();const socket=sockets[0];const command=JSON.parse(socket.sent.at(-1));expect(command).toMatchObject({type:'capture',action:'start'})
 socket.onmessage({data:JSON.stringify({type:'capture',recording:true,epoch:command.epoch})});expect(input.onCapture).toHaveBeenCalledWith(true)
 provider.finishCapture();expect(JSON.parse(socket.sent.at(-1))).toMatchObject({type:'capture',action:'end',epoch:command.epoch})
 provider.stop()
})
