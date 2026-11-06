// @vitest-environment jsdom
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach,expect,it,vi} from 'vitest'
import {api} from '../api/client'
import {LocaleProvider} from '../content/Locale'
import {captureStillFrame,openCamera,stopStream} from '../vision/camera'
import {Reading} from './Reading'

vi.mock('../api/client',()=>({api:vi.fn()}))
vi.mock('../vision/camera',()=>({
  openCamera:vi.fn(),stopStream:vi.fn(),captureStillFrame:vi.fn(),
}))
vi.mock('../accessibility/useSpeech',()=>({useSpeech:()=>({speak:vi.fn(),stop:vi.fn()})}))

afterEach(()=>vi.restoreAllMocks())

it('keeps preview local, refuses without a POST and sends one explicitly authorized frame',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true)
  vi.spyOn(HTMLMediaElement.prototype,'play').mockResolvedValue()
  const preview={} as MediaStream
  vi.mocked(openCamera).mockResolvedValue(preview)
  vi.mocked(captureStillFrame).mockReturnValue('data:image/jpeg;base64,fixture')
  vi.mocked(api).mockImplementation(async(path:string)=>(
    path==='/reading/availability'?{provider:'qwen',status:'configured',service_name:'Alibaba Cloud Model Studio (Qwen)'}:
    {label_kind:'garment',status:'UNCERTAIN',summary:'Partial text',uncertain_characters:['[unknown]'],
     full_text:'Label ABC\nFiber: 1[unknown]0% cotton',service:'qwen',simulated:false}
  ) as never)
  const host=document.createElement('div')
  document.body.append(host)
  const root=createRoot(host)
  try{
    await act(async()=>root.render(<LocaleProvider initialLocale="en"><Reading health={null} onError={vi.fn()}/></LocaleProvider>))
    const click=(label:string)=>act(async()=>[...host.querySelectorAll('button')].find(button=>button.textContent===label)!.click())
    const submitted=()=>vi.mocked(api).mock.calls.filter(([path])=>path==='/reading/read')
    expect(host.textContent).toContain('Alibaba Cloud Model Studio (Qwen)')
    await click('Open local label preview')
    await act(async()=>host.querySelector('video')!.dispatchEvent(new Event('loadeddata')))
    expect(submitted()).toHaveLength(0)
    await click('Close without sending')
    expect(submitted()).toHaveLength(0)
    expect(stopStream).toHaveBeenCalledWith(preview)

    await click('Open local label preview')
    await act(async()=>host.querySelector('video')!.dispatchEvent(new Event('loadeddata')))
    await click('Allow and send one label image')
    expect(submitted()).toHaveLength(1)
    expect(submitted()[0][1]).toMatchObject({
      explicit_consent:true,remote_upload_consent:true,authorized_provider:'qwen',demo:false,
    })
    expect(host.textContent).toContain('[unknown]')
    await click('Read all text')
    expect(host.querySelector('pre')?.textContent).toBe('Label ABC\nFiber: 1[unknown]0% cotton')
  }finally{
    await act(async()=>root.unmount())
    host.remove()
    vi.unstubAllGlobals()
  }
})
