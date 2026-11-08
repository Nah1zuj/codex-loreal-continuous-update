import {useTrace} from '../content/Locale'
import {useEffect,useRef,useState} from 'react'
import {BrowserTTSProvider} from '../realtime/voice'
export function useSpeech(){
  const {locale}=useTrace()
  const provider=useRef<BrowserTTSProvider|null>(null)
  if(provider.current===null)provider.current=new BrowserTTSProvider()
  const speech=provider.current
  const [,refresh]=useState(0)
  useEffect(()=>{speech.onState=()=>refresh(n=>n+1);return ()=>{speech.onState=null;speech.stop()}},[speech])
  useEffect(()=>{speech.setLocale(locale)},[speech,locale])
  return speech
}
