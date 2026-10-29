import {describe,it,expect,vi,afterEach} from 'vitest'
import {hardwareRequest} from './gateway'
afterEach(()=>vi.unstubAllGlobals())
describe('bounded hardware transport',()=>{
 it('uses a scoped header rather than URL credentials',async()=>{
  const request=vi.fn().mockResolvedValue({ok:true,json:async()=>({workflow:'READY'})});vi.stubGlobal('fetch',request)
  await hardwareRequest('/display',undefined,'scoped-device-token')
  expect(request.mock.calls[0][0]).toBe('/api/hardware/display')
  expect(request.mock.calls[0][1].headers.Authorization).toBe('Bearer scoped-device-token')
 })
 it('rejects a revoked device and supports cancellation',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({detail:'Device revoked'})}))
  await expect(hardwareRequest('/display')).rejects.toThrow('Device revoked')
 })
})
