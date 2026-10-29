// @vitest-environment jsdom
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {it,expect,vi} from 'vitest'
import {SaveLookRecord} from './SaveLookRecord'
import {LocaleProvider} from '../content/Locale'
import {api} from '../api/client'
vi.mock('../api/client',()=>({api:vi.fn(async()=>({id:'saved'}))}))
;(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true
it('requires review and explicit consent, and saves only a bounded text snapshot',async()=>{
 const host=document.createElement('div');document.body.append(host);const root=createRoot(host)
 const session={session_id:'test',user_id:'owner',todays_look:{version:1,sections:{makeup:{state:'proposed',suggestions:[{display_name_zh:'自然',display_name_en:'Natural'}]}}}} as any
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><SaveLookRecord session={session} onError={()=>{}}/></LocaleProvider>))
 expect(api).not.toHaveBeenCalled()
 await act(async()=>host.querySelector('button')!.click())
 expect(host.querySelector('textarea')!.value).toContain('Proposed, not yet confirmed')
 const submit=host.querySelector('button.primary') as HTMLButtonElement
 expect(submit.disabled).toBe(true)
 await act(async()=>host.querySelector<HTMLInputElement>('input[type=checkbox]')!.click())
 expect(submit.disabled).toBe(false)
 await act(async()=>submit.click())
 expect(api).toHaveBeenCalledTimes(1)
 expect(vi.mocked(api).mock.calls[0]).toMatchObject(['/journal',{session_id:'test',user_id:'owner',explicit_consent:true,save_transcript:false}])
 expect(host.textContent).toContain('Photos and full chat were not saved')
 await act(async()=>root.unmount());host.remove()
})
