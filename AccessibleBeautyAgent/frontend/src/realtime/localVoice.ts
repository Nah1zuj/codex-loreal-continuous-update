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
 private connectionAbort:AbortController|null=null
 private locale:'zh-CN'|'en'='zh-CN'
 private generation=0
 private epoch=0
 private acknowledged=-1
 private mode:VoiceInputMode='active'
 private capturePending=false
 get available(){return !!navigator.mediaDevices?.getUserMedia&&typeof AudioContext!=='undefined'&&typeof AudioWorkletNode!=='undefined'}
 setLocale(locale:'zh-CN'|'en'){this.locale=locale}
 startCycle(handlers:RecognitionHandlers){
  this.handlers=handlers
  if(this.stream&&this.socket?.readyState===WebSocket.OPEN){handlers.onReady?.();return}
  if(this.connecting)return
  const version=this.generation
  const controller=new AbortController()
  this.connectionAbort=controller
  const pending=this.connect(controller.signal)
  this.connecting=pending
  void pending.catch(error=>{
   if(version!==this.generation)return
   const current=this.handlers
   this.stop()
   current?.onError(error instanceof Error?error.message:'本地语音未能启动')
  }).finally(()=>{
   if(this.connecting===pending){this.connecting=null;this.connectionAbort=null}
  })
 }
 setMode(mode:VoiceInputMode){if(this.mode===mode&&this.acknowledged===this.epoch)return;this.mode=mode;++this.epoch;this.acknowledged=-1;if(this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'mode',mode,epoch:this.epoch}))}
 beginCapture(){this.capturePending=true;this.flushCapture()}
 finishCapture(){this.capturePending=false;if(this.mode==='bounded'&&this.socket?.readyState===WebSocket.OPEN)this.socket.send(JSON.stringify({type:'capture',action:'end',epoch:this.epoch}))}
 private flushCapture(){if(this.capturePending&&this.mode==='bounded'&&this.acknowledged===this.epoch&&this.socket?.readyState===WebSocket.OPEN){this.capturePending=false;this.socket.send(JSON.stringify({type:'capture',action:'start',epoch:this.epoch}))}}
 abort(){this.capturePending=false;this.handlers=null;this.setMode('quiet')}
 stop(){
  ++this.generation;this.capturePending=false;this.handlers=null;this.connecting=null;this.acknowledged=-1
  this.connectionAbort?.abort();this.connectionAbort=null
  if(this.worklet)this.worklet.port.onmessage=null
  const socket=this.socket;this.socket=null;if(socket){socket.onopen=null;socket.onclose=null;socket.onerror=null;socket.onmessage=null;socket.close()}
  this.worklet?.disconnect();this.worklet=null;this.source?.disconnect();this.source=null;this.gain?.disconnect();this.gain=null
  this.stream?.getTracks().forEach(track=>{track.onended=null;track.stop()});this.stream=null
  const context=this.context;this.context=null;if(context)void context.close().catch(()=>{})
 }
 private async connect(signal:AbortSignal){
  if(!this.available)throw new Error('当前浏览器缺少本地音频采集能力，请使用支持麦克风与AudioWorklet的浏览器。')
  const version=this.generation
  this.handlers?.onProgress?.(this.locale==='en'?'Checking the local voice service':'正在检查本机语音服务')
  const health=await fetch('/local-voice/health',{signal:AbortSignal.any([signal,AbortSignal.timeout(12000)])}).then(async response=>{if(!response.ok)throw new Error('本地语音服务尚未启动，请使用本项目启动入口。');return response.json()})
  if(!health.ready)throw new Error('本地中文语音模型尚未就绪。')
  if(version!==this.generation)return
  this.handlers?.onProgress?.(this.locale==='en'?'Waiting for microphone access. Allow it in your browser and system settings when prompted.':'等待浏览器与系统提供麦克风。请完成首次许可。')
  const acquisition=navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false}).then(stream=>{if(version!==this.generation)stream.getTracks().forEach(track=>track.stop());return stream})
  const stream=await deadline(acquisition,signal,45000,'麦克风仍未返回。请检查系统中的 Codex 或当前浏览器麦克风许可，再重新开启语音引导。')
  if(version!==this.generation){stream.getTracks().forEach(track=>track.stop());return}
  this.stream=stream
  this.handlers?.onProgress?.(this.locale==='en'?'Microphone connected. Preparing local audio processing.':'麦克风已连接，正在准备本地音频处理')
  const context=new AudioContext();this.context=context
  await deadline(context.audioWorklet.addModule('/voice-pcm-worklet.js'),signal,12000,'浏览器未能载入本地音频处理模块。')
  if(version!==this.generation)return
  await deadline(context.resume(),signal,12000,'浏览器未激活音频，请重新操作开启语音引导。')
  if(version!==this.generation)return
  if(context.state!=='running')throw new Error('浏览器尚未激活声音，请通过系统语音控制操作“开启语音引导”。')
  this.handlers?.onProgress?.(this.locale==='en'?'Connecting to local speech recognition and wake phrase detection':'正在连接本地识别与唤醒服务')
  const ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/local-voice/stream');this.socket=ws
  await deadline(new Promise<void>((resolve,reject)=>{
   ws.onopen=()=>resolve()
   ws.onerror=()=>reject(new Error('本地语音连接失败'))
   ws.onclose=()=>reject(new Error('本地语音连接已断开'))
  }),signal,12000,'本地语音连接超时')
  if(version!==this.generation){ws.close();return}
  let acknowledge:()=>void=()=>{}
  const acknowledged=new Promise<void>(resolve=>{acknowledge=resolve})
  ws.onmessage=event=>{
   if(version!==this.generation)return
   let item
   try{item=JSON.parse(event.data)}catch{return}
   if(item.epoch!==this.epoch)return
   if(item.type==='mode'){
    this.acknowledged=item.epoch;acknowledge();this.flushCapture()
   }else if(item.type==='capture'){
    this.handlers?.onCapture?.(!!item.recording)
    const en=this.locale==='en'
    const message=item.recording
     ? (en?'Recording. Say “结束” or submit when done.':'正在收集本段内容，说“结束”后提交。')
     : item.reason==='duration_limit'
      ? (en?'Recording exceeded 120 seconds and was discarded. Record a shorter request.':'录音超过 120 秒，已丢弃。请重新录制较短的一段。')
      : item.discarded
       ? (en?'Recording was not submitted. Start a new request.':'本段未提交，请说“开始”重新表达。')
       : (en?'Waiting for the start keyword.':'等待“开始”。')
    this.handlers?.onProgress?.(message)
   }else if(item.type==='transcribing'){
    this.handlers?.onTranscribing?.()
   }else if(item.type==='transcript'&&typeof item.text==='string'){
    this.handlers?.onCapture?.(false)
    this.handlers?.onText(item.text)
   }
  }
  ws.onclose=()=>{if(version===this.generation){const current=this.handlers;this.stop();current?.onError('本地语音连接已断开。当前步骤保留，可重新开启语音引导。')}}
  this.setMode(this.mode)
  await deadline(acknowledged,signal,12000,'本地语音服务未确认就绪。请重新开启语音引导。')
  if(version!==this.generation)return
  const source=context.createMediaStreamSource(stream),worklet=new AudioWorkletNode(context,'trace-pcm'),gain=context.createGain();gain.gain.value=0
  this.source=source;this.worklet=worklet;this.gain=gain
  worklet.port.onmessage=event=>{if(version===this.generation&&ws.readyState===WebSocket.OPEN&&this.acknowledged===this.epoch&&ws.bufferedAmount<256000)ws.send(event.data)}
  source.connect(worklet);worklet.connect(gain);gain.connect(context.destination)
  stream.getAudioTracks().forEach(track=>{track.onended=()=>{if(version===this.generation){const current=this.handlers;this.stop();current?.onError('麦克风许可已撤回或设备已断开。')}}})
  this.handlers?.onReady?.()
 }
}
function deadline<T>(pending:Promise<T>,signal:AbortSignal,ms:number,message:string):Promise<T>{
 return new Promise((resolve,reject)=>{
  const cancel=()=>{cleanup();reject(signal.reason)}
  const cleanup=()=>{clearTimeout(timer);signal.removeEventListener('abort',cancel)}
  const timer=setTimeout(()=>{cleanup();reject(new Error(message))},ms)
  pending.then(value=>{cleanup();resolve(value)},error=>{cleanup();reject(error)})
  signal.addEventListener('abort',cancel,{once:true})
  if(signal.aborted)cancel()
 })
}
