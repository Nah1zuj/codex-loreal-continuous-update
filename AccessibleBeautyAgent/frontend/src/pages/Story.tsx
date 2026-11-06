import {SectionBackground} from '../visual/SectionBackground'
import {BilingualHeading} from '../visual/BilingualHeading'
import {useEffect,useRef,useState,type FormEvent} from 'react'
import gsap from 'gsap'
import {useTrace,bilingual} from '../content/Locale'
import {traceBrand,modules,type ModuleKey} from '../content/traceBrand'
import {TraceDotGrid} from '../components/TraceDotGrid'
import {AppleMark} from '../components/AppleMark'
import type {CallSnapshot} from '../realtime/callController'

interface Props {start:()=>void;navigate:(key:string)=>void;motion?:boolean;snapshot?:CallSnapshot;startVoice?:()=>void;pauseVoice?:()=>void;endVoice?:()=>void;submitVoice?:(text:string)=>void;audioReactive?:boolean;setAudioReactive?:(value:boolean)=>void}
export function Story({start,navigate,motion=true,snapshot,startVoice,pauseVoice,endVoice,submitVoice,audioReactive=false,setAudioReactive}:Props){
 const {locale,c,t}=useTrace(),scope=useRef<HTMLElement>(null),[text,setText]=useState('')
 useEffect(()=>{
  const media=gsap.matchMedia();media.add('(prefers-reduced-motion: no-preference)',()=>{
   if(!motion||!scope.current)return
   const context=gsap.context(()=>gsap.from('.story-title-line',{y:16,opacity:.72,letterSpacing:'.035em',stagger:.10,duration:1.1,ease:'power3.out'}),scope)
   return()=>context.revert()
  });return()=>media.revert()
 },[locale,motion])
 useEffect(()=>{
  if(!motion||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||!scope.current||typeof IntersectionObserver==='undefined')return
  const tweens:gsap.core.Tween[]=[]
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){tweens.push(gsap.from(entry.target,{y:12,duration:.8,ease:'power2.out'}));observer.unobserve(entry.target)}}),{threshold:.15})
  scope.current.querySelectorAll('[data-story-reveal]').forEach(node=>observer.observe(node))
  return()=>{observer.disconnect();tweens.forEach(tween=>tween.revert())}
 },[locale,motion])
 function submit(event:FormEvent){event.preventDefault();if(text.trim()){submitVoice?.(text.trim());setText('')}}
 const active=!!snapshot&&!['idle','ended','error','paused'].includes(snapshot.state)
 return <article ref={scope} className="trace-story story-editorial" lang={locale}>
  <section className="story-hero" data-story-depth="0"><SectionBackground showPortrait={false} variant="hero" enabled={motion} state={snapshot?.state} audioReactive={audioReactive} onAudioError={()=>setAudioReactive?.(false)}/>
   <BilingualHeading zh={"美的信息，\n可以改变形式。"} en="Beauty can take another form."/>
   <p className="story-opening">{t('声音、语言与记忆。让美，从你自己的感受开始。','Through voice, language and memory. Begin with how you feel.')}</p>
   <button className="story-enter" onClick={start}>{c.start}<span aria-hidden="true">↗</span></button>
   {snapshot?<details className="story-voice"><summary>{t('听见此刻 · 在这里聊一聊','Hear this moment · Talk here')}</summary>
    <p>{t('开始后允许麦克风才会聆听。浏览器识别可能由其供应商处理；这里不录音。也可以直接写下来。','Listening starts after you allow the microphone. Browser recognition may use its provider; we do not record audio. You can also write instead.')}</p>
    <div className="story-voice-actions"><button disabled={active} onClick={startVoice}>{t('开始语音','Start voice')}</button><button disabled={!active} onClick={pauseVoice}>{t('暂停','Pause')}</button><button onClick={endVoice}>{t('结束','End')}</button></div>
    <label className="story-energy"><input type="checkbox" checked={audioReactive} onChange={event=>setAudioReactive?.(event.target.checked)}/>{t('聆听时本地测量音量，不录制或上传声音。朗读动效仅表示状态。','Measure listening volume locally, without recording or uploading audio. Playback motion indicates state only.')}</label>
    <form onSubmit={submit}><label htmlFor="story-message">{t('把此刻写下来','Write this moment')}</label><div className="story-input"><input id="story-message" value={text} onChange={event=>setText(event.target.value)} maxLength={2000}/><button disabled={!text.trim()}>{t('发送','Send')}</button></div></form>
    {snapshot.error?<p role="alert">{t('语音暂时不可用，可以用文字继续。','Voice is unavailable. Continue with text.')}</p>:null}
    {snapshot.transcript?<p className="story-transcript">{snapshot.transcript}</p>:null}
    {snapshot.reply?<p className="story-reply" aria-live="polite">{snapshot.reply}</p>:null}
   </details>:null}
  </section>
  <section className="story-chapter" data-story-depth="1" data-story-reveal><span aria-hidden="true" className="story-number">01</span><SectionBackground showPortrait={false} variant="wireframe" enabled={motion}/><div className="story-chapter-copy"><BilingualHeading zh="美，从感知开始。" en="Beauty begins with perception." level={2}/><p>{c.storyVisualBody}</p></div></section>
  <section className="story-chapter story-chapter-offset" data-story-depth="2" data-story-reveal><span aria-hidden="true" className="story-number">02</span><SectionBackground showPortrait={false} variant="sculpture" enabled={motion}/><div className="story-chapter-copy"><BilingualHeading zh="听见属于你的表达。" en="An expression of your own." level={2}/><p>{c.storyTranslationBody}</p></div><TraceDotGrid activeDots={[1,3,5]} size="large"/></section>
  <section className="story-signature" data-story-depth="3" data-story-reveal><AppleMark/><div><h2>TRACE</h2><p className="story-line">{bilingual('听见你的美',traceBrand.tagline,locale)}</p><p>{t('由你决定，用自己的方式开始。','Choose your own way to begin.')}</p></div></section>
  <section className="story-modules" aria-label={t('可以怎样开始','Ways to begin')} data-story-depth="4" data-story-reveal>{(['dot','pair','thread','echo','imprint'] as ModuleKey[]).map(key=><button key={key} aria-label={modules[key].accessible[locale]} onClick={()=>navigate(key)}><strong>{modules[key].label[locale]}</strong><span>{modules[key].description[locale]}</span><span className="story-module-arrow" aria-hidden="true">↗</span></button>)}</section>
  <section className="story-agency" data-story-depth="5" data-story-reveal><BilingualHeading zh="今天的你。" en="Today’s Full Look." level={2}/><SectionBackground showPortrait={false} variant="full-look" enabled={motion}/><p>{c.storyAgencyBody}</p><p className="story-channel">{t('我们改变信息的渠道，尊重每一个人。',c.storyChannel)}</p></section>
  <section className="story-ending" data-story-depth="6"><p className="closing-line">{t('美不应始于看见，而应始于你。',traceBrand.closing)}</p><button className="primary" onClick={start}>{c.start}</button><p className="muted research-note">{c.storyResearch}</p></section>
 </article>
}
