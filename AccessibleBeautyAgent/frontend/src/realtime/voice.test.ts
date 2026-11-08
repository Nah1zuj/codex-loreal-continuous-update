import {describe,it,expect,vi,afterEach} from 'vitest'
import {BrowserTTSProvider,ContinuousRecognitionProvider} from './voice'
afterEach(()=>vi.unstubAllGlobals())
describe('speech lifecycle',()=>{
 it('ignores completion from cancelled speech and keeps pause/resume visible',()=>{
  const utterances:any[]=[]
  const synthesis={cancel:vi.fn(),pause:vi.fn(),resume:vi.fn(),speak:(u:any)=>utterances.push(u)}
  vi.stubGlobal('window',{speechSynthesis:synthesis})
  vi.stubGlobal('SpeechSynthesisUtterance',class {constructor(public text:string){}})
  const tts=new BrowserTTSProvider()
  tts.speak('first');utterances[0].onstart();expect(tts.state).toBe('speaking')
  const lateEnd=utterances[0].onend
  tts.speak('second');utterances[1].onstart();lateEnd();expect(tts.state).toBe('speaking')
  tts.pause();expect(tts.state).toBe('paused');tts.resume();expect(tts.state).toBe('speaking')
  const lateError=utterances[1].onerror
  tts.stop();lateError();expect(tts.state).toBe('idle')
 })
 it('returns a text fallback when browser speech is unavailable',()=>{vi.stubGlobal('window',{});const tts=new BrowserTTSProvider();expect(tts.speak('text')).toBe(false);expect(tts.state).toBe('error')})
 it('emits a final transcript once and ignores late events after abort',()=>{
  const instances:any[]=[]
  class Recognition {lang='';continuous=true;interimResults=true;onresult:any;onerror:any;onend:any;start=vi.fn();stop=vi.fn();abort=vi.fn();constructor(){instances.push(this)}}
  vi.stubGlobal('window',{SpeechRecognition:Recognition})
  const provider=new ContinuousRecognitionProvider(),texts:string[]=[]
  provider.startCycle({onText:text=>texts.push(text),onError:vi.fn(),onEnd:vi.fn()})
  instances[0].onresult({results:[{isFinal:true,0:{transcript:'你好'}}]})
  instances[0].onresult({results:[{isFinal:true,0:{transcript:'重复'}}]})
  provider.abort();instances[0].onend?.()
  expect(texts).toEqual(['你好']);expect(instances[0].abort).toHaveBeenCalled()
 })
 it('maps recognition errors and reports unavailable browsers',()=>{
  vi.stubGlobal('window',{});expect(new ContinuousRecognitionProvider().available).toBe(false)
  const instances:any[]=[];class Recognition {onresult:any;onerror:any;onend:any;start(){}stop(){}abort(){}constructor(){instances.push(this)}}
  vi.stubGlobal('window',{webkitSpeechRecognition:Recognition});const errors:string[]=[]
  new ContinuousRecognitionProvider().startCycle({onText:vi.fn(),onError:e=>errors.push(e),onEnd:vi.fn()});instances[0].onerror({error:'not-allowed'})
  expect(errors[0]).toContain('not-allowed')
 })
 it('calls TTS completion only for the current utterance',()=>{
  const utterances:any[]=[];vi.stubGlobal('window',{speechSynthesis:{cancel:vi.fn(),pause:vi.fn(),resume:vi.fn(),speak:(u:any)=>utterances.push(u)}})
  vi.stubGlobal('SpeechSynthesisUtterance',class {onstart:any;onend:any;onerror:any;constructor(public text:string){}})
  const done=vi.fn(),tts=new BrowserTTSProvider();tts.speak('one',false,done);tts.speak('two',false,done)
  utterances[0].onend?.();utterances[1].onend();expect(done).toHaveBeenCalledTimes(1)
 })
 it('detaches cancelled recognition handlers and ignores captured callbacks',()=>{
  let instance:any
  class Recognition {onresult:any;onerror:any;onend:any;start(){}stop(){}abort(){}constructor(){instance=this}}
  vi.stubGlobal('window',{SpeechRecognition:Recognition})
  const provider=new ContinuousRecognitionProvider(),onText=vi.fn(),onError=vi.fn(),onEnd=vi.fn()
  provider.startCycle({onText,onError,onEnd})
  const {onresult,onerror,onend}=instance
  provider.abort()
  onresult({results:[{isFinal:true,0:{transcript:'late'}}]});onerror({error:'late'});onend()
  expect(onText).not.toHaveBeenCalled();expect(onError).not.toHaveBeenCalled();expect(onEnd).not.toHaveBeenCalled()
  expect(instance.onresult).toBeNull();expect(instance.onerror).toBeNull();expect(instance.onend).toBeNull()
 })
 it('closes recognition on natural end before notifying its caller',()=>{
  let instance:any
  class Recognition {onresult:any;onerror:any;onend:any;start(){}stop(){}abort(){}constructor(){instance=this}}
  vi.stubGlobal('window',{SpeechRecognition:Recognition})
  const provider=new ContinuousRecognitionProvider(),onText=vi.fn(),onError=vi.fn()
  const onEnd=vi.fn(()=>{expect(instance.onresult).toBeNull();expect(instance.onerror).toBeNull();expect(instance.onend).toBeNull()})
  provider.startCycle({onText,onError,onEnd})
  const {onresult,onerror,onend}=instance
  onend()
  onresult({results:[{isFinal:true,0:{transcript:'late'}}]});onerror({error:'late'});onend()
  expect(onText).not.toHaveBeenCalled();expect(onError).not.toHaveBeenCalled();expect(onEnd).toHaveBeenCalledTimes(1)
 })
 it('detaches cancelled speech handlers',()=>{
  let utterance:any
  vi.stubGlobal('window',{speechSynthesis:{cancel:vi.fn(),speak:(u:any)=>utterance=u}})
  vi.stubGlobal('SpeechSynthesisUtterance',class {})
  const provider=new BrowserTTSProvider();provider.speak('hello');provider.stop()
  expect(utterance.onstart).toBeNull();expect(utterance.onend).toBeNull();expect(utterance.onerror).toBeNull()
 })
 it('reports recognition start failures without retaining active handlers',()=>{
  let instance:any
  class Recognition {onresult:any;onerror:any;onend:any;start(){throw new Error('start failed')}stop(){}abort(){}constructor(){instance=this}}
  vi.stubGlobal('window',{SpeechRecognition:Recognition})
  const onError=vi.fn()
  expect(()=>new ContinuousRecognitionProvider().startCycle({onText:vi.fn(),onError,onEnd:vi.fn()})).not.toThrow()
  expect(onError).toHaveBeenCalled();expect(instance.onresult).toBeNull()
 })
 it('returns a fallback if the utterance API is missing',()=>{
  vi.stubGlobal('window',{speechSynthesis:{cancel:vi.fn(),speak:vi.fn()}})
  vi.stubGlobal('SpeechSynthesisUtterance',undefined)
  const provider=new BrowserTTSProvider()
  expect(provider.speak('hello')).toBe(false);expect(provider.state).toBe('error')
 })
})

it('uses the selected speech locale and stops old speech when changed',()=>{const utterances:any[]=[];const cancel=vi.fn();vi.stubGlobal('window',{speechSynthesis:{cancel,speak:(u:any)=>utterances.push(u)}});vi.stubGlobal('SpeechSynthesisUtterance',class {constructor(public text:string){}});const tts=new BrowserTTSProvider();tts.setLocale('en');tts.speak('Next');expect(utterances[0].lang).toBe('en-US');const count=cancel.mock.calls.length;tts.setLocale('zh-CN');expect(cancel.mock.calls.length).toBeGreaterThan(count)})

it('sets recognition language and ignores callbacks from the previous locale',()=>{const instances:any[]=[];class Recognition {lang='';onresult:any;onerror:any;onend:any;start(){}stop(){}abort=vi.fn();constructor(){instances.push(this)}}vi.stubGlobal('window',{SpeechRecognition:Recognition});const voice=new ContinuousRecognitionProvider(),text=vi.fn();voice.setLocale('en');voice.startCycle({onText:text,onError:vi.fn(),onEnd:vi.fn()});expect(instances[0].lang).toBe('en-US');const late=instances[0].onresult;voice.setLocale('zh-CN');late({results:[{isFinal:true,0:{transcript:'old'}}]});expect(text).not.toHaveBeenCalled();expect(instances[0].abort).toHaveBeenCalled();voice.startCycle({onText:text,onError:vi.fn(),onEnd:vi.fn()});expect(instances[1].lang).toBe('zh-CN')})
