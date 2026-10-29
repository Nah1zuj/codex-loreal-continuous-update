// @vitest-environment jsdom
// File/media fixtures verify consent and cancellation, not vision accuracy.
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach,it,expect,vi} from 'vitest'
import {LocalPhotoCheck} from './LocalPhotoCheck'
import {LocaleProvider} from '../content/Locale'
import {api} from '../api/client'
import {preparePhoto} from '../realtime/photo'
vi.mock('../api/client',()=>({api:vi.fn()}))
vi.mock('../realtime/photo',()=>({preparePhoto:vi.fn(async()=> 'data:image/jpeg;base64,synthetic')}))
;(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true
let root:ReturnType<typeof createRoot>,host:HTMLDivElement
afterEach(async()=>{await act(async()=>root?.unmount());host?.remove();vi.clearAllMocks()})
async function mount(props:any){host=document.createElement('div');document.body.append(host);root=createRoot(host);await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalPhotoCheck {...props}/></LocaleProvider>))}
async function select(){const input=host.querySelector<HTMLInputElement>('input[type=file]')!;Object.defineProperty(input,'files',{configurable:true,value:[new File(['synthetic'],'photo.png',{type:'image/png'})]});await act(async()=>input.dispatchEvent(new Event('change',{bubbles:true})))}
function checkButton(){return [...host.querySelectorAll('button')].find(b=>b.textContent==='Check this photo')!}
it('prepares locally but sends only after explicit consent, without camera or remote endpoint',async()=>{
 const onResult=vi.fn(),ensureSession=vi.fn(async()=> 'same');vi.mocked(api).mockResolvedValue({message:'Uncertain',session:{session_id:'same'}} as any)
 await mount({ensureSession,onResult});await select();expect(preparePhoto).toHaveBeenCalledOnce();expect(api).not.toHaveBeenCalled();expect(checkButton().disabled).toBe(true)
 await act(async()=>host.querySelector<HTMLInputElement>('input[type=checkbox]')!.click());await act(async()=>checkButton().click())
 expect(ensureSession).toHaveBeenCalledOnce();expect(api).toHaveBeenCalledWith('/vision/local',expect.objectContaining({session_id:'same',capture_kind:'photo',explicit_consent:true,baseline_consent:false}),undefined,expect.any(AbortSignal));expect(onResult).toHaveBeenCalledOnce();expect(host.querySelector<HTMLInputElement>('input[type=checkbox]')!.checked).toBe(false)
})
it('does not abort photo consent when creating the initial shared session, but cancels a changed owner session',async()=>{
 let finish!:(r:any)=>void;const onResult=vi.fn();vi.mocked(api).mockImplementation(async()=>new Promise(resolve=>{finish=resolve}))
 await mount({ensureSession:async()=> 'new',onResult});await select();await act(async()=>host.querySelector<HTMLInputElement>('input[type=checkbox]')!.click());await act(async()=>checkButton().click())
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalPhotoCheck sessionId="new" onResult={onResult}/></LocaleProvider>));await act(async()=>finish({session:{session_id:'new'},message:'New session image reply'}))
 expect(onResult).toHaveBeenCalledOnce()
 await select();await act(async()=>host.querySelector<HTMLInputElement>('input[type=checkbox]')!.click());await act(async()=>checkButton().click());const signal=vi.mocked(api).mock.calls.at(-1)![3]!
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalPhotoCheck sessionId="different" onResult={onResult}/></LocaleProvider>));expect(signal.aborted).toBe(true);await act(async()=>finish({message:'Late forbidden'}));expect(host.textContent).not.toContain('Late forbidden');expect(onResult).toHaveBeenCalledTimes(1)
})
