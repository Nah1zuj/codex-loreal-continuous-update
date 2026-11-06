import {useRef} from 'react'
import {api} from '../api/client'
import type {Reply,Session} from '../types'

type Controls={open:()=>Promise<void>;close:()=>void;allowLocal:()=>boolean}
type LocalCheck=(target?:'blush'|'lips',signal?:AbortSignal)=>Promise<Reply>

export function useCameraCoordination(
  session:{current:Session|null},
  clearConsent:(sessionId:string)=>void,
  onError:(message:string)=>void,
){
  const controls=useRef<Controls|null>(null)
  const localCheck=useRef<LocalCheck|null>(null)
  const pendingOpen=useRef(false)

  function revoke(){
    pendingOpen.current=false
    const sid=session.current?.session_id
    if(!sid||!session.current?.camera_consent)return
    clearConsent(sid)
    void api('/chat',{session_id:sid,message:'',action:'camera_consent',consent:false}).catch(()=>{})
  }

  function registerControls(next:Controls|null){
    controls.current=next
    if(next&&pendingOpen.current){
      pendingOpen.current=false
      void next.open().catch(error=>onError(String(error)))
    }
  }

  return {controls,localCheck,pendingOpen,revoke,registerControls,
    registerLocalCheck:(check:LocalCheck|null)=>{localCheck.current=check}}
}
