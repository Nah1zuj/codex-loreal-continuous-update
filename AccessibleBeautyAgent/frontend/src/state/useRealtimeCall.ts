import {useEffect,useRef,useState} from 'react'
import {RealtimeCallController,type CallSnapshot} from '../realtime/callController'
import {LocalRecognitionProvider} from '../realtime/localVoice'
import {BrowserTTSProvider} from '../realtime/voice'

type Turn=(text:string,onDelta?:(part:string)=>void,signal?:AbortSignal)=>Promise<string>

export function useRealtimeCall(locale:'zh-CN'|'en',bounded:boolean,send:Turn,onReady:()=>void){
  const [snapshot,setSnapshot]=useState<CallSnapshot>({state:'idle',transcript:'',reply:'',error:''})
  const current=useRef<RealtimeCallController|null>(null)
  const unsubscribe=useRef<(()=>void)|null>(null)
  const lastReply=useRef('')
  const manualInputRequested=useRef(false)
  const handlers=useRef({send,onReady})
  handlers.current={send,onReady}

  function controller(){
    if(!current.current||current.current.state==='ended'){
      unsubscribe.current?.()
      const call=new RealtimeCallController(new LocalRecognitionProvider(),new BrowserTTSProvider(),
        (text,delta,signal)=>handlers.current.send(text,delta,signal))
      call.setLocale(locale)
      call.onReady=()=>handlers.current.onReady()
      current.current=call
      unsubscribe.current=call.subscribe(value=>{
        if(value.reply)lastReply.current=value.reply
        setSnapshot(value)
      })
    }
    current.current.setBounded(bounded)
    return current.current
  }

  useEffect(()=>{
    controller()
    return ()=>{
      unsubscribe.current?.()
      current.current?.end()
      current.current=null
      unsubscribe.current=null
    }
  },[])
  useEffect(()=>{current.current?.setLocale(locale)},[locale])
  useEffect(()=>{current.current?.setBounded(bounded)},[bounded])

  function start(){
    manualInputRequested.current=false
    controller().start()
  }
  function beginCapture(){
    manualInputRequested.current=true
    const call=controller()
    call.setBounded(true)
    call.beginCapture()
  }

  return {current,snapshot,lastReply,manualInputRequested,start,beginCapture,
    submit:(text:string)=>controller().submit(text),
    submitText:(text:string)=>controller().submit(text,{speakReply:false})}
}
