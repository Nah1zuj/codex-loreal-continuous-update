import {useState} from 'react'
import type {Health,Session,Step} from '../types'
import {useTrace} from '../content/Locale'
import {ModuleHeader} from '../components/ModuleHeader'

interface Props {
 session:Session|null;step:Step|null;health:Health|null;busy:boolean
 consent:(yes:boolean)=>Promise<void>
 check:(status:string,task:string)=>Promise<void>
 stop:()=>void;send:(text:string)=>void;developerTools?:boolean
}

export function CameraCheck({session,step,health,busy,consent,check,stop,send,developerTools=false}:Props){
 const {c,t}=useTrace()
 const [status,setStatus]=useState('BOTH')
 const demoEnabled=health?.developer_mode&&health.providers.vision==='mock'
 const task=step?.visual_task??'blush_presence'
 const statuses=task==='blush_presence'?['NO_BLUSH','LEFT_ONLY','RIGHT_ONLY','BOTH','UNCERTAIN']:['NOT_APPLIED','APPLIED','OBVIOUS_OVERFLOW','UNCERTAIN']
 const selectedStatus=statuses.includes(status)?status:statuses[0]
 const simulated=session?.visual_state?.simulated&&session.stage==='VERIFY'
 return <section>
  <ModuleHeader module="echo" explanation={t('在映照进行本地画面检查。','Use Reflect for local visual checks.')}/>
  <p className="notice">{t('人脸检查仅在本机处理。旧入口提供不使用相机的模拟演示。','Face checks stay on this computer. This older entry provides a simulation without a camera.')}</p>
  <a href="/explore">{t('打开映照 · 本地检查','Open Reflect · Local checks')}</a>
  {session?.stage==='CAMERA_CONSENT'?<div className="consent-box">
   <h2>{demoEnabled?t('体验一次模拟检查？','Try a simulated check?'):t('当前仅支持本地检查。','Local checks are available in Reflect.')}</h2>
   <div className="controls">
    {demoEnabled?<button className="primary" disabled={busy} onClick={()=>void consent(true)}>{t('允许本次模拟','Allow this simulation')}</button>:null}
    <button disabled={busy} onClick={()=>void consent(false)}>{c.declineCamera}</button>
   </div>
  </div>:null}
  {simulated?<article className="echo-result">
   <h2>{t('模拟结果','Simulated result')}</h2>
   <p>{c.simulated}</p>
   <p>{c.observe[session.visual_state?.status as keyof typeof c.observe]??c.insufficient}</p>
  </article>:null}
  <div className="controls">
   {session?.camera_consent?<button disabled={busy} onClick={stop}>{t('关闭演示检查','Stop simulated checks')}</button>:null}
   {session?.stage==='VERIFY'?<button disabled={busy} onClick={()=>send('next')}>{c.continue}</button>:null}
   {demoEnabled&&session&&['LOOK_SELECTED','GUIDE','VERIFY'].includes(session.stage)?
    <button disabled={busy} onClick={()=>send('check this')}>{t('请求模拟检查','Request simulated check')}</button>:null}
  </div>
  {demoEnabled?<div className="demo-box">
   <p>{c.simulateExplain}</p>
   {developerTools?<><label htmlFor="mock-status">{t('开发者 · 模拟状态','Developer · Simulated state')}</label>
    <select id="mock-status" value={selectedStatus} onChange={e=>setStatus(e.target.value)}>{statuses.map(x=><option key={x}>{x}</option>)}</select></>:null}
   <button disabled={busy||!session?.camera_consent} onClick={()=>void check(developerTools?selectedStatus:task==='blush_presence'?'BOTH':'APPLIED',task)}>{c.simulate}</button>
  </div>:null}
 </section>
}
