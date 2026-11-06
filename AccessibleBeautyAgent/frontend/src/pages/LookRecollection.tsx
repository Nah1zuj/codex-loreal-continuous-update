import {useEffect,useState} from 'react'
import {api} from '../api/client'
import {useSpeech} from '../accessibility/useSpeech'
import {useTrace} from '../content/Locale'
import type {LookSummary,RecollectionView} from '../realtime/recollection'

interface Candidate {
  candidate_id:string
  version:string
  summary:LookSummary
}
interface Edits {name:string;note:string}
interface Props {
  sessionId?:string
  onChange:(view:RecollectionView)=>void
  onError:(message:string)=>void
}

export function LookRecollection({sessionId,onChange,onError}:Props){
  const {t}=useTrace(),speech=useSpeech()
  const [view,setView]=useState<RecollectionView|null>(null)
  const [candidate,setCandidate]=useState<Candidate|null>(null)
  const [edits,setEdits]=useState<Edits>({name:'',note:''})
  const [reviewed,setReviewed]=useState(false)
  const [pending,setPending]=useState(false)
  const [deleteId,setDeleteId]=useState('')
  const [status,setStatus]=useState('')

  function apply(value:RecollectionView){setView(value);onChange(value)}
  function review(value:Candidate){
    setCandidate(value)
    setEdits({name:value.summary.name,note:value.summary.note??''})
    setReviewed(false)
  }
  useEffect(()=>{
    let active=true
    const abort=new AbortController()
    api<RecollectionView>('/recollection',undefined,undefined,abort.signal).then(value=>{
      if(active)apply(value)
    }).catch(error=>{if(active)onError(String(error))})
    setCandidate(null)
    if(sessionId){
      api<Candidate>('/recollection/candidate/'+encodeURIComponent(sessionId),undefined,undefined,abort.signal)
        .then(value=>{if(active&&value?.candidate_id)review(value)})
        .catch(error=>{if(active&&(error as {status?:number}).status!==404)onError(String(error))})
    }
    return ()=>{active=false;abort.abort()}
  },[sessionId])
  async function refresh(){apply(await api<RecollectionView>('/recollection'))}
  async function perform(action:()=>Promise<void>){
    if(pending)return
    setPending(true)
    setStatus('')
    try{await action()}catch(error){onError(error instanceof Error?error.message:String(error))}
    finally{setPending(false)}
  }
  const unchanged=candidate!==null&&edits.name.trim()===candidate.summary.name&&edits.note.trim()===(candidate.summary.note??'')
  const candidatePath=(id:string)=>'/recollection/candidates/'+encodeURIComponent(id)
  function read(item:LookSummary){
    const completed=item.completed_steps.length?item.completed_steps.join('、'):t('没有确认完成的步骤。','No steps were confirmed complete.')
    if(!speech.speak([item.name,item.date,completed,item.note].filter(Boolean).join('. '))){
      setStatus(t('设备朗读不可用。摘要仍可用文字和读屏阅读。','Speech is unavailable. The summary remains available as text.'))
    }
  }
  async function decide(save:boolean){
    if(!candidate||!unchanged||save&&!reviewed)return
    await api(candidatePath(candidate.candidate_id)+(save?'/confirm':'/reject'),{
      version:candidate.version,edits,explicit_consent:save,
    })
    setCandidate(null)
    setReviewed(false)
    await refresh()
    setStatus(save?t('摘要已单独保存。','Summary saved separately.'):t('已拒绝这份摘要。','Summary declined.'))
  }
  return <section className="look-recollection" aria-labelledby="recollection-title">
    <h1 id="recollection-title">{t('拾光 · 我们的上次相遇','Trace · Our last visit')}</h1>
    <p>{t('摘要、私人日志和偏好分别由你确认。摘要最多保留 30 天。','Review summaries, private journal entries, and preferences separately. Summaries are kept for up to 30 days.')}</p>
    {candidate&&<section aria-labelledby="summary-review-title">
      <h2 id="summary-review-title">{t('待审阅摘要','Summary to review')}</h2>
      <p>{candidate.summary.date} · {candidate.summary.completed_steps.length
        ?candidate.summary.completed_steps.join('、'):t('没有确认完成的步骤。','No steps were confirmed complete.')}</p>
      <label>{t('摘要标题','Summary title')}<input maxLength={100} value={edits.name} onChange={e=>{
        setEdits(value=>({...value,name:e.target.value}));setReviewed(false)
      }}/></label>
      <label>{t('私人备注（可选）','Private note (optional)')}<textarea maxLength={1200} value={edits.note} onChange={e=>{
        setEdits(value=>({...value,note:e.target.value}));setReviewed(false)
      }}/></label>
      {!unchanged&&<button disabled={pending||!edits.name.trim()} onClick={()=>void perform(async()=>{
        review(await api<Candidate>(candidatePath(candidate.candidate_id)+'/preview',edits))
        setStatus(t('新版摘要已准备好，请重新确认。','Updated summary ready for review.'))
      })}>{t('预览修改后的版本','Preview edited version')}</button>}
      <div className="controls">
        <button disabled={!unchanged} onClick={()=>read(candidate.summary)}>{t('朗读摘要','Read summary aloud')}</button>
        <button onClick={speech.stop}>{t('停止朗读','Stop reading')}</button>
      </div>
      <label><input type="checkbox" checked={reviewed} disabled={!unchanged||pending}
        onChange={e=>setReviewed(e.target.checked)}/>{t('我已审阅并同意保存这个版本。','I reviewed and agree to save this version.')}</label>
      <div className="controls">
        <button className="primary" disabled={pending||!reviewed||!unchanged} onClick={()=>void perform(()=>decide(true))}>
          {t('保存此摘要','Save this summary')}</button>
        <button disabled={pending} onClick={()=>void perform(async()=>{
          if(!unchanged){
            await api(candidatePath(candidate.candidate_id)+'/reject',{version:candidate.version,
              edits:{name:candidate.summary.name,note:candidate.summary.note??''}})
            setCandidate(null);setStatus(t('已拒绝这份摘要。','Summary declined.'))
            return
          }
          await decide(false)
        })}>{t('不保存这份摘要','Decline this summary')}</button>
      </div>
    </section>}
    {view?.entries.length?<ol>{view.entries.map(item=>{
      const id=item.id??item.session_id
      const legacy=item.origin==='legacy_automatic'
      return <li key={id}>
        <h2>{item.name}</h2>
        <p>{item.date} · {legacy?t('旧版自动摘要','Earlier automatic summary'):t('已确认摘要','Confirmed summary')}</p>
        {item.completed_steps.length>0&&<p>{item.completed_steps.join('、')}</p>}
        {item.note&&<p>{item.note}</p>}
        <div className="controls">
          <button onClick={()=>read(item)}>{t('朗读这份记录','Read this record aloud')}</button>
          {legacy?<button disabled={pending} onClick={()=>void perform(async()=>review(
            await api<Candidate>(candidatePath(id)+'/preview',{}),
          ))}>{t('重新审阅旧摘要','Review earlier summary')}</button>
          :<button disabled={pending} aria-pressed={item.reusable??false} onClick={()=>void perform(async()=>{
            apply(await api<RecollectionView>('/recollection/'+encodeURIComponent(id)+'/reuse',{explicit_consent:true}))
            setStatus(t('已选用这份记录的风格。','This record’s style has been selected.'))
          })}>{t('下次沿用这个风格','Reuse this style next time')}</button>}
          {deleteId!==id?<button disabled={pending} onClick={()=>setDeleteId(id)}>{t('删除摘要','Delete summary')}</button>
          :<><button disabled={pending} onClick={()=>void perform(async()=>{
            apply(await api<RecollectionView>('/recollection/'+encodeURIComponent(id),{explicit_consent:true},'DELETE'))
            setDeleteId('');setStatus(t('已删除摘要。','Summary deleted.'))
          })}>{t('确认删除摘要','Confirm summary deletion')}</button>
          <button onClick={()=>setDeleteId('')}>{t('取消删除','Cancel deletion')}</button></>}
        </div>
      </li>
    })}</ol>:<p>{t('暂无已存摘要。','No stored summaries.')}</p>}
    <p role="status" aria-live="polite">{status}</p>
  </section>
}
