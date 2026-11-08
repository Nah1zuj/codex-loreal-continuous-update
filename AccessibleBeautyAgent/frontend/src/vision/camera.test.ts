import {describe,it,expect} from 'vitest'
import {captureStillFrame} from './camera'
describe('camera privacy',()=>{
  it('does not capture before camera is ready',()=>{
    expect(()=>captureStillFrame({readyState:0,videoWidth:0} as HTMLVideoElement)).toThrow('相机尚未准备好')
  })
})
