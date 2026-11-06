import {humanError} from '../content/errors'
import {BrowserTTSProvider} from './voice'
import type {RecognitionEngine,VoiceInputMode} from './localVoice'
import {isSoftPause,isMicrophoneClosePhrase,wakeInput} from './voiceCommands'
export type CallState='idle'|'requesting_permission'|'listening'|'thinking'|'speaking'|'paused'|'quiet_wake'|'ended'|'error'
export interface CallSnapshot {state:CallState;transcript:string;reply:string;error:string;progress?:string;recording?:boolean;transcribing?:boolean}
/** The browser owns permission. Soft pause retains only the local wake listener. */
export class RealtimeCallController {
 private value:CallSnapshot={state:'idle',transcript:'',reply:'',error:''}
 private bounded=false
 private capturePending=false
 setBounded(enabled:boolean){if(this.bounded===enabled)return;this.bounded=enabled;if(this.voiceActive&&['listening','requesting_permission'].includes(this.state)){this.cancel();this.listen()}else if(this.voiceActive)this.recognition.setMode?.('quiet')}
 private generation=0
 private voiceActive=false
 private inputReady=false
 private locale:'zh-CN'|'en'='zh-CN'
 private listeners=new Set<(snapshot:CallSnapshot)=>void>()
 private request:AbortController|null=null
 private finishSpeech:(()=>void)|null=null
 onReady:(()=>void)|null=null
 private readyAnnounced=false
 constructor(private recognition:RecognitionEngine,private tts:BrowserTTSProvider,private sendTranscript:(text:string,onDelta?:(part:string)=>void,signal?:AbortSignal)=>Promise<string>){}
 setLocale(locale:'zh-CN'|'en'){this.locale=locale;if(!['idle','ended'].includes(this.state))this.pause();this.recognition.setLocale(locale);this.tts.setLocale(locale);this.update(this.state,{transcript:'',reply:'',error:''})}
 get available(){return this.recognition.available}
 get state(){return this.value.state}
 get snapshot():CallSnapshot{return {...this.value}}
 private get readyProgress(){
  if(!this.bounded)return ''
  return this.locale==='en'?'Say “kai shi”, make your request, then say “jie shu” to submit it.':'请说“开始”，表达需求后说“结束”，再提交分析。'
 }
 subscribe(listener:(snapshot:CallSnapshot)=>void){this.listeners.add(listener);listener(this.snapshot);return ()=>{this.listeners.delete(listener)}}
 private update(state:CallState,fields:Partial<CallSnapshot>={}){this.value={...this.value,...fields,state};for(const listener of this.listeners)listener(this.snapshot)}
 private cancel(){this.capturePending=false;this.value={...this.value,recording:false,transcribing:false};++this.generation;this.request?.abort();this.request=null;this.finishSpeech?.();this.finishSpeech=null;this.recognition.abort();this.tts.onState=null;this.tts.stop()}
 start(record=false){
  if(this.state==='ended'||!['idle','error','paused','quiet_wake'].includes(this.state))return
  this.cancel();this.capturePending=record;this.voiceActive=true;this.readyAnnounced=false;const generation=this.generation
  this.update('requesting_permission',{error:'',progress:''})
  if(generation===this.generation&&this.state==='requesting_permission')this.listen()
 }
 beginCapture(){
  if(!this.bounded||!this.recognition.beginCapture||this.value.transcribing)return
  if(['idle','error','paused','quiet_wake'].includes(this.state)){this.start(true);return}
  if(this.state==='requesting_permission'){this.capturePending=true;return}
  if(this.state==='speaking')this.interrupt()
  if(this.state==='listening'){this.update('listening',{error:'',progress:this.locale==='en'?'Preparing recording…':'正在准备录音…'});this.recognition.beginCapture()}
 }
 discardCapture(){
  if(this.state!=='listening'&&this.state!=='requesting_permission')return
  this.cancel()
  if(this.state==='requesting_permission'){
   this.inputReady=false;this.voiceActive=false;this.recognition.stop()
   this.update('paused',{transcript:'',progress:''})
  }else this.listen()
 }
 private showTranscription(){
  this.update('listening',{recording:false,transcribing:true,
   progress:this.locale==='en'?'Transcribing this request…':'正在识别这一段…'})
 }
 finishCapture(){
  if(this.state!=='listening'||!this.value.recording)return
  this.showTranscription()
  this.recognition.finishCapture?.()
 }
 pause(){
  if(this.state==='ended'||this.state==='quiet_wake'||this.state==='paused')return
  const live=this.voiceActive&&this.inputReady&&this.recognition.local
  if(!live&&this.state==='requesting_permission'){this.recognition.stop();this.inputReady=false}
  if(!live)this.voiceActive=false
  this.cancel();this.update(live?'quiet_wake':'paused',{transcript:''})
  if(live)this.bindInput('quiet')
 }
 resume(){if(this.state==='quiet_wake'){this.voiceActive=true;this.cancel();this.listen();this.announce(this.locale==='en'?'I am here. Please continue.':'我在，请继续。')}else if(this.state==='paused')this.start()}
 interrupt(){if(this.state!=='speaking'&&this.state!=='thinking')return;this.cancel();if(this.voiceActive)this.listen();else this.update('paused')}
 end(){if(this.state==='ended')return;this.voiceActive=false;this.inputReady=false;this.cancel();this.recognition.stop();this.update('ended')}
 submit(text:string){if(this.state==='ended'||!text.trim())return;const resume=this.voiceActive;this.cancel();const generation=this.generation;this.update('thinking',{transcript:text,reply:'',error:'',progress:''});if(generation!==this.generation||this.state!=='thinking')return;if(this.recognition.local&&resume)this.bindInput('active');void this.respond(text,generation,resume)}
 announce(text:string){
  if(this.state==='ended'||this.state==='quiet_wake'||!text.trim())return
  const resume=this.voiceActive&&this.state!=='paused';this.cancel();const generation=this.generation
  this.update('speaking',{reply:text,error:'',progress:''});if(generation!==this.generation)return
  if(this.recognition.local&&resume)this.bindInput('speaking')
  this.tts.onState=()=>{if(generation===this.generation&&this.tts.state==='error')this.fail('语音播放失败，内容已保留为文字。')}
  const accepted=this.tts.speak(text,false,()=>{if(generation===this.generation){this.tts.onState=null;if(resume)this.listen();else this.update('paused')}})
  if(!accepted&&generation===this.generation)this.fail('语音不可用，内容已保留为文字。')
 }
 private fail(message:string,recognitionFailure=false){
  const retained=this.voiceActive&&this.recognition.local&&!recognitionFailure
  this.cancel()
  if(recognitionFailure){this.inputReady=false;this.recognition.stop()}
  this.voiceActive=!!retained
  if(retained){this.update('quiet_wake',{error:message+' 可以说重新启动语音交流功能重试。'});this.bindInput('quiet')}
  else {this.update('error',{error:message+' 请使用文字输入，或重新开启语音引导。'});if(recognitionFailure)this.tts.speak(humanError(message,this.locale))}
 }
 private bindInput(mode:VoiceInputMode){
  const generation=this.generation
  this.recognition.setMode?.(this.bounded?(mode==='active'&&['listening','requesting_permission'].includes(this.state)?'bounded':'quiet'):mode)
  this.recognition.startCycle({
   onCapture:recording=>{if(generation===this.generation&&this.state==='listening')this.update('listening',{recording,transcribing:false})},
   onTranscribing:()=>{if(generation===this.generation&&this.state==='listening')this.showTranscription()},
   onProgress:message=>{if(generation===this.generation&&['requesting_permission','listening'].includes(this.state))this.update(this.state,{progress:message})},
   onReady:()=>{if(generation!==this.generation)return;this.inputReady=true;if(this.state==='requesting_permission')this.update('listening',{progress:this.readyProgress});if(this.capturePending&&this.state==='listening'){this.capturePending=false;this.readyAnnounced=true;this.recognition.beginCapture?.();return}if(!this.readyAnnounced&&this.state==='listening'){this.readyAnnounced=true;this.onReady?.()}},
   onText:text=>{
    if(generation!==this.generation||this.state==='ended')return
    const wake=wakeInput(text)
    if(this.state==='quiet_wake'){
     if(wake===null)return
     this.voiceActive=true;this.cancel();this.listen()
     if(wake&&!this.bounded)this.submit(wake);else this.announce(this.locale==='en'?'I am here. Please continue.':'我在，请继续。')
     return
    }
    if(!this.recognition.local&&this.state!=='listening')return
    if(isSoftPause(text)){this.pause();return}
    if(isMicrophoneClosePhrase(text)){if(this.voiceActive)this.announce(this.locale==='en'?'Closing the microphone is available through its button. You can pause replies by voice.':'关闭麦克风使用按钮。需要安静时，可以说请终止对话。');return}
    if(this.state!=='listening')return
    if(wake!==null){if(wake&&!this.bounded)this.submit(wake);else this.announce(this.locale==='en'?'I am here.':'我在，请继续。');return}
    if(!text.trim())return
    this.submit(text)
   },
   onError:message=>{if(generation===this.generation)this.fail(message,true)},
   onEnd:()=>{if(generation===this.generation&&this.state==='listening'&&!this.recognition.local)this.pause()},
  })
 }
 private listen(){
  ++this.generation
  if(!this.recognition.local)this.update('listening')
  else if(this.state!=='requesting_permission')this.update('listening',{progress:this.readyProgress})
  const generation=this.generation
  if(generation===this.generation&&(this.state==='listening'||this.state==='requesting_permission'))this.bindInput('active')
 }
 private async respond(text:string,generation:number,resume=true){
  if(generation!==this.generation||this.state!=='thinking')return
  try{
   this.request=new AbortController()
   let streamed='',pending='',spoken='',chain=Promise.resolve(),speechFailed=false
   const speechFallback=()=>{speechFailed=true;this.voiceActive=false;this.tts.onState=null;this.tts.stop();this.finishSpeech=null;this.update(this.recognition.local?'quiet_wake':'error',{error:this.locale==='en'?'Speech unavailable; the complete reply will remain as text.':'语音播放不可用。完整回复将保留为文字。'});if(this.recognition.local){this.voiceActive=true;this.bindInput('quiet')}}
   const enqueue=(sentence:string)=>{
    spoken+=sentence
    chain=chain.then(()=>new Promise<void>(resolve=>{
     if(generation!==this.generation||speechFailed){resolve();return}
     this.update('speaking',{reply:streamed});if(generation!==this.generation){resolve();return}if(this.recognition.local&&resume)this.bindInput('speaking')
     this.finishSpeech=resolve
     this.tts.onState=()=>{if(generation===this.generation&&this.tts.state==='error'){speechFallback();resolve()}}
     if(!this.tts.speak(sentence,false,()=>{this.finishSpeech=null;resolve()})){speechFallback();resolve()}
    }))
   }
   const reply=await this.sendTranscript(text,part=>{
    if(generation!==this.generation)return
    streamed+=part;pending+=part;this.update(this.state,{reply:streamed})
    let match:RegExpMatchArray|null
    while((match=pending.match(/^([\s\S]*?[。！？.!?](?:\s|$))/))){enqueue(match[1]);pending=pending.slice(match[1].length)}
   },this.request.signal)
   if(generation!==this.generation)return
   if(streamed){
    const remainder=reply.startsWith(spoken)?reply.slice(spoken.length):pending
    if(remainder.trim())enqueue(remainder)
    await chain
    if(generation!==this.generation)return
    if(speechFailed){this.request=null;this.update(this.recognition.local?'quiet_wake':'error',{reply});return}
    this.tts.onState=null;this.request=null;this.update(this.state,{reply})
    if(resume)this.listen();else this.update('paused')
    return
   }
   if(this.state!=='thinking')return
   this.update('speaking',{reply})
   if(generation!==this.generation||this.snapshot.state!=='speaking')return
   if(this.recognition.local&&resume)this.bindInput('speaking')
   this.tts.onState=()=>{if(generation===this.generation&&this.tts.state==='error')this.fail('语音播放失败。回复已保留为文字。')}
   const accepted=this.tts.speak(reply,false,()=>{if(generation===this.generation&&this.state==='speaking'){this.tts.onState=null;if(resume)this.listen();else this.update('paused')}})
   if(!accepted&&generation===this.generation)this.fail('语音播放不可用。回复已保留为文字。')
  }catch(error){if(generation===this.generation)this.fail('请求失败：'+String(error))}
 }
}
