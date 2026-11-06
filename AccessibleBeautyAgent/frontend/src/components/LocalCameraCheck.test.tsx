// @vitest-environment jsdom
// Synthetic media fixture: verifies wiring/privacy, not physical camera or vision accuracy.
import {act,createRef} from 'react'
import {createRoot,type Root} from 'react-dom/client'
import {afterEach,expect,it,vi} from 'vitest'
import {LocalCameraCheck,type LocalCheck} from './LocalCameraCheck'
import {LocaleProvider} from '../content/Locale'
import {api} from '../api/client'
import {captureVideoFrame} from '../realtime/frameAnalysis'
vi.mock('../api/client',()=>({api:vi.fn()}))
vi.mock('../realtime/frameAnalysis',()=>({captureVideoFrame:vi.fn()}))
;(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true
let host:HTMLDivElement,root:Root,check:LocalCheck|null,allow:(()=>boolean)|null
function permit(scope='camera'){return {permit_id:scope+'-permit',expires_at:Date.now()/1000+900,baseline_version:1}}
const result={message:'Uncertain local observation',session:{session_id:'same'},step:null,observation:{observation_id:'obs',status:'UNCERTAIN',target:'blush',assessment:{status:'uncertain'},gate:{gate_pass:true},captured_at:Date.now()/1000}} as any
async function mount(onResult=vi.fn()){
 host=document.createElement('div');document.body.append(host);root=createRoot(host)
 const video=createRef<HTMLVideoElement>();video.current=document.createElement('video')
 vi.mocked(captureVideoFrame).mockReturnValue({image:'synthetic',pixels:new Uint8ClampedArray(4096)})
 vi.mocked(api).mockImplementation(async(path,body)=>path==='/vision/local/permits'?permit((body as {scope:string}).scope) as any:result)
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalCameraCheck live video={video} sessionId="same" register={value=>{check=value}} registerPermission={value=>{allow=value}} onResult={onResult}/></LocaleProvider>))
 return {video,onResult}
}
function button(label:string){return Array.from(host.querySelectorAll('button')).find(b=>b.textContent===label)!}
it('an inactive camera never deletes a photo observation when an initial session appears',async()=>{
 await mount();const video=createRef<HTMLVideoElement>();vi.mocked(api).mockClear()
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalCameraCheck live={false} video={video}/></LocaleProvider>))
 vi.mocked(api).mockClear()
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalCameraCheck live={false} video={video} sessionId="photo-created"/></LocaleProvider>))
 expect(api).not.toHaveBeenCalled()
})
it('offers an actionable camera setup and explains why frame controls are unavailable',async()=>{
 await mount();const open=vi.fn();const video=createRef<HTMLVideoElement>()
 await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalCameraCheck live={false} video={video} openCamera={open}/></LocaleProvider>))
 expect(host.textContent).toContain('Enable the camera first')
 expect(button('Enable camera to prepare checks').disabled).toBe(false)
 await act(async()=>button('Enable camera to prepare checks').click());expect(open).toHaveBeenCalledOnce()
 expect(button('Allow local single-frame checks').disabled).toBe(true)
})
afterEach(async()=>{if(root)await act(async()=>root.unmount());host?.remove();vi.clearAllMocks();vi.useRealTimers()})
it('consent gates capture and manual result is applied without a success badge',async()=>{const {onResult}=await mount();expect(check).toBeNull();expect(captureVideoFrame).not.toHaveBeenCalled();await act(async()=>button('Allow local single-frame checks').click());await act(async()=>button('Check fresh frame').click());expect(onResult).toHaveBeenCalledWith(result);expect(host.querySelector('[data-analysis-state]')?.getAttribute('data-analysis-state')).toBe('uncertain');expect(host.textContent).toContain('Uncertain; no makeup conclusion')})
it('voice recheck uses a fresh ID with explicit target and does not double-publish',async()=>{const {onResult}=await mount();await act(async()=>{allow?.()});await act(async()=>{await check?.('lips');await check?.('lips')});const calls=vi.mocked(api).mock.calls.filter(([path])=>path==='/vision/local');expect(calls).toHaveLength(2);expect((calls[0][1] as any).frame_id).not.toBe((calls[1][1] as any).frame_id);expect((calls[1][1] as any).target).toBe('lips');expect(onResult).not.toHaveBeenCalled()})
it('unchanged adaptive keyframes are skipped and stop prevents late publishing',async()=>{vi.useFakeTimers();const {onResult}=await mount();await act(async()=>button('Allow local single-frame checks').click());const checkbox=host.querySelector('input[type=checkbox]')!;await act(async()=>{(checkbox as HTMLInputElement).click()});await act(async()=>{await vi.advanceTimersByTimeAsync(3000)});await act(async()=>{await vi.advanceTimersByTimeAsync(3000)});expect(onResult).toHaveBeenCalledTimes(1);await act(async()=>button('Stop local checks').click());await act(async()=>{await vi.advanceTimersByTimeAsync(15000)});expect(onResult).toHaveBeenCalledTimes(1);expect(check).toBeNull()})
it('unmount aborts a pending frame request and never publishes it',async()=>{let finish!:(r:any)=>void;let signal:AbortSignal|undefined;const {onResult}=await mount();vi.mocked(api).mockImplementation(async(path,body,method,abort)=>{if(path==='/vision/local/permits')return permit() as any;if(path==='/vision/local'){signal=abort;return new Promise(resolve=>{finish=resolve})}return {} as any});await act(async()=>button('Allow local single-frame checks').click());await act(async()=>button('Check fresh frame').click());await act(async()=>root.unmount());expect(signal?.aborted).toBe(true);await act(async()=>finish(result));expect(onResult).not.toHaveBeenCalled()})
it('changing session revokes local consent before any new-session capture',async()=>{const {video}=await mount();await act(async()=>button('Allow local single-frame checks').click());expect(check).not.toBeNull();await act(async()=>root.render(<LocaleProvider initialLocale="en"><LocalCameraCheck live video={video} sessionId="new" register={value=>{check=value}}/></LocaleProvider>));expect(check).toBeNull();expect(button('Check fresh frame').disabled).toBe(true);expect(button('Allow local single-frame checks').disabled).toBe(false)})

it('uses separate camera and adaptive permits and revokes the adaptive frame in flight',async()=>{
 vi.useFakeTimers()
 let resolveFrame!:(r:any)=>void
 let signal:AbortSignal|undefined
 const {onResult}=await mount()
 vi.mocked(api).mockImplementation(async(path,body,method,abort)=>{
  if(path==='/vision/local/permits')return permit((body as {scope:string}).scope) as any
  if(path==='/vision/local'){signal=abort;return new Promise(resolve=>{resolveFrame=resolve})}
  return {} as any
 })
 await act(async()=>button('Allow local single-frame checks').click())
 const checkbox=host.querySelector<HTMLInputElement>('input[type=checkbox]')!
 await act(async()=>checkbox.click())
 await act(async()=>{await vi.advanceTimersByTimeAsync(3000)})
 expect(api).toHaveBeenCalledWith('/vision/local',expect.objectContaining({permit_id:'adaptive-permit',adaptive:true,baseline_consent:false}),undefined,expect.any(AbortSignal))
 await act(async()=>checkbox.click())
 expect(signal?.aborted).toBe(true)
 expect(api).toHaveBeenCalledWith('/vision/local/same',{permit_id:'adaptive-permit'},'DELETE',undefined,true)
 await act(async()=>resolveFrame(result))
 expect(onResult).not.toHaveBeenCalled()
 expect(button('Check fresh frame').disabled).toBe(false)
})

it('revokes a late local permit instead of reenabling checks after stop',async()=>{
 let finish!:(r:any)=>void
 await mount()
 vi.mocked(api).mockImplementation(async(path)=>path==='/vision/local/permits'?new Promise(resolve=>{finish=resolve}):{} as any)
 await act(async()=>button('Allow local single-frame checks').click())
 await act(async()=>button('Stop local checks').click())
 await act(async()=>finish(permit()))
 expect(api).toHaveBeenCalledWith('/vision/local/same',{permit_id:'camera-permit'},'DELETE',undefined,true)
 expect(button('Check fresh frame').disabled).toBe(true)
 expect(captureVideoFrame).not.toHaveBeenCalled()
})
