import {useEffect,useState} from 'react'
import {api} from '../api/client'
import type {Vocabulary} from './types'
import {KnowledgePage} from './KnowledgePage'
import {ReferencePage} from './ReferencePage'
import {RagPage} from './RagPage'
import './admin.css'
import {TraceMark} from '../components/TraceMark'
export default function AdminApp(){
  const [vocabulary,setVocabulary]=useState<Vocabulary>({});const [message,setMessage]=useState('');const [error,setError]=useState(false)
  const path=window.location.pathname
  function notify(text:string,failed=false){setMessage(text);setError(failed)}
  useEffect(()=>{document.title='TRACE Knowledge · 内部研究工作台';api<Vocabulary>('/admin/vocabulary').then(setVocabulary).catch(e=>notify(e.message,true))},[])
  return <div className="kb-admin"><a className="skip-link" href="#kb-main">跳到主要内容</a><header><a className="brand" href="/admin/knowledge"><TraceMark/><span><small>知识研究工作台</small></span></a><a href="/">返回 TRACE</a></header><div className="kb-shell"><nav aria-label="知识管理导航"><a href="/admin/knowledge" aria-current={path==='/admin/knowledge'?'page':undefined}>知识工作台</a><a href="/admin/references" aria-current={path==='/admin/references'?'page':undefined}>图片审核</a><a href="/admin/rag" aria-current={path==='/admin/rag'?'page':undefined}>检索调试</a><p>本机工具 · 无自动审核<br/>RAW → DRAFT → HUMAN VERIFIED → INDEXED</p></nav><main id="kb-main">{path==='/admin/references'?<ReferencePage vocabulary={vocabulary} onMessage={notify}/>:path==='/admin/rag'?<RagPage onMessage={notify}/>:<KnowledgePage vocabulary={vocabulary} onMessage={notify}/>} {message?<section className={'kb-message '+(error?'error':'notice')} role={error?'alert':'status'} aria-live="polite"><h2>{error?'操作未完成':'操作结果'}</h2><pre>{message}</pre><button onClick={()=>setMessage('')}>收起结果</button></section>:null}</main></div></div>
}
