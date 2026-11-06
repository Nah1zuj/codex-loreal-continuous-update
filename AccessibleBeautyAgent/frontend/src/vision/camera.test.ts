import {describe,it,expect,vi} from 'vitest'
import {stopStream,captureThreeFrames} from './camera'
describe('camera privacy',()=>{
  it('stops every media track on close',()=>{
    const a=vi.fn(),b=vi.fn()
    stopStream({getTracks:()=>[{stop:a},{stop:b}]} as unknown as MediaStream)
    expect(a).toHaveBeenCalledOnce();expect(b).toHaveBeenCalledOnce()
  })
  it('does not capture before camera is ready',async()=>{
    await expect(captureThreeFrames({readyState:0,videoWidth:0} as HTMLVideoElement)).rejects.toThrow('相机尚未准备好')
  })
})
