// @vitest-environment jsdom
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach,expect,it,vi} from 'vitest'
import {api} from '../api/client'
import {LocaleProvider} from '../content/Locale'
import {Pair} from './Pair'

vi.mock('../api/client',()=>({api:vi.fn()}))

afterEach(()=>{vi.restoreAllMocks();vi.clearAllMocks()})

it('keeps manufacturer evidence, unknown fields, and personal preference separate',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true)
  vi.mocked(api).mockImplementation(async(path:string)=>{
    if(path==='/products/catalog')return {results:[
      {product_id:'maybelline_matte_ink',brand:'Maybelline New York',name:'Super Stay Matte Ink Liquid Lipstick'},
      {product_id:'maybelline_vinyl_ink',brand:'Maybelline New York',name:'Super Stay Vinyl Ink Longwear Liquid Lipcolor'},
    ]} as never
    if(path==='/products/compare')return {results:[
      {product_id:'maybelline_matte_ink',evidence_kind:'source',attributes:{name:'Super Stay Matte Ink Liquid Lipstick',brand:'Maybelline New York',category:'lip',finish:'matte',saturation:null,undertone:null},review_status:'DRAFT',sources:[{source_id:'matte',title:'Matte Ink official source',url:'https://www.maybelline.com/matte',accessed_at:'2026-11-12'}]},
      {product_id:'maybelline_vinyl_ink',evidence_kind:'source',attributes:{name:'Super Stay Vinyl Ink Longwear Liquid Lipcolor',brand:'Maybelline New York',category:'lip',finish:'glossy',saturation:null,undertone:null},review_status:'DRAFT',sources:[{source_id:'vinyl',title:'Vinyl Ink official source',url:'https://www.maybelline.com/vinyl',accessed_at:'2026-11-12'}]},
    ]} as never
    throw new Error('unexpected request')
  })
  const host=document.createElement('div')
  document.body.append(host)
  const root=createRoot(host)
  try{
    await act(async()=>root.render(<LocaleProvider initialLocale="en"><Pair session={null} start={vi.fn()} onError={vi.fn()}/></LocaleProvider>))
    await act(async()=>{})
    const button=[...host.querySelectorAll('button')].find(node=>node.textContent==='Compare these two options')!
    expect(button.disabled).toBe(false)
    await act(async()=>button.click())
    expect(host.textContent?.match(/Public manufacturer information/g)).toHaveLength(2)
    expect(host.textContent?.match(/Team review pending/g)).toHaveLength(2)
    expect(host.textContent?.match(/Unknown/g)?.length).toBeGreaterThanOrEqual(4)
    expect(host.textContent).not.toContain('Your personal preference')
    expect(host.querySelectorAll('a[href^="https://www.maybelline.com/"]')).toHaveLength(2)

    const preference=host.querySelectorAll('select')[2]
    await act(async()=>{
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value')!.set!.call(preference,'matte')
      preference.dispatchEvent(new Event('change',{bubbles:true}))
    })
    expect(host.textContent).toContain('Your personal preference · Matte')
  }finally{
    await act(async()=>root.unmount())
    host.remove()
    vi.unstubAllGlobals()
  }
})
