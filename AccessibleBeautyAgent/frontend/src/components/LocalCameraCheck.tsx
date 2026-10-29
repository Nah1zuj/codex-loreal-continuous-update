import {useEffect,useRef,useState,type RefObject} from 'react'
import {api} from '../api/client'
import {captureVideoFrame} from '../realtime/frameAnalysis'
import {useTrace} from '../content/Locale'
import type {Reply} from '../types'
import {LocalFrameOverlay,validNativeBounds,type BoundsObservation} from './LocalFrameOverlay'
export type LocalCheck=(target?:'blush'|'lips',signal?:AbortSignal)=>Promise<Reply>
type Observation=BoundsObservation&{observation_id:string;target:string;status:string;method:string;quality_warnings?:string[];assessment?:{status:string;scope:string};gate?:{gate_pass:boolean};comparison?:{comparable:boolean};captured_at:number}
type LocalReply=Reply&{observation:Observation}
export function LocalCameraCheck({video,live,sessionId,register,registerPermission,onResult,canAutoCheck=true,openCamera,registerStop}:{video:RefObject<HTMLVideoElement|null>;live:boolean;sessionId?:string;register?:(fn:LocalCheck|null)=>void;registerPermission?:(fn:(()=>boolean)|null)=>void;onResult?:(reply:Reply)=>void;canAutoCheck?:boolean;openCamera?:()=>void;registerStop?:(fn:(()=>Promise<void>)|null)=>void}){
 const {t,locale}=useTrace();const [enabled,setEnabled]=useState(false),[status,setStatus]=useState(''),[baseline,setBaseline]=useState(false),[continuous,setContinuous]=useState(false),[phase,setPhase]=useState('off'),[observation,setObservation]=useState<Observation|null>(null)
 const [observedFrame,setObservedFrame]=useState<string|null>(null)
 useEffect(()=>{if(!observedFrame||!observation)return;const timer=setTimeout(()=>setObservedFrame(null),Math.max(0,observation.captured_at*1000+30000-Date.now()));return()=>clearTimeout(timer)},[observedFrame,observation])
 const generation=useRef(0),busy=useRef(false),consent=useRef(false),baselineRef=useRef(false),lastPixels=useRef<Uint8ClampedArray|null>(null),lastAttempt=useRef(0),lastVideoTime=useRef(-1)
 const request=useRef<AbortController|null>(null),publish=useRef(onResult),autoAllowed=useRef(canAutoCheck)
 const ownsObservation=useRef(false)
 publish.current=onResult;autoAllowed.current=canAutoCheck;baselineRef.current=baseline
 function allow(){if(!live||!sessionId)return false;consent.current=true;setEnabled(true);setPhase('ready');setStatus(t('本地检查已授权；最近15分钟的数值临时用于重查，不保存图片。','Local checks allowed; numerical observations stay in RAM up to 15 minutes for rechecks. Images are not saved.'));return true}
 useEffect(()=>{registerPermission?.(allow);return()=>registerPermission?.(null)},[live,sessionId])
 async function check(target?:'blush'|'lips',signal?:AbortSignal,deliver=false,adaptive=false):Promise<Reply>{
  if(!consent.current||!live||!sessionId||!video.current)throw new Error(t('请先开启摄像头并同意本地检查。','Enable camera and allow local checks first.'))
  if(busy.current)throw new Error(t('检查正在进行，请稍后重试。','A check is running. Try again shortly.'))
  const element=video.current
  if(element.currentTime>0&&element.currentTime===lastVideoTime.current)throw new Error(t('视频尚未更新，请等待新画面。','Video has not advanced. Wait for a fresh frame.'))
  const frame=captureVideoFrame(element);if(!frame)throw new Error(t('还没有清晰的新画面，请重试。','A fresh frame is not ready. Try again.'))
  if(adaptive&&lastPixels.current&&Date.now()-lastAttempt.current<12000){let delta=0,count=0;for(let i=0;i<frame.pixels.length;i++)if(i%4!==3){delta+=Math.abs(frame.pixels[i]-lastPixels.current[i]);count++}if(delta/Math.max(1,count)/255<.025)throw new Error('Unchanged keyframe skipped')}
  busy.current=true;ownsObservation.current=true;const token=generation.current;lastVideoTime.current=element.currentTime;lastAttempt.current=Date.now();lastPixels.current=frame.pixels
  setPhase('analyzing');setObservation(null);setObservedFrame(null);setStatus(t('已获取新画面，正在本地定位和测量。','Fresh frame captured. Local geometry and color analysis is running.'))
  const abort=new AbortController();request.current=abort
  try{
   const result=await api<LocalReply>('/vision/local',{session_id:sessionId,image:frame.image,frame_id:crypto.randomUUID(),captured_at:Date.now()/1000,explicit_consent:true,baseline_consent:baselineRef.current,target:target??'auto',locale},undefined,signal?AbortSignal.any([signal,abort.signal]):abort.signal)
   if(token!==generation.current||!consent.current)throw new Error('Local check cancelled')
   baselineRef.current=false;setBaseline(false);setStatus(result.message);setObservation(result.observation)
   setObservedFrame(validNativeBounds(result.observation)?frame.image:null)
   setPhase(result.observation.gate?.gate_pass?result.observation.status==='HEURISTIC_OBSERVATION'?'observed':'uncertain':'quality')
   if(deliver)publish.current?.(result)
   return result
  }catch(error){if(token===generation.current&&!abort.signal.aborted){setPhase('unavailable');setStatus(t('本地检查未完成，请重试或继续文字辅导。','Local analysis did not complete. Retry or continue with text.'))}throw error}
  finally{if(request.current===abort){busy.current=false;request.current=null}}
 }
 function stop():Promise<void>{const clear=ownsObservation.current||consent.current;ownsObservation.current=false;consent.current=false;generation.current++;request.current?.abort();request.current=null;busy.current=false;setEnabled(false);setContinuous(false);setBaseline(false);setObservation(null);setObservedFrame(null);setStatus(t('本地检查已关闭；再次使用需要重新同意。','Local checks are off. Allow them again before use.'));setPhase('off');lastPixels.current=null;lastVideoTime.current=-1;register?.(null);return clear&&sessionId?api('/vision/local/'+encodeURIComponent(sessionId),undefined,'DELETE').then(()=>{}).catch(()=>{}):Promise.resolve()}
 useEffect(()=>{registerStop?.(stop);return()=>registerStop?.(null)},[sessionId])
 useEffect(()=>{if(!live)stop()},[live])
 useEffect(()=>{stop()},[sessionId,locale])
 useEffect(()=>{register?.(enabled?check:null);return()=>register?.(null)},[enabled,live,sessionId])
 useEffect(()=>{if(!enabled||!continuous||!live)return;const timer=setInterval(()=>{if(!document.hidden&&autoAllowed.current&&!busy.current&&consent.current)void check(undefined,undefined,true,true).catch(()=>{})},3000);return()=>clearInterval(timer)},[enabled,continuous,live,sessionId])
 useEffect(()=>()=>{const clear=ownsObservation.current||consent.current;ownsObservation.current=false;consent.current=false;generation.current++;request.current?.abort();if(clear&&sessionId)void api('/vision/local/'+encodeURIComponent(sessionId),undefined,'DELETE').catch(()=>{})},[sessionId])
 return <section className="local-vision-controls" aria-label={t('本地画面观察','Local visual observation')} data-analysis-state={phase}>
  <p>{t('仅由本应用后端处理单帧，不调用第三方视觉模型，不保存照片。临时数值用于新帧比较；颜色差异不等于腮红差异，也不是准确率。','Single frames are processed only by this app backend, without third-party vision services or saved photos. Temporary numbers support fresh-frame comparisons; color differences are not proven blush differences or accuracy.')}</p>
  <h3>{t('摄像头截帧 · 本地检查','Camera frames · Local checks')}</h3>
  <p>{!live?t('第1步：先开启摄像头。浏览器询问权限时，请选择允许；下方授权按钮会在预览就绪后启用。','Enable the camera first. Allow the browser permission prompt; analysis consent becomes available when preview is ready.'):!sessionId?t('正在准备检查会话，请稍候；无需先选妆容或开始语音。','Preparing the analysis session. No look selection or voice call is required.'):!enabled?t('第2步：同意本地单帧检查，然后检查新画面。连续截帧需要另外勾选授权。','Allow local single-frame checks, then check a fresh frame. Adaptive frames require the separate checkbox.'):t('可以检查新画面；勾选自适应关键帧后会自动复查。','Check a fresh frame, or opt into adaptive keyframes for automatic rechecks.')}</p>
  {!live&&openCamera?<button onClick={openCamera}>{t('开启摄像头，准备检查','Enable camera to prepare checks')}</button>:null}
  <button disabled={!live||!sessionId||enabled} onClick={allow}>{t('同意本地单帧检查','Allow local single-frame checks')}</button>
  <button disabled={!enabled||phase==='analyzing'} onClick={()=>void check(undefined,undefined,true).catch(()=>{})}>{t('检查新画面','Check fresh frame')}</button>
  <label><input type="checkbox" disabled={!enabled} checked={continuous} onChange={e=>setContinuous(e.target.checked)}/>{t('授权自适应关键帧：至少3秒间隔，画面有变化才检查；最长12秒复查，不录制','Allow adaptive keyframes: at least 3 seconds apart, analyze changes, recheck after 12 seconds; no recording')}</label>
  <label><input type="checkbox" disabled={!enabled} checked={baseline} onChange={e=>setBaseline(e.target.checked)}/>{t('下一帧作为15分钟临时妆前基线（请在未上妆时选择）','Use next frame as a 15-minute pre-application baseline (select before makeup)')}</label>
  <button disabled={!enabled} onClick={stop}>{t('关闭本地检查','Stop local checks')}</button>
  <p role="status" aria-live="polite">{status}</p>
  {observedFrame&&observation?<LocalFrameOverlay image={observedFrame} observation={observation} capturedAt={observation.captured_at}/>:null}
  {observation?<>{Number.isFinite(observation.captured_at)?<p>{t('仅对应这一帧：','For this frame only: ')}{new Date(observation.captured_at*1000).toLocaleTimeString(locale)} · {t('当前画面需要重新检查。','Capture again to assess the current view.')}</p>:null}<p>{t('观察目标：','Observation target: ')}{observation.target==='lips'?t('唇部','Lips'):t('腮红区域','Cheeks')} · {observation.assessment?.status==='uncertain'?t('不确定，不作妆效结论','Uncertain; no makeup conclusion'):t('未校准颜色观察','Uncalibrated color observation')}</p><details><summary>{t('技术详情与限制','Technical details and limits')}</summary><pre>{JSON.stringify(observation,null,2)}</pre></details></>:null}
 </section>
}
