import {useRef,useState} from 'react'
import type {Session,Step} from '../types'

const sessionKey='trace.session_id'

export function storedSessionId(){return sessionStorage.getItem(sessionKey)}

/** The server supplies progress. Keep the event-time reference and rendered snapshot in sync. */
export function useSessionSnapshot(){
  const [snapshot,setSnapshot]=useState<{session:Session|null;step:Step|null}>({session:null,step:null})
  const current=useRef<Session|null>(null)

  function accept(session:Session,step:Step|null){
    const previous=current.current
    const oldPlan=previous?.makeup_plan
    const nextPlan=session.makeup_plan
    if(previous?.session_id===session.session_id&&oldPlan&&nextPlan&&oldPlan.id===nextPlan.id&&
       nextPlan.revision<oldPlan.revision)return false
    const publicSession=session.visual_state?.task==='local_region_measurement'
      ? {...session,visual_state:null}
      : session
    current.current=publicSession
    sessionStorage.setItem(sessionKey,session.session_id)
    setSnapshot({session:publicSession,step})
    return true
  }

  function clear(){
    current.current=null
    sessionStorage.removeItem(sessionKey)
    setSnapshot({session:null,step:null})
  }

  function clearCameraConsent(sessionId:string){
    const session=current.current
    if(!session||session.session_id!==sessionId||!session.camera_consent)return
    const revoked={...session,camera_consent:false}
    current.current=revoked
    setSnapshot(previous=>({...previous,session:revoked}))
  }

  return {...snapshot,current,accept,clear,clearCameraConsent}
}
