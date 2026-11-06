import {useEffect,useRef,useState} from 'react'
import {BilingualText} from '../components/BilingualText'
import {api} from '../api/client'
import {openCamera,stopStream,captureStillFrame} from '../vision/camera'
import {useSpeech} from '../accessibility/useSpeech'
import {useTrace} from '../content/Locale'
import {ModuleHeader} from '../components/ModuleHeader'
import {TraceDotGrid} from '../components/TraceDotGrid'
import type {Health} from '../types'

interface Availability {
  provider:'mock'|'qwen'|'deepseek'
  service_name:string
  destination_host?:string|null
  status:'demo'|'disabled'|'configured'|'missing_configuration'
}
interface ReadingReply {
  label_kind:'product'|'garment'
  composition:string|null
  uncertain_characters:string[]
  status:'READ'|'UNCERTAIN'
  summary:string
  shade:string|null
  instructions:string|null
  full_text:string|null
  simulated:boolean
  service:string
}
type ResultField='summary'|'shade'|'composition'|'instructions'|'full_text'

export function Reading({health,onError}:{health:Health|null;onError:(text:string)=>void}){
  const {c,t,d,locale}=useTrace()
  const [availability,setAvailability]=useState<Availability|null>(null)
  const [labelKind,setLabelKind]=useState<'product'|'garment'>('product')
  const [active,setActive]=useState(false)
  const [opening,setOpening]=useState(false)
  const [ready,setReady]=useState(false)
  const [busy,setBusy]=useState(false)
  const [result,setResult]=useState<ReadingReply|null>(null)
  const [selected,setSelected]=useState<ResultField>('summary')
  const [notice,setNotice]=useState<''|'readEnded'|'declineRead'>('')
  const video=useRef<HTMLVideoElement>(null)
  const stream=useRef<MediaStream|null>(null)
  const generation=useRef(0)
  const pending=useRef<AbortController|null>(null)
  const tts=useSpeech()
  const remote=availability?.status==='configured'&&availability.provider!=='mock'
  const demoAvailable=availability?.status==='demo'||(!availability&&health?.reading_provider==='mock'&&health.developer_mode)

  function releaseStream(){
    stopStream(stream.current)
    stream.current=null
    if(video.current)video.current.srcObject=null
  }

  function close(){
    generation.current++
    pending.current?.abort()
    pending.current=null
    releaseStream()
    setActive(false)
    setOpening(false)
    setReady(false)
    setBusy(false)
  }

  useEffect(()=>{
    const controller=new AbortController()
    api<Availability>('/reading/availability',undefined,'GET',controller.signal)
      .then(service=>{if(!controller.signal.aborted)setAvailability(service)})
      .catch(error=>{if(!controller.signal.aborted)onError(error instanceof Error?error.message:c.requestError)})
    const hide=()=>{if(document.hidden)close()}
    window.addEventListener('pagehide',close)
    document.addEventListener('visibilitychange',hide)
    return ()=>{
      controller.abort()
      generation.current++
      pending.current?.abort()
      releaseStream()
      window.removeEventListener('pagehide',close)
      document.removeEventListener('visibilitychange',hide)
    }
  },[])

  async function open(){
    const id=++generation.current
    setOpening(true)
    setNotice('')
    try{
      const media=await openCamera('environment')
      if(id!==generation.current){stopStream(media);return}
      stream.current=media
      setActive(true)
      if(video.current){video.current.srcObject=media;await video.current.play()}
    }catch(error){
      if(id===generation.current){close();onError(error instanceof Error?error.message:c.requestError)}
    }finally{if(id===generation.current)setOpening(false)}
  }

  async function read(demo:boolean){
    if(pending.current)return
    const provider=availability?.provider
    if(!demo&&(!remote||!ready||provider==='mock'))return
    if(demo&&!demoAvailable)return
    const id=++generation.current
    const controller=new AbortController()
    pending.current=controller
    setBusy(true)
    setResult(null)
    try{
      const image=demo?undefined:captureStillFrame(video.current!)
      releaseStream()
      setActive(false)
      setReady(false)
      const response=await api<ReadingReply>('/reading/read',{
        image,demo,explicit_consent:true,remote_upload_consent:!demo,
        authorized_provider:demo?undefined:provider,label_kind:labelKind,locale,
      },undefined,controller.signal)
      if(id===generation.current){setResult(response);setSelected('summary');setNotice('readEnded')}
    }catch(error){if(id===generation.current)onError(error instanceof Error?error.message:c.requestError)}
    finally{
      if(id===generation.current){
        setBusy(false)
        setActive(false)
        setReady(false)
        pending.current=null
        releaseStream()
      }
    }
  }

  const fieldText=(field:ResultField)=>{
    const value=result?.[field]
    if(!value)return c.readUnknown
    return field==='summary'?d(value):value
  }
  return <section>
    <ModuleHeader module="dot" explanation={c.readIntro}/>
    <label>{t('标签类型','Label type')}
      <select disabled={busy||active||opening} value={labelKind} onChange={event=>setLabelKind(event.target.value as 'product'|'garment')}>
        <option value="product">{t('产品标签','Product label')}</option>
        <option value="garment">{t('衣物成分与洗护吊牌','Garment composition & care label')}</option>
      </select>
    </label>
    <p>{t('只读取标签文字。照片外观无法证明成分。','The reader transcribes label text. Appearance cannot establish composition.')}</p>
    {remote?<p className="notice">
      {t('打开相机只作本地预览。只有点击允许并发送，才会向以下服务发送一张标签图供文字读取。请让画面只包含标签。',
         'Opening the camera previews locally. Choosing Allow and send sends one label image to the service below for text reading. Frame only the label.')}
      {' '}{availability.service_name}{availability.destination_host?' · '+availability.destination_host:''}
    </p>:<p className="notice">{availability?
      t('真实标签读取服务当前未启用或未配置。','Real label reading is disabled or unconfigured.'):
      t('正在检查标签读取服务。','Checking the label reading service.')}</p>}
    <div className="camera-preview reading-preview">
      <video ref={video} hidden={!active} playsInline muted aria-label={c.readReady}
        onLoadedData={()=>{if(stream.current)setReady(true)}}/>
      {active?<TraceDotGrid activeDots={[1,3,5]} size="large"/>:<p>{busy?c.readWait:c.cameraClosed}</p>}
    </div>
    <div className="controls">
      {remote?<><button disabled={active||opening||busy} onClick={()=>void open()}>
        {t('打开本地标签预览','Open local label preview')}
      </button><button className="primary" disabled={!ready||busy} onClick={()=>void read(false)}>
        {t('允许并发送一张标签图','Allow and send one label image')}
      </button></>:null}
      <button onClick={()=>{close();setNotice('declineRead')}}>
        {busy?t('关闭并忽略读取结果','Close and ignore reading result'):
          active||opening?t('关闭且不发送','Close without sending'):c.declineRead}
      </button>
      {demoAvailable?<button disabled={busy||active||opening} onClick={()=>void read(true)}>{c.readSample}</button>:null}
    </div>
    <p role="status">{busy?c.readWait:notice?c[notice]:''}</p>
    {result?<article className="reading-result">
      <h2><BilingualText text={c.readSummary}/></h2>
      <p className="notice">{result.simulated?t('虚构演示标签','Fictional demo label'):
        (availability?.service_name??result.service)+' · '+(result.status==='READ'?t('标签转写','Label transcription'):t('部分或无法辨认','Partial or unreadable'))}</p>
      <p>{t('难辨字符','Uncertain characters')} · {result.uncertain_characters.join('、')||t('无报告','None reported')}</p>
      {selected==='full_text'?<pre className="instruction" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{fieldText(selected)}</pre>:
        <p aria-live="polite" className="instruction">{fieldText(selected)}</p>}
      <div className="controls">
        {([
          ['summary',c.readSummary],[result.label_kind==='garment'?'composition':'shade',result.label_kind==='garment'?t('成分','Composition'):c.readShade],
          ['instructions',c.readInstructions],['full_text',c.readAll],
        ] as const).map(([field,label])=><button key={field} aria-pressed={selected===field}
          onClick={()=>{setSelected(field);tts.speak(fieldText(field))}}>{label}</button>)}
        <button onClick={()=>tts.speak(fieldText(selected))}><BilingualText text={c.readAgain}/></button>
        <button onClick={tts.stop}><BilingualText text={c.stopRead}/></button>
      </div>
    </article>:null}
  </section>
}
