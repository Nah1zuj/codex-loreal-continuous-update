import {LocalPhotoCheck} from '../components/LocalPhotoCheck'
import {MakeupDigitalTwin} from '../visual/BeautyVisuals'
import {BilingualHeading} from '../visual/BilingualHeading'
import {humanError} from '../content/errors'
import {useTrace} from '../content/Locale'
import {useEffect,useRef,useState} from 'react'
import {VoiceCall,type VoiceCallProps} from './VoiceCall'
import {CameraStreamController} from '../realtime/cameraStream'
import {LocalCameraCheck,type LocalCheck} from '../components/LocalCameraCheck'
import type {Reply} from '../types'
export interface VideoCallProps extends VoiceCallProps {cameraOnly?:boolean;ensureSession?:()=>Promise<string>;region?:string;previewRegion?:(region:string)=>void;revoke:()=>void;apply:(reply:Reply)=>void;registerLocalCheck?:(fn:LocalCheck|null)=>void;registerCameraControls?:(controls:{open:()=>Promise<void>;close:()=>void;allowLocal:()=>boolean}|null)=>void}
export function VideoCall(props:VideoCallProps){const {t,locale}=useTrace();const video=useRef<HTMLVideoElement>(null);const camera=useRef(new CameraStreamController());const [facing,setFacing]=useState<'user'|'environment'>('user');const [state,setState]=useState('off');const [error,setError]=useState('');const generation=useRef(0)
function revokeChecks(){void stopLocal.current?.();props.revoke()}
function stop(){generation.current++;camera.current.stop();revokeChecks();setState('off');setError('')}
const allowLocal=useRef<(()=>boolean)|null>(null),stopLocal=useRef<(()=>Promise<void>)|null>(null)
useEffect(()=>{
 const controller=camera.current
 controller.onUnexpectedEnd=()=>{
  generation.current++
  revokeChecks()
  setState(controller.state)
  setError(controller.error||'')
 }
 return()=>{controller.onUnexpectedEnd=undefined}
},[props.revoke])
useEffect(()=>{props.registerCameraControls?.({open:preview,close:stop,allowLocal:()=>allowLocal.current?.()??false});return()=>props.registerCameraControls?.(null)},[props.session?.session_id,state])
useEffect(()=>{const hidden=()=>{if(document.hidden)stop()};document.addEventListener('visibilitychange',hidden);window.addEventListener('pagehide',stop);return()=>{document.removeEventListener('visibilitychange',hidden);window.removeEventListener('pagehide',stop);generation.current++;camera.current.stop();props.revoke()}},[])
const previousCallState=useRef(props.snapshot.state);useEffect(()=>{if(previousCallState.current!==props.snapshot.state&&(props.snapshot.state==='ended'||props.snapshot.state==='paused'))stop();previousCallState.current=props.snapshot.state},[props.snapshot.state])
async function preview(){stop();setFacing('user');const token=++generation.current;setError('');setState('requesting');try{if(!props.session?.session_id&&props.ensureSession)await props.ensureSession();if(token!==generation.current)return;if(video.current){const result=await camera.current.requestPreview(video.current);if(token===generation.current){setState(result);setError(camera.current.error||'')}}}catch(e){if(token===generation.current){setState('error');setError(e instanceof Error?e.message:String(e))}}}
async function switchCamera(){
 const token=++generation.current
 revokeChecks();setState('requesting');setError('')
 const result=await camera.current.switchFacingMode()
 if(token!==generation.current)return
 setState(result);setError(camera.current.error||'')
 if(result==='live')setFacing(current=>current==='user'?'environment':'user')
}
return <section className={props.cameraOnly?"video-call contextual-camera":"video-call"}><BilingualHeading zh={props.cameraOnly?"当前会话 · 摄像头观察":"实时上妆指导"} en={props.cameraOnly?"Current session · Camera observation":"Real-time Makeup Guidance"} level={props.cameraOnly?2:1}/><p className="twin-disclosure">{t("通用数字示意，不是你的面部扫描。区域显示步骤位置，实际判断以文字反馈为准。","Generic digital illustration, not a scan of your face. Regions locate steps; actual observations are shown in text.")}</p><div className="makeup-workspace"><div className="makeup-observation"><div className="region-preview"><p>{t('查看数字示意区域，不改变当前辅导进度。','Preview a region without changing your coaching progress.')}</p><div className="controls">{[['base','底妆','Base'],['blush','腮红','Blush'],['eyes','眼妆','Eyes'],['lips','唇妆','Lips'],['finish','定妆','Finish']].map(([key,zh,en])=><button key={key} aria-pressed={props.region===key} onClick={()=>props.previewRegion?.(key)}>{t(zh,en)}</button>)}</div></div><div className="video-stage" data-camera-state={state}>{!props.cameraOnly&&state!=='live'?<div className="makeup-art"><div className="face-region-labels" aria-hidden="true"><span className="region-eye">{t("眼妆区域","Eyeshadow area")}</span><span className="region-cheek">{t("腮红区域","Blush area")}</span><span className="region-lip">{t("唇部区域","Lip area")}</span></div><MakeupDigitalTwin step={props.step} session={props.session} enabled={props.motion??true} state={props.snapshot.state} regionOverride={props.region}/><p className="art-disclosure">{t("通用区域示意 · 非实时面部追踪","Generic region illustration · Not live face tracking")}</p></div>:null}<video ref={video} className={facing==='user'?'local-mirror':undefined} style={{transform:facing==='user'?'scaleX(-1)':'none'}} muted playsInline aria-label={t("本地摄像头预览","Local camera preview")}/><p role="status">{t("摄像头：","Camera: ")}{t(({off:"关闭",live:"已开启",error:"不可用",unavailable:"不可用",requesting:"请求中"} as Record<string,string>)[state]||"不可用",state)}</p><p>{t("预览不会自动分析。人脸检查仅在本机处理。","Preview has no automatic analysis. Face checks stay on this computer.")}</p><div className="controls"><button disabled={state==='requesting'} onClick={()=>void preview()}>{t("开启摄像头","Enable camera")}</button><button onClick={()=>void switchCamera()} disabled={state!=='live'}>{t("切换摄像头","Switch camera")}</button><button onClick={stop}>{t("关闭摄像头","Close camera")}</button></div>{error?<p role="alert">{state==='denied'?t('摄像头权限被拒绝。请在浏览器的站点权限中允许摄像头，然后点击开启摄像头重试；也可以直接选择下方的图片检查。','Camera permission was denied. Allow camera access in browser site permissions, then retry Enable camera; or use the photo check below.'):state==='unavailable'?t('摄像头已断开或不可用。请检查连接和权限，再重新开启摄像头并允许本地检查。','The camera is disconnected or unavailable. Check the connection and permissions, then enable the camera and allow local checks again.'):humanError(error,locale)}</p>:null}</div></div>{!props.cameraOnly?<VoiceCall {...props} compact headingLevel={2} end={()=>{stop();props.end()}} pause={()=>{stop();props.pause()}}/>:null}</div><LocalCameraCheck registerStop={fn=>{stopLocal.current=fn}} openCamera={()=>void preview()} video={video} live={state==='live'} sessionId={props.session?.session_id} register={props.registerLocalCheck} onResult={props.apply} canAutoCheck={!['thinking','speaking','requesting_permission','quiet_wake','paused','ended','error'].includes(props.snapshot.state)} registerPermission={fn=>{allowLocal.current=fn}}/><LocalPhotoCheck beforeCheck={async()=>{await stopLocal.current?.()}} sessionId={props.session?.session_id} ensureSession={props.ensureSession} onResult={props.apply}/></section>}
