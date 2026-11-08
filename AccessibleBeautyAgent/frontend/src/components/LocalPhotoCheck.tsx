import {useEffect,useRef,useState} from 'react'
import {useTrace} from '../content/Locale'
import {api} from '../api/client'
import {grantLocalPermit,revokeLocalPermit} from '../vision/localConsent'
import {preparePhoto} from '../realtime/photo'
import type {Reply} from '../types'
import {humanError} from '../content/errors'

export function LocalPhotoCheck({sessionId,ensureSession,onResult,beforeCheck}:{sessionId?:string;ensureSession?:()=>Promise<string>;onResult:(reply:Reply)=>void;beforeCheck?:()=>Promise<void>}){
 const {t,locale}=useTrace(),[image,setImage]=useState<string|null>(null),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[hasEvidence,setHasEvidence]=useState(false),[status,setStatus]=useState(''),[target,setTarget]=useState<'blush'|'lips'>('blush')
 const generation=useRef(0),request=useRef<AbortController|null>(null),fileInput=useRef<HTMLInputElement|null>(null)
 const grant=useRef<{sessionId:string;id:string}|null>(null)
 function revoke(){
  const previous=grant.current
  grant.current=null
  if(previous)void revokeLocalPermit(previous.sessionId,previous.id)
 }
 useEffect(()=>()=>{generation.current++;request.current?.abort();revoke()},[])
 const previousSession=useRef(sessionId)
 useEffect(()=>{if(previousSession.current!==undefined&&previousSession.current!==sessionId)clear();previousSession.current=sessionId},[sessionId])
 useEffect(()=>{clear()},[locale])
 function clear(){generation.current++;request.current?.abort();revoke();setBusy(false);setHasEvidence(false);setImage(null);setConsent(false);setStatus('');if(fileInput.current)fileInput.current.value=''}
 useEffect(()=>{
  const hide=()=>{if(document.hidden)clear()}
  document.addEventListener('visibilitychange',hide)
  window.addEventListener('pagehide',clear)
  return()=>{
   document.removeEventListener('visibilitychange',hide)
   window.removeEventListener('pagehide',clear)
  }
 },[])
 async function select(file?:File){clear();if(!file)return;const token=generation.current;setBusy(true);try{const data=await preparePhoto(file);if(token===generation.current){setImage(data);setStatus(t('图片已在浏览器中准备好，尚未发送。请明确同意后检查。','Image prepared in your browser; not sent yet. Allow the local check to continue.'))}}catch(e){if(token===generation.current)setStatus(t('图片无法读取，请选择15MB以内的 JPEG、PNG 或 WebP。','Cannot read this image. Select a JPEG, PNG or WebP smaller than 15 MB.'))}finally{if(token===generation.current)setBusy(false)}}
 async function check(){if(!image||!consent||busy)return;setBusy(true);setStatus(t('正在本地检查这张图片。','Checking this image locally.'));const token=generation.current,abort=new AbortController();request.current=abort
  revoke()
  try{await beforeCheck?.();if(abort.signal.aborted)return;const sid=sessionId??await ensureSession?.();if(!sid)throw new Error(t('检查会话未准备好，请重试。','Analysis session is not ready. Retry.'));if(abort.signal.aborted)return
   // ensureSession may rerender the parent. Consent remains bound to this selected
   // file; request cancellation is handled separately from session creation.
   const permit=await grantLocalPermit(sid,'photo')
   if(token!==generation.current||abort.signal.aborted){void revokeLocalPermit(sid,permit.permit_id);return}
   grant.current={sessionId:sid,id:permit.permit_id}
   const result=await api<Reply>('/vision/local',{session_id:sid,permit_id:permit.permit_id,image,capture_kind:'photo',frame_id:crypto.randomUUID(),captured_at:Date.now()/1000,explicit_consent:true,baseline_consent:false,target,locale},undefined,abort.signal)
   if(token===generation.current&&!abort.signal.aborted){setStatus(result.message);setHasEvidence(true);setImage(null);setConsent(false);if(fileInput.current)fileInput.current.value='';onResult(result)}
  }catch(e){if(token===generation.current&&!abort.signal.aborted){revoke();setConsent(false);setStatus(humanError(e instanceof Error?e.message:String(e),locale))}}finally{if(token===generation.current){setBusy(false);request.current=null}}
 }
 return <section className="local-vision-controls local-photo-controls" aria-label={t('图片 · 本地检查','Photo · Local check')}><h3>{t('也可以检查一张图片','You can also check a photo')}</h3><p>{t('选择正面、光线均匀的面部图片。选择文件不会上传；同意后仅由本应用后端处理，不保存照片。图片可能镜像，不直接判断你本人左右补色。照片检查会暂停自动截帧。','Choose a front-facing photo in even light. Selection does not upload it; after consent, only this app backend processes it without saving it. Unknown photo mirroring prevents advice about your physical sides. Photo checks pause adaptive camera frames.')}</p><label>{t('选择图片（JPEG、PNG、WebP，15MB以内）','Select photo (JPEG, PNG or WebP, up to 15 MB)')}<input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={e=>void select(e.target.files?.[0])}/></label><label>{t('检查区域','Region to inspect')}<select value={target} disabled={busy} onChange={e=>{setTarget(e.target.value as 'blush'|'lips');setConsent(false)}}><option value="blush">{t('面颊颜色与画面质量','Cheek colors and image quality')}</option><option value="lips">{t('唇部颜色与画面质量','Lip colors and image quality')}</option></select></label><label><input type="checkbox" checked={consent} disabled={!image||busy} onChange={e=>setConsent(e.target.checked)}/>{t('同意仅对这张图片做本地检查','Allow a local check of this selected photo only')}</label><button disabled={!image||!consent||busy} onClick={()=>void check()}>{busy?t('处理中…','Processing…'):t('检查这张图片','Check this photo')}</button><button disabled={!image&&!busy&&!hasEvidence} onClick={clear}>{t('清除图片 / 取消','Clear photo / Cancel')}</button><p role="status" aria-live="polite">{status}</p></section>
}
