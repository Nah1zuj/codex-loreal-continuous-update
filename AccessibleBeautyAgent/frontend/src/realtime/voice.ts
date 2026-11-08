export interface TextChatProvider {send(text:string):Promise<void>}
export interface RealtimeVoiceProvider {connect(sessionId:string):Promise<{realtime:boolean;capabilities:string[];notice:string}>}
export class BrowserTTSProvider {
  private locale:'zh-CN'|'en'='zh-CN'
  setLocale(locale:'zh-CN'|'en'){if(this.locale!==locale){this.stop();this.locale=locale}}

  state:'idle'|'speaking'|'paused'|'error'='idle'
  private generation=0
  private utterance:SpeechSynthesisUtterance|null=null
  onState:(()=>void)|null=null
  private update(state:'idle'|'speaking'|'paused'|'error'){this.state=state;this.onState?.()}
  pause(){if('speechSynthesis' in window){window.speechSynthesis.pause();this.update('paused')}}
  resume(){if('speechSynthesis' in window){window.speechSynthesis.resume();this.update('speaking')}}
  private clearUtterance(){if(this.utterance){this.utterance.onstart=null;this.utterance.onend=null;this.utterance.onerror=null;this.utterance=null}}
  stop(){ ++this.generation;this.clearUtterance();if('speechSynthesis' in window) window.speechSynthesis.cancel();this.update('idle') }
  speak(text:string,slow=false,onEnd?:()=>void){
    if(!window.speechSynthesis||typeof SpeechSynthesisUtterance!=='function'){this.update('error');return false}
    this.stop()
    const generation=this.generation
    const utterance=new SpeechSynthesisUtterance(text)
    this.utterance=utterance
    utterance.lang=this.locale==='en'?'en-US':'zh-CN';utterance.rate=slow?.72:.95
    utterance.onstart=()=>{if(generation===this.generation)this.update('speaking')};utterance.onend=()=>{if(generation===this.generation){++this.generation;this.clearUtterance();this.update('idle');onEnd?.()}};utterance.onerror=()=>{if(generation===this.generation){++this.generation;this.clearUtterance();this.update('error')}}
    try{window.speechSynthesis.speak(utterance)}catch{++this.generation;this.clearUtterance();this.update('error');return false}
    return true
  }
}
interface SpeechResult {isFinal:boolean;0:{transcript:string}}
interface Recognition {
  lang:string;continuous:boolean;interimResults:boolean;
  onresult:((event:{results:ArrayLike<SpeechResult>})=>void)|null;
  onerror:((event:{error:string})=>void)|null;
  onend:(()=>void)|null;
  start():void;stop():void;abort():void
}
type VoiceWindow=Window&{SpeechRecognition?:new()=>Recognition;webkitSpeechRecognition?:new()=>Recognition}
export type RecognitionHandlers={onText:(text:string)=>void;onError:(message:string)=>void;onEnd:()=>void;onReady?:()=>void;onProgress?:(message:string)=>void;onCapture?:(recording:boolean)=>void;onTranscribing?:()=>void}
export class ContinuousRecognitionProvider {
  private locale:'zh-CN'|'en'='zh-CN'
  setLocale(locale:'zh-CN'|'en'){if(this.locale!==locale){this.abort();this.locale=locale}}

  private recognition:Recognition|null=null
  private generation=0
  get available(){return !!((window as VoiceWindow).SpeechRecognition||(window as VoiceWindow).webkitSpeechRecognition)}
  startCycle(handlers:RecognitionHandlers){
    const Constructor=(window as VoiceWindow).SpeechRecognition||(window as VoiceWindow).webkitSpeechRecognition
    if(!Constructor){handlers.onError(this.locale==='en'?'Speech recognition is unavailable. Use text input.':'此浏览器不支持语音识别，请使用文字输入。');return}
    this.abort();const generation=this.generation;let emitted=false;const recognition=new Constructor()
    recognition.lang=this.locale==='en'?'en-US':'zh-CN';recognition.continuous=false;recognition.interimResults=false
    recognition.onresult=event=>{if(generation!==this.generation||emitted)return;const result=event.results[0];if(result?.isFinal){emitted=true;handlers.onText(result[0].transcript.trim())}}
    recognition.onerror=event=>{if(generation===this.generation)handlers.onError(this.locale==='en'?'Recognition did not finish: '+event.error+'. Use text.':'语音识别未完成：'+event.error+'。可以改用文字。')}
    recognition.onend=()=>{if(generation===this.generation){++this.generation;this.clearRecognition();handlers.onEnd()}}
    this.recognition=recognition
    try{recognition.start();handlers.onReady?.()}catch(error){this.clearRecognition();++this.generation;handlers.onError(this.locale==='en'?'Recognition did not finish: '+String(error)+'. Use text.':'语音识别未完成：'+String(error)+'。可以改用文字。')}
  }
  private clearRecognition(){const current=this.recognition;this.recognition=null;if(current){current.onresult=null;current.onerror=null;current.onend=null}return current}
  stop(){++this.generation;this.clearRecognition()?.stop()}
  abort(){++this.generation;this.clearRecognition()?.abort()}
}
/** Push-to-talk shares the generation-safe recognition lifecycle. */
export class PushToTalkProvider {
 private provider=new ContinuousRecognitionProvider()
 get available(){return this.provider.available}
 setLocale(locale:'zh-CN'|'en'){this.provider.setLocale(locale)}
 start(onText:(text:string)=>void,onError:(text:string)=>void,onEnd:()=>void){this.provider.startCycle({onText,onError,onEnd})}
 stop(){this.provider.stop()}
 abort(){this.provider.abort()}
}
