// @vitest-environment jsdom
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {expect,it,vi} from 'vitest'
import {LocaleProvider} from '../content/Locale'
import {LookRecollection} from './LookRecollection'
import {api} from '../api/client'

vi.mock('../api/client',()=>({api:vi.fn()}))

it('requires preview and explicit consent after editing a candidate',async()=>{
  ;(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true
  const draft={candidate_id:'plan:session',version:'before',summary:{
    name:'Daily look',note:'',date:'2026-11-07',completed_steps:['Prepare'],
  }}
  vi.mocked(api).mockImplementation(async(path,body)=>{
    if(path.endsWith('/preview'))return {...draft,version:'edited',summary:{...draft.summary,...body as object}} as any
    if(path.includes('/candidate/'))return draft as any
    if(path.endsWith('/confirm'))return {saved:true} as any
    return {entries:[],latest:null,enabled:true} as any
  })
  const host=document.createElement('div')
  const root=createRoot(host)
  try{
    await act(async()=>root.render(<LocaleProvider initialLocale="en">
      <LookRecollection sessionId="session" onChange={()=>{}} onError={error=>{throw Error(error)}}/>
    </LocaleProvider>))
    const find=(label:string)=>[...host.querySelectorAll('button')].find(button=>button.textContent?.includes(label))!
    const input=host.querySelector('input')!
    const checkbox=host.querySelector<HTMLInputElement>('input[type=checkbox]')!
    expect(find('Save this summary').disabled).toBe(true)
    await act(async()=>checkbox.click())
    expect(find('Save this summary').disabled).toBe(false)
    await act(async()=>{
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,'Edited private title')
      input.dispatchEvent(new Event('input',{bubbles:true}))
    })
    expect(find('Save this summary').disabled).toBe(true)
    await act(async()=>find('Preview edited version').click())
    expect(find('Save this summary').disabled).toBe(true)
    await act(async()=>checkbox.click())
    await act(async()=>find('Save this summary').click())
    expect(api).toHaveBeenCalledWith('/recollection/candidates/plan%3Asession/confirm',{
      version:'edited',edits:{name:'Edited private title',note:''},explicit_consent:true,
    })
  }finally{await act(async()=>root.unmount())}
})
