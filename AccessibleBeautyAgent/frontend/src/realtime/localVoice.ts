import type {RecognitionHandlers} from './voice'
export type VoiceInputMode='active'|'quiet'|'speaking'|'bounded'
export interface RecognitionEngine{
 readonly available:boolean;readonly local?:boolean
 setLocale(locale:'zh-CN'|'en'):void
 startCycle(handlers:RecognitionHandlers):void
 abort():void;stop():void
 setMode?(mode:VoiceInputMode):void
 beginCapture?():void;finishCapture?():void
}
/** A single owned microphone stream. Soft cancellation never closes it. */
export class LocalRecognitionProvider implements RecognitionEngine{
 readonly local=true
 private handlers:RecognitionHandlers|null=null
 private socket:WebSocket|null=null
 private stream:MediaStream|null=null
 private context:AudioContext|null=null
 private source:MediaStreamAudioSourceNode|null=null
 private worklet:AudioWorkletNode|null=null
 private gain:GainNode|null=null
 private connecting:Promise<void>|null=null
 private generation=0
 private epoch=0
 private acknowledged=-1
 private mode:VoiceInputMode='active'
 private capturePending=false
 get available(){return !!navigator.mediaDevices?.getUserMedia&&typeof AudioContext!=='undefined'&&typeof AudioWorkletNode!=='undefined'}
 setLocale(_locale:'zh-CN'|'en'){}
 startCycle(handlers:RecognitionHandlers){
  this.handlers=handlers
  if(this.stream&&this.socket?.readyState===WebSocket.OPEN){handlers.onReady?.();return}
  if(!this.connecting){const version=this.generation;const pending=this.connect();this.connecting=pending;void pending.catch(error=>{if(version!==this.generation)return;const current=this.handlers;this.stop();current?.onError(error instanceof Error?error.message:'本地语音未能启动')}).finally(()=>{if(this.connecting===pending)this.connecting=null})}
 }
 setMode(mode:VoiceInputMode){if(this.mode===mode&&this.acknowledged===this.epoch)return;this.mode=mode;++this.epoch;this.acknowledged=-1;if(this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'mode',mode,epoch:this.epoch}))}
 beginCapture(){this.capturePending=true;this.flushCapture()}
 finishCapture(){this.capturePending=false;if(this.mode==='bounded'&&this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'capture',action:'end',epoch:this.epoch}))}
 private flushCapture(){if(this.capturePending&&this.mode==='bounded'&&this.acknowledged===this.epoch&&this.socket?.readyState===WebSocket.OPEN){this.capturePending=false;this.socket.send(JSON.stringify({type:'capture',action:'start',epoch:this.epoch}))}}
 abort(){this.capturePending=false;this.handlers=null;this.setMode('quiet')}
 stop(){
  ++this.generation;this.capturePending=false;this.handlers=null;this.connecting=null;this.acknowledged=-1
  const socket=this.socket;this.socket=null;if(socket){socket.onclose=null;socket.onerror=null;socket.onmessage=null;socket.close()}
  this.worklet?.disconnect();this.worklet=null;this.source?.disconnect();this.source=null;this.gain?.disconnect();this.gain=null
  this.stream?.getTracks().forEach(track=>{track.onended=null;track.stop()});this.stream=null
  const context=this.context;this.context=null;if(context)void context.close().catch(()=>{})
 }
 private async connect(){
  if(!this.available)throw new Error('当前浏览器缺少本地音频采集能力，请使用支持麦克风与AudioWorklet的浏览器。')
  const version=this.generation
  this.handlers?.onProgress?.('正在检查本机语音服务')
  const health=await fetch('/local-voice/health',{signal:AbortSignal.timeout(12000)}).then(async response=>{if(!response.ok)throw new Error('本地语音服务尚未启动，请使用本项目启动入口。');return response.json()})
  if(!health.ready)throw new Error('本地中文语音模型尚未就绪。')
  if(version!==this.generation)return
  this.handlers?.onProgress?.('等待浏览器与系统提供麦克风。请完成首次许可。')
  const acquisition=navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false}).then(stream=>{if(version!==this.generation)stream.getTracks().forEach(track=>track.stop());return stream})
  const stream=await deadline(acquisition,45000,'麦克风仍未返回。请检查系统中的 Codex 或当前浏览器麦克风许可，再重新开启语音引导。')
  if(version!==this.generation){stream.getTracks().forEach(track=>track.stop());return}
  this.stream=stream
  this.handlers?.onProgress?.('麦克风已连接，正在准备本地音频处理')
  const context=new AudioContext();this.context=context
  await deadline(context.audioWorklet.addModule('/voice-pcm-worklet.js'),12000,'浏览器未能载入本地音频处理模块。')
  if(version!==this.generation)return
  await deadline(context.resume(),12000,'浏览器未激活音频，请重新操作开启语音引导。')
  if(version!==this.generation)return
  if(context.state!=='running')throw new Error('浏览器尚未激活声音，请通过系统语音控制操作“开启语音引导”。')
  this.handlers?.onProgress?.('正在连接本地识别与唤醒服务')
  const ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/local-voice/stream');this.socket=ws
  await new Promise<void>((resolve,reject)=>{
   const timeout=setTimeout(()=>{reject(new Error('本地语音连接超时'));ws.close()},12000)
   ws.onopen=()=>{clearTimeout(timeout);resolve()};ws.onerror=()=>{clearTimeout(timeout);reject(new Error('本地语音连接失败'))}
  })
  if(version!==this.generation){ws.close();return}
  let acknowledge:()=>void=()=>{}
  const acknowledged=new Promise<void>(resolve=>{acknowledge=resolve})
  ws.onmessage=event=>{if(version!==this.generation)return;const item=JSON.parse(event.data);if(item.type==='mode'&&item.epoch===this.epoch){this.acknowledged=item.epoch;acknowledge();this.flushCapture()}if(item.type==='capture'&&item.epoch===this.epoch)this.handlers?.onCapture?.(!!item.recording);if(item.type==='capture'&&item.epoch===this.epoch)this.handlers?.onProgress?.(item.recording?'正在收集本段内容，说“结束”后提交。':item.discarded?'本段未提交，请说“开始”重新表达。':'等待“开始”。');if(item.type==='transcript'&&item.epoch===this.epoch){this.handlers?.onCapture?.(false);this.handlers?.onText(item.text)}}
  ws.onclose=()=>{if(version===this.generation){const current=this.handlers;this.stop();current?.onError('本地语音连接已断开。当前步骤保留，可重新开启语音引导。')}}
  this.setMode(this.mode)
  await deadline(acknowledged,12000,'本地语音服务未确认就绪。请重新开启语音引导。')
  if(version!==this.generation)return
  const source=context.createMediaStreamSource(stream),worklet=new AudioWorkletNode(context,'trace-pcm'),gain=context.createGain();gain.gain.value=0
  this.source=source;this.worklet=worklet;this.gain=gain
  worklet.port.onmessage=event=>{if(version===this.generation&&ws.readyState===WebSocket.OPEN&&this.acknowledged===this.epoch&&ws.bufferedAmount<256000)ws.send(event.data)}
  source.connect(worklet);worklet.connect(gain);gain.connect(context.destination)
  stream.getAudioTracks().forEach(track=>{track.onended=()=>{if(version===this.generation){const current=this.handlers;this.stop();current?.onError('麦克风许可已撤回或设备已断开。')}}})
  this.handlers?.onReady?.()
 }
}
function deadline<T>(pending:Promise<T>,ms:number,message:string):Promise<T>{
 return new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error(message)),ms);pending.then(value=>{clearTimeout(timer);resolve(value)},error=>{clearTimeout(timer);reject(error)})})
}
