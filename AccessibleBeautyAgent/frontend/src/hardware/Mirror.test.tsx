// @vitest-environment jsdom
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {it,expect,vi} from 'vitest'
import {Mirror} from '../pages/Hardware'
import {LocaleProvider} from '../content/Locale'
import {hardwareRequest} from './gateway'
vi.mock('./gateway',()=>({hardwareRequest:vi.fn()}))
;(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true
it('pairs only on submission, shows canonical data, and disconnects on unmount',async()=>{
 vi.mocked(hardwareRequest).mockImplementation(async(path)=>path==='/pair'?{token:'temporary',device:{}}:path==='/display'?{workflow:'PAUSED',step:{title:'Fixture step',instruction:'Wait until ready',review_status:'draft'},progress:{completed:1,total:3}}:{} as any)
 const host=document.createElement('div');document.body.append(host);const root=createRoot(host)
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><Mirror/></LocaleProvider>))
 expect(hardwareRequest).not.toHaveBeenCalled()
 const input=host.querySelector('input')!
 await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,'test-code');input.dispatchEvent(new Event('input',{bubbles:true}))})
 await act(async()=>host.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
 expect(host.textContent).toContain('Fixture step')
 expect(host.textContent).toContain('PAUSED')
 expect(localStorage.getItem('temporary')).toBeNull()
 await act(async()=>root.unmount());host.remove()
 expect(vi.mocked(hardwareRequest).mock.calls.some(([path,body,token])=>path==='/disconnect'&&token==='temporary')).toBe(true)
})
