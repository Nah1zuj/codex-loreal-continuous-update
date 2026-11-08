// @vitest-environment jsdom
import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach,expect,it,vi} from 'vitest'
import {api} from '../api/client'
import {LocaleProvider} from '../content/Locale'
import {captureStillFrame} from '../vision/camera'
import {Reading} from './Reading'

vi.mock('../api/client',()=>({api:vi.fn()}))
vi.mock('../vision/camera',()=>({captureStillFrame:vi.fn()}))
vi.mock('../accessibility/useSpeech',()=>({useSpeech:()=>({speak:vi.fn(),stop:vi.fn()})}))

afterEach(()=>{vi.restoreAllMocks();vi.clearAllMocks()})

function preview(){
  const track=Object.assign(new EventTarget(),{readyState:'live',stop:vi.fn()})
  track.stop.mockImplementation(()=>{track.readyState='ended'})
  const media={getTracks:()=>[track],getVideoTracks:()=>[track]} as unknown as MediaStream
  return {track,media}
}

function mockCamera(...streams:MediaStream[]){
  const getUserMedia=vi.fn()
  for(const stream of streams)getUserMedia.mockResolvedValueOnce(stream)
  vi.stubGlobal('navigator',{mediaDevices:{getUserMedia}})
  return getUserMedia
}

it('keeps preview local, refuses without a POST and sends one explicitly authorized frame',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true)
  vi.spyOn(HTMLMediaElement.prototype,'play').mockResolvedValue()
  const first=preview(),second=preview()
  const getUserMedia=mockCamera(first.media,second.media)
  vi.mocked(captureStillFrame).mockReturnValue('data:image/jpeg;base64,fixture')
  let remoteVerification='unverified'
  vi.mocked(api).mockImplementation(async(path:string)=>{
    if(path==='/reading/availability')return {provider:'qwen',status:'configured',
      service_name:'Alibaba Cloud Model Studio (Qwen)',destination_host:'label.example',
      remote_verification:remoteVerification} as never
    remoteVerification='verified'
    return {label_kind:'garment',status:'UNCERTAIN',summary:'Partial text',uncertain_characters:['[unknown]'],
     full_text:'Label ABC\nFiber: 1[unknown]0% cotton',service:'qwen',simulated:false} as never
  })
  const host=document.createElement('div')
  document.body.append(host)
  const root=createRoot(host)
  try{
    await act(async()=>root.render(<LocaleProvider initialLocale="en"><Reading health={null} onError={vi.fn()}/></LocaleProvider>))
    const click=(label:string)=>act(async()=>[...host.querySelectorAll('button')].find(button=>button.textContent===label)!.click())
    const submitted=()=>vi.mocked(api).mock.calls.filter(([path])=>path==='/reading/read')
    const video=host.querySelector('video')!
    Object.defineProperty(video,'readyState',{value:2})
    expect(host.textContent).toContain('Alibaba Cloud Model Studio (Qwen)')
    expect(host.textContent).toContain('A live request has yet to be verified in this run.')
    await click('Open local label preview')
    await act(async()=>video.dispatchEvent(new Event('loadeddata')))
    expect(getUserMedia).toHaveBeenCalledWith({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1024},height:{ideal:768}}})
    expect(submitted()).toHaveLength(0)
    await click('Close without sending')
    expect(submitted()).toHaveLength(0)
    expect(host.textContent).toContain('A live request has yet to be verified in this run.')
    expect(first.track.stop).toHaveBeenCalledOnce()

    await click('Open local label preview')
    await act(async()=>video.dispatchEvent(new Event('loadeddata')))
    await click('Allow and send one label image')
    expect(submitted()).toHaveLength(1)
    expect(submitted()[0][1]).toMatchObject({
      explicit_consent:true,remote_upload_consent:true,authorized_provider:'qwen',
      authorized_destination_host:'label.example',demo:false,
    })
    expect(second.track.stop).toHaveBeenCalledOnce()
    expect(host.textContent).toContain('The remote label service returned a valid result in this run.')
    expect(host.textContent).toContain('[unknown]')
    await click('Read all text')
    expect(host.querySelector('pre')?.textContent).toBe('Label ABC\nFiber: 1[unknown]0% cotton')
  }finally{
    await act(async()=>root.unmount())
    host.remove()
    vi.unstubAllGlobals()
  }
})

it('requires a fresh preview after track loss and never captures a cached frame',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true)
  vi.spyOn(HTMLMediaElement.prototype,'play').mockResolvedValue()
  const first=preview(),second=preview()
  const getUserMedia=mockCamera(first.media,second.media)
  vi.mocked(captureStillFrame).mockReturnValue('data:image/jpeg;base64,cached-fixture')
  vi.mocked(api).mockImplementation(async path=>path==='/reading/availability'
    ?{provider:'qwen',status:'configured',service_name:'Test label service',destination_host:'label.example'} as never
    :{label_kind:'product',status:'UNCERTAIN',summary:'Fixture reply',uncertain_characters:[],service:'qwen'} as never)
  const host=document.createElement('div')
  document.body.append(host)
  const root=createRoot(host)
  try{
    await act(async()=>root.render(<LocaleProvider initialLocale="en"><Reading health={null} onError={vi.fn()}/></LocaleProvider>))
    const button=(label:string)=>[...host.querySelectorAll('button')].find(button=>button.textContent===label)!
    const send=button('Allow and send one label image')
    const video=host.querySelector('video')!
    Object.defineProperty(video,'readyState',{value:2})
    const open=async()=>{
      await act(async()=>button('Open local label preview').click())
      await act(async()=>video.dispatchEvent(new Event('loadeddata')))
      expect(send.disabled).toBe(false)
    }
    await open()
    first.track.readyState='ended'
    await act(async()=>send.click())
    expect(captureStillFrame).not.toHaveBeenCalled()
    expect(send.disabled).toBe(true)
    expect(video.srcObject).toBeNull()

    await open()
    await act(async()=>{
      second.track.readyState='ended'
      second.track.dispatchEvent(new Event('ended'))
    })
    expect(send.disabled).toBe(true)
    expect(video.srcObject).toBeNull()
    expect(host.textContent).toContain('Open a new local label preview')
    expect(vi.mocked(api).mock.calls.some(([path])=>path==='/reading/read')).toBe(false)
    expect(getUserMedia).toHaveBeenCalledTimes(2)
  }finally{
    await act(async()=>root.unmount())
    host.remove()
    vi.unstubAllGlobals()
  }
})
