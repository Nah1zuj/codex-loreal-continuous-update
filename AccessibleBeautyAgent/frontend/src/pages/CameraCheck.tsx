import {BilingualText} from '../components/BilingualText'
import {useEffect,useRef,useState} from 'react'
import type {Health,Session,Step,VisionReply} from '../types'
import {useTrace} from '../content/Locale'
import {ModuleHeader} from '../components/ModuleHeader'
import {openCamera,stopStream,captureThreeFrames} from '../vision/camera'
interface Props {session:Session|null;step:Step|null;health:Health|null;busy:boolean;consent:(yes:boolean)=>Promise<void>;check:(images:string[],demo:boolean,status:string,task:string)=>Promise<void>;stop:()=>void;send:(text:string)=>void;onError:(error:string)=>void;developerTools?:boolean}
export function CameraCheck({session,step,health,busy,consent,check,stop,send,onError,developerTools=false}:Props){
  const {c}=useTrace()
  const video=useRef<HTMLVideoElement>(null)
  const stream=useRef<MediaStream|null>(null)
  const abort=useRef<AbortController|null>(null)
  const opening=useRef(0)
  const [active,setActive]=useState(false)
  const [captureBusy,setCaptureBusy]=useState(false)
  const [ready,setReady]=useState(false)
  const task=step?.visual_task??'blush_presence'
  const [status,setStatus]=useState('BOTH')
  const statuses=task==='blush_presence'?['NO_BLUSH','LEFT_ONLY','RIGHT_ONLY','BOTH','UNCERTAIN']:['NOT_APPLIED','APPLIED','OBVIOUS_OVERFLOW','UNCERTAIN']
  const selectedStatus=statuses.includes(status)?status:statuses[0]
  function close(){opening.current++;abort.current?.abort();stopStream(stream.current);stream.current=null;setActive(false);setReady(false)}
  useEffect(()=>()=>{opening.current++;abort.current?.abort();stopStream(stream.current)},[])
  useEffect(()=>{if(!session?.camera_consent)close()},[session?.camera_consent])
  async function open(){
    const generation=++opening.current
    try{
      const media=await openCamera()
      if(generation!==opening.current){stopStream(media);return}
      stream.current=media;setActive(true)
      if(video.current){video.current.srcObject=media;await video.current.play()}
    }catch(error){close();onError(error instanceof Error?error.message:'相机开启失败。')}
  }
  async function capture(){
    if(!video.current)return
    setCaptureBusy(true);abort.current=new AbortController()
    try{const images=await captureThreeFrames(video.current,abort.current.signal);stopStream(stream.current);stream.current=null;setActive(false);setReady(false);await check(images,false,selectedStatus,task)}catch(error){onError(error instanceof Error?error.message:'捕获失败')}finally{setCaptureBusy(false);close()}
  }
  const visual=session?.visual_state
  const reliable=!!visual&&visual.status!=='UNCERTAIN'&&visual.confidence>=.8
  return <section><ModuleHeader module="echo" explanation={c.cameraIntro}/><p className="notice">{c.cameraPrivacy} {health?.providers.vision==='mock'?c.simulated:c.remoteImage}</p>{session?.stage==='CAMERA_CONSENT'?<div className="consent-box"><h2><BilingualText text={c.cameraQuestion}/></h2><div className="controls"><button className="primary" disabled={busy} onClick={()=>void consent(true)}><BilingualText text={c.allowCamera}/></button><button disabled={busy} onClick={()=>void consent(false)}><BilingualText text={c.declineCamera}/></button></div></div>:null}{!session?<p className="notice"><BilingualText text={c.selectFirst}/></p>:null}<div className="camera-preview"><video ref={video} playsInline muted aria-label={c.cameraOpen} onLoadedData={()=>setReady(true)} hidden={!active}/><p>{active?c.cameraOpen:c.cameraClosed}</p></div><div className="controls"><button disabled={busy||active||!session?.camera_consent} onClick={()=>void open()}><BilingualText text={c.openCamera}/></button><button className="primary" disabled={busy||captureBusy||!ready||!session?.camera_consent} onClick={()=>void capture()}><BilingualText text={c.capture}/></button><button disabled={!active&&!session?.camera_consent} onClick={()=>{close();stop()}}><BilingualText text={c.stopCamera}/></button>{session?.stage==='VERIFY'?<button disabled={busy} onClick={()=>send('next')}><BilingualText text={c.continue}/></button>:null}{session&&['LOOK_SELECTED','GUIDE','VERIFY'].includes(session.stage)?<button disabled={busy} onClick={()=>send('check this')}><BilingualText text={c.retryCamera}/></button>:null}</div>{visual&&session?.stage==='VERIFY'?<article className="echo-result"><h2><BilingualText text={c.observation}/></h2>{visual.simulated?<p className="notice"><BilingualText text={c.simulated}/></p>:null}<p className="instruction">{reliable?c.observe[visual.status as keyof typeof c.observe]??c.insufficient:c.insufficient}</p>{reliable?<><h2><BilingualText text={c.optionalAction}/></h2><p><BilingualText text={c.optionalNext}/></p></>:null}</article>:null}{health?.developer_mode&&health.providers.vision==='mock'?<div className="demo-box"><p><BilingualText text={c.simulateExplain}/></p>{developerTools?<><label htmlFor="mock-status">Developer · 模拟状态</label><select id="mock-status" value={selectedStatus} onChange={e=>setStatus(e.target.value)}>{statuses.map(x=><option key={x}>{x}</option>)}</select></>:null}<button disabled={busy||!session?.camera_consent} onClick={()=>void check([],true,developerTools?selectedStatus:task==='blush_presence'?'BOTH':'APPLIED',task)}><BilingualText text={c.simulate}/></button></div>:null}</section>
}
