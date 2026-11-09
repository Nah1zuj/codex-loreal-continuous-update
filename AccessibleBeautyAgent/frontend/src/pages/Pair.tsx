import {useEffect, useMemo, useState} from 'react'
import {api} from '../api/client'
import {BilingualText} from '../components/BilingualText'
import {ModuleHeader} from '../components/ModuleHeader'
import {useTrace} from '../content/Locale'
import {readableDescription} from '../content/traceBrand'
import type {Session} from '../types'

interface CatalogueItem {product_id:string; name:string; category:string}
interface EvidenceSource {source_id:string; title:string; url:string; accessed_at:string|null}
interface Comparison {
  product_id:string
  evidence_kind:'source'|'demo'|'unavailable'
  attributes:Partial<Record<'name'|'category'|'finish'|'saturation'|'undertone',string|null>>
  sources:EvidenceSource[]
  review_status:string|null
}

export function Pair({session,start,onError}:{session:Session|null;start:()=>void;onError:(text:string)=>void}){
  const {c,locale,t,d}=useTrace()
  const [catalogue,setCatalogue]=useState<CatalogueItem[]>([])
  const [first,setFirst]=useState('')
  const [second,setSecond]=useState('')
  const [result,setResult]=useState<Comparison[]>([])
  const [preference,setPreference]=useState('')
  const [busy,setBusy]=useState(false)

  useEffect(()=>{
    const controller=new AbortController()
    api<{results:CatalogueItem[]}>('/products/catalog',undefined,'GET',controller.signal)
      .then(response=>setCatalogue(response.results??[]))
      .catch(error=>{if(!controller.signal.aborted)onError(error.message)})
    return ()=>controller.abort()
  },[])

  const products=useMemo(()=>{
    const options=new Map<string,string>()
    for(const row of catalogue)options.set(row.product_id,row.name||row.category)
    for(const [index,row] of (session?.selected_products??[]).entries()){
      if(!options.has(row.product_id))options.set(row.product_id,
        (index+1)+' · '+readableDescription(row.description.split('。')[0],locale))
    }
    return [...options]
  },[catalogue,session?.selected_products,locale])
  const productKey=products.map(([id])=>id).join(' ')
  useEffect(()=>{
    const [one='',two='']=productKey.split(' ')
    setFirst(one)
    setSecond(two)
    setResult([])
  },[productKey])

  async function compare(){
    setBusy(true)
    setResult([])
    try{
      const response=await api<{results:Comparison[]}>('/products/compare',[first,second])
      setResult(response.results)
    }catch(error){onError(error instanceof Error?error.message:c.requestError)}
    finally{setBusy(false)}
  }

  const labels={category:t('类别','Category'),finish:t('妆效','Finish'),
    saturation:t('饱和度','Saturation'),undertone:t('底调','Undertone')}
  const values:Record<string,string>={skincare:t('护肤','Skincare'),base:t('底妆','Base makeup'),
    eye:t('眼妆','Eye makeup'),brow:t('眉部单品','Brow product'),blush:t('腮红','Blush'),
    lip:t('唇部彩妆','Lip colour'),hair:t('头发护理','Hair care'),fragrance:t('香氛','Fragrance'),
    accessories:t('配饰','Accessories'),matte:t('哑光','Matte'),glossy:t('亮泽','Glossy')}
  return <section>
    <ModuleHeader module="pair" explanation={c.pairIntro}/>
    <p><BilingualText text={c.pairDisclaimer}/></p>
    {products.length>=2?<><div className="pair-selectors">
      {([[first,setFirst,c.firstOption],[second,setSecond,c.secondOption]] as const).map(([value,set,label])=>
        <label key={label}>{label}<select disabled={busy} value={value} onChange={e=>{set(e.target.value);setResult([])}}>
          {products.map(([id,name])=><option key={id} value={id}>{name}</option>)}
        </select></label>)}
      <label>{t('我偏好的妆效（可选）','My finish preference (optional)')}
        <select value={preference} onChange={e=>setPreference(e.target.value)}>
          <option value="">{t('暂不选择','No preference selected')}</option>
          <option value="matte">{values.matte}</option><option value="glossy">{values.glossy}</option>
        </select>
      </label>
    </div>
    <button className="primary" disabled={busy||!first||!second||first===second} onClick={()=>void compare()}>{busy?c.working:c.compare}</button>
    <p role="status">{result.length?t('比较结果已更新。','Comparison updated.'):''}</p>
    <div className="pair-results">
      {result.map((row,index)=><article key={row.product_id}>
        <h2>{row.attributes.name||(index===0?c.firstOption:c.secondOption)}</h2>
        <p>{row.evidence_kind==='source'?t('厂商公开资料','Public manufacturer information'):
          row.evidence_kind==='demo'?t('虚构演示属性','Fictional demo attributes'):t('缺少可追溯的资料','Traceable information unavailable')}</p>
        {row.evidence_kind!=='unavailable'?<dl>
          {(Object.keys(labels) as Array<keyof typeof labels>).map(key=><div key={key}>
            <dt>{labels[key]}</dt><dd>{row.attributes[key]?(values[row.attributes[key]]??d(row.attributes[key])):t('未知','Unknown')}</dd>
          </div>)}
        </dl>:null}
        {row.evidence_kind==='source'?<><p>{row.review_status==='HUMAN_VERIFIED'?
          t('团队已核验来源','Source reviewed by the team'):t('团队审核待完成','Team review pending')}</p>
          <ul>{row.sources.map(source=><li key={source.source_id}>
            <a href={source.url} target="_blank" rel="noreferrer">{source.title}</a>
            {source.accessed_at?' · '+source.accessed_at:''}
          </li>)}</ul></>:null}
      </article>)}
    </div>
    {result.length&&preference?<p>{t('你的个人偏好','Your personal preference')} · {values[preference]}</p>:null}
    </>:<><p className="notice"><BilingualText text={c.pairEmpty}/></p><button className="primary" onClick={start}><BilingualText text={c.start}/></button></>}
  </section>
}
