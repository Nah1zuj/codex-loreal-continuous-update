import {useEffect,useRef,useState,type RefObject} from 'react'
import {api} from '../api/client'
import {grantLocalPermit,revokeLocalBaseline,revokeLocalPermit} from '../vision/localConsent'
import {captureVideoFrame} from '../realtime/frameAnalysis'
import {useTrace} from '../content/Locale'
import type {Reply} from '../types'
import {LocalFrameOverlay,validNativeBounds,type BoundsObservation} from './LocalFrameOverlay'
export type LocalCheck=(target?:'blush'|'lips',signal?:AbortSignal)=>Promise<Reply>
type Observation=BoundsObservation&{observation_id:string;target:string;status:string;method:string;quality_warnings?:string[];assessment?:{status:string;scope:string};gate?:{gate_pass:boolean};comparison?:{comparable:boolean};captured_at:number}
type LocalReply=Reply&{observation:Observation&{baseline_saved?:boolean}}
type CameraScope='camera'|'adaptive'
type Grant={sessionId:string;id?:string;expiresAt?:number;baselineVersion?:number}
type Capture={abort:AbortController;scope:CameraScope;usesBaseline:boolean}
export function LocalCameraCheck({video,live,sessionId,register,registerPermission,onResult,canAutoCheck=true,openCamera,registerStop}:{video:RefObject<HTMLVideoElement|null>;live:boolean;sessionId?:string;register?:(fn:LocalCheck|null)=>void;registerPermission?:(fn:(()=>boolean)|null)=>void;onResult?:(reply:Reply)=>void;canAutoCheck?:boolean;openCamera?:()=>void;registerStop?:(fn:(()=>Promise<void>)|null)=>void}){
 const {t,locale}=useTrace()
 const [enabled,setEnabled]=useState(false),[authorizing,setAuthorizing]=useState(false)
 const [continuous,setContinuous]=useState(false),[adaptivePending,setAdaptivePending]=useState(false)
 const [baseline,setBaseline]=useState(false),[baselineAvailable,setBaselineAvailable]=useState(false),[baselinePending,setBaselinePending]=useState(false)
 const [status,setStatus]=useState(''),[phase,setPhase]=useState('off')
 const [observation,setObservation]=useState<Observation|null>(null),[observedFrame,setObservedFrame]=useState<string|null>(null)
 const grants=useRef<Partial<Record<CameraScope,Grant>>>({})
 const request=useRef<Capture|null>(null),baselineRef=useRef(false),baselineActive=useRef(false),baselineClearing=useRef(false)
 const lastPixels=useRef<Uint8ClampedArray|null>(null),lastAttempt=useRef(0),lastVideoTime=useRef(-1)
 const publish=useRef(onResult),autoAllowed=useRef(canAutoCheck)
 const observationScope=useRef<CameraScope|null>(null)
 publish.current=onResult
 autoAllowed.current=canAutoCheck

 useEffect(()=>{
  if(!observation)return
  const timer=setTimeout(clearObservation,Math.max(0,observation.captured_at*1000+30000-Date.now()))
  return()=>clearTimeout(timer)
 },[observation])

 function clearObservation(){
  observationScope.current=null
  setObservation(null)
  setObservedFrame(null)
 }
 function acquire(scope:CameraScope,sid:string){
  const grant:Grant={sessionId:sid}
  grants.current[scope]=grant
  if(scope==='camera')setAuthorizing(true)
  else setAdaptivePending(true)
  void grantLocalPermit(sid,scope).then(permit=>{
   if(grants.current[scope]!==grant){
    void revokeLocalPermit(sid,permit.permit_id)
    return
   }
   grant.id=permit.permit_id
   grant.expiresAt=permit.expires_at
   grant.baselineVersion=permit.baseline_version
   if(scope==='camera'){
    setEnabled(true)
    setPhase('ready')
    setStatus(t('本地单帧检查已授权。只有明确选择的基线数值可用于前后比较。','Single-frame checks are allowed. Only a baseline you explicitly choose can be used for before/after comparison.'))
   }else setContinuous(true)
  }).catch(()=>{
   if(grants.current[scope]!==grant)return
   delete grants.current[scope]
   setStatus(t('本地授权未建立，请重试。','Local consent could not be established. Please try again.'))
  }).finally(()=>{
   if(grants.current[scope]&&grants.current[scope]!==grant)return
   if(scope==='camera')setAuthorizing(false)
   else setAdaptivePending(false)
  })
 }
 function allow(){
  if(!live||!sessionId)return false
  if(!grants.current.camera)acquire('camera',sessionId)
  return true
 }
 function release(scope:CameraScope){
  const grant=grants.current[scope]
  delete grants.current[scope]
  if(request.current?.scope===scope){
   request.current.abort.abort()
   request.current=null
  }
  return grant?.id?revokeLocalPermit(grant.sessionId,grant.id):Promise.resolve()
 }
 function resetPermits(){
  const released=[release('camera'),release('adaptive')]
  baselineRef.current=false
  baselineActive.current=false
  baselineClearing.current=false
  lastPixels.current=null
  lastVideoTime.current=-1
  return Promise.all(released).then(()=>{})
 }
 function stop(){
  const released=resetPermits()
  setEnabled(false)
  setAuthorizing(false)
  setContinuous(false)
  setAdaptivePending(false)
  setBaseline(false)
  setBaselineAvailable(false)
  setBaselinePending(false)
  clearObservation()
  setStatus(t('本地检查已关闭；再次使用需要重新同意。','Local checks are off. Allow them again before use.'))
  setPhase('off')
  register?.(null)
  return released
 }
 function setAdaptive(next:boolean){
  if(next&&sessionId){
   acquire('adaptive',sessionId)
  }else{
   void release('adaptive')
   setContinuous(false)
   setAdaptivePending(false)
   lastPixels.current=null
   if(observationScope.current==='adaptive')clearObservation()
   setPhase('ready')
  }
 }
 async function clearBaseline(){
  const camera=grants.current.camera
  if(!camera?.id||!sessionId)return
  baselineClearing.current=true
  if(request.current?.usesBaseline){
   request.current.abort.abort()
   request.current=null
  }
  baselineRef.current=false
  baselineActive.current=false
  setBaseline(false)
  setBaselineAvailable(false)
  setBaselinePending(false)
  clearObservation()
  setPhase('ready')
  try{
   const result=await revokeLocalBaseline(sessionId,camera.id)
   if(grants.current.camera===camera)camera.baselineVersion=result.baseline_version
  }catch{
   if(grants.current.camera===camera)void stop()
  }finally{
   if(grants.current.camera===camera)baselineClearing.current=false
  }
 }
 async function check(target?:'blush'|'lips',signal?:AbortSignal,deliver=false,adaptive=false):Promise<Reply>{
  const scope:CameraScope=adaptive?'adaptive':'camera'
  const grant=grants.current[scope]
  if(!grant?.id||!live||!sessionId||grant.sessionId!==sessionId||!video.current)throw new Error(t('请先开启摄像头并同意本地检查。','Enable camera and allow local checks first.'))
  if(grant.expiresAt&&grant.expiresAt<=Date.now()/1000){
   void stop()
   throw new Error(t('本地授权已到期，请重新同意。','Local consent expired. Allow checks again.'))
  }
  if(signal?.aborted)throw new Error('Local check cancelled')
  if(request.current||baselineClearing.current)throw new Error(t('检查正在进行，请稍后重试。','A check is running. Try again shortly.'))
  const element=video.current
  if(element.currentTime>0&&element.currentTime===lastVideoTime.current)throw new Error(t('视频尚未更新，请等待新画面。','Video has not advanced. Wait for a fresh frame.'))
  const frame=captureVideoFrame(element)
  if(!frame)throw new Error(t('还没有清晰的新画面，请重试。','A fresh frame is not ready. Try again.'))
  if(adaptive&&lastPixels.current&&Date.now()-lastAttempt.current<12000){
   let delta=0,count=0
   for(let i=0;i<frame.pixels.length;i++)if(i%4!==3){delta+=Math.abs(frame.pixels[i]-lastPixels.current[i]);count++}
   if(delta/Math.max(1,count)/255<.025)throw new Error('Unchanged keyframe skipped')
  }
  lastVideoTime.current=element.currentTime
  lastAttempt.current=Date.now()
  if(adaptive)lastPixels.current=frame.pixels
  const saveBaseline=!adaptive&&baselineRef.current
  const compareBaseline=baselineActive.current&&!saveBaseline
  const capture={abort:new AbortController(),scope,usesBaseline:saveBaseline||compareBaseline}
  request.current=capture
  if(saveBaseline){baselineRef.current=false;setBaseline(false);setBaselinePending(true)}
  setPhase('analyzing')
  clearObservation()
  setStatus(t('已获取新画面，正在本地定位和测量。','Fresh frame captured. Local geometry and color analysis is running.'))
  const abort=capture.abort
  try{
   const result=await api<LocalReply>('/vision/local',{
    session_id:sessionId,permit_id:grant.id,image:frame.image,frame_id:crypto.randomUUID(),captured_at:Date.now()/1000,
    explicit_consent:true,adaptive,baseline_consent:saveBaseline,compare_baseline:compareBaseline,
    baseline_version:grants.current.camera?.baselineVersion,target:target??'auto',locale,
   },undefined,signal?AbortSignal.any([signal,abort.signal]):abort.signal)
   if(request.current!==capture||grants.current[scope]!==grant||abort.signal.aborted||signal?.aborted)throw new Error('Local check cancelled')
   if(result.observation.baseline_saved){baselineActive.current=true;setBaselineAvailable(true)}
   setStatus(result.message)
   setObservation(result.observation)
   observationScope.current=scope
   setObservedFrame(validNativeBounds(result.observation)?frame.image:null)
   setPhase(result.observation.gate?.gate_pass?result.observation.status==='HEURISTIC_OBSERVATION'?'observed':'uncertain':'quality')
   if(deliver)publish.current?.(result)
   return result
  }catch(error){
   if(request.current===capture&&!abort.signal.aborted){
    if((error as {status?:number}).status===403)void stop()
    else{
     setPhase('unavailable')
     setStatus(t('本地检查未完成，请重试或继续文字辅导。','Local analysis did not complete. Retry or continue with text.'))
    }
   }
   throw error
  }finally{
   if(request.current===capture){request.current=null;if(saveBaseline)setBaselinePending(false)}
  }
 }
 useEffect(()=>{registerPermission?.(allow);return()=>registerPermission?.(null)},[live,sessionId])
 useEffect(()=>{registerStop?.(stop);return()=>registerStop?.(null)},[sessionId,locale])
 useEffect(()=>{if(!live)void stop()},[live])
 useEffect(()=>{
  void stop()
  return()=>{void resetPermits()}
 },[sessionId,locale])
 useEffect(()=>{
  const expiresAt=grants.current.camera?.expiresAt
  if(!enabled||!expiresAt)return
  const timer=setTimeout(()=>{void stop()},Math.max(0,expiresAt*1000-Date.now()))
  return()=>clearTimeout(timer)
 },[enabled,sessionId,locale])
 useEffect(()=>{register?.(enabled?check:null);return()=>register?.(null)},[enabled,live,sessionId,locale])
 useEffect(()=>{
  if(!enabled||!continuous||!live)return
  const timer=setInterval(()=>{
   if(!document.hidden&&autoAllowed.current&&!request.current)void check(undefined,undefined,true,true).catch(()=>{})
  },3000)
  return()=>clearInterval(timer)
 },[enabled,continuous,live,sessionId,locale])
 return <section className="local-vision-controls" aria-label={t('本地画面观察','Local visual observation')} data-analysis-state={phase}>
  <p>{t('仅由本应用后端处理单帧，不调用第三方视觉模型，不保存照片。前后比较需要你明确选定临时基线。颜色数值无法确定妆效。','Single frames are processed only by this app backend, without third-party vision services or saved photos. Before/after comparison requires a baseline you choose. Color values do not establish makeup results.')}</p>
  <h3>{t('摄像头截帧 · 本地检查','Camera frames · Local checks')}</h3>
  <p>{!live?t('第1步：先开启摄像头。浏览器询问权限时，请选择允许；下方授权按钮会在预览就绪后启用。','Enable the camera first. Allow the browser permission prompt; analysis consent becomes available when preview is ready.'):!sessionId?t('正在准备检查会话，请稍候；无需先选妆容或开始语音。','Preparing the analysis session. No look selection or voice call is required.'):!enabled?t('第2步：同意本地单帧检查，然后检查新画面。连续截帧需要另外勾选授权。','Allow local single-frame checks, then check a fresh frame. Adaptive frames require the separate checkbox.'):t('可以检查新画面；勾选自适应关键帧后会自动复查。','Check a fresh frame, or opt into adaptive keyframes for automatic rechecks.')}</p>
  {!live&&openCamera?<button onClick={openCamera}>{t('开启摄像头，准备检查','Enable camera to prepare checks')}</button>:null}
  <button disabled={!live||!sessionId||enabled||authorizing} onClick={allow}>{t('同意本地单帧检查','Allow local single-frame checks')}</button>
  <button disabled={!enabled||phase==='analyzing'} onClick={()=>void check(undefined,undefined,true).catch(()=>{})}>{t('检查新画面','Check fresh frame')}</button>
  <label><input type="checkbox" disabled={!enabled||adaptivePending} checked={continuous} onChange={e=>setAdaptive(e.target.checked)}/>{t('授权自适应关键帧：至少3秒间隔，画面有变化才检查；最长12秒复查，不录制','Allow adaptive keyframes: at least 3 seconds apart, analyze changes, recheck after 12 seconds; no recording')}</label>
  <label><input type="checkbox" disabled={!enabled} checked={baseline} onChange={e=>{baselineRef.current=e.target.checked;setBaseline(e.target.checked)}}/>{t('下一次手动检查作为15分钟临时基线','Use the next manual check as a 15-minute baseline')}</label>
  <button disabled={!baseline&&!baselineAvailable&&!baselinePending} onClick={()=>void clearBaseline()}>{t('清除比较基线','Clear comparison baseline')}</button>
  <button disabled={!enabled&&!authorizing} onClick={stop}>{t('关闭本地检查','Stop local checks')}</button>
  <p role="status" aria-live="polite">{status}</p>
  {observedFrame&&observation?<LocalFrameOverlay image={observedFrame} observation={observation} capturedAt={observation.captured_at}/>:null}
  {observation?<>{Number.isFinite(observation.captured_at)?<p>{t('仅对应这一帧：','For this frame only: ')}{new Date(observation.captured_at*1000).toLocaleTimeString(locale)} · {t('当前画面需要重新检查。','Capture again to assess the current view.')}</p>:null}<p>{t('观察目标：','Observation target: ')}{observation.target==='lips'?t('唇部','Lips'):t('腮红区域','Cheeks')} · {observation.assessment?.status==='uncertain'?t('不确定，不作妆效结论','Uncertain; no makeup conclusion'):t('未校准颜色观察','Uncalibrated color observation')}</p><details><summary>{t('技术详情与限制','Technical details and limits')}</summary><pre>{JSON.stringify(observation,null,2)}</pre></details></>:null}
 </section>
}
