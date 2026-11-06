import {afterEach,it,expect,vi} from 'vitest'
import {api} from './client'
afterEach(()=>vi.unstubAllGlobals())
it('preserves consent in the request body',async()=>{
  const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({saved:true})})
  vi.stubGlobal('fetch',fetch)
  expect(await api('/memory',{explicit_consent:false})).toEqual({saved:true})
  expect(fetch.mock.calls[0][1].body).toBe('{"explicit_consent":false}')
})
it('surfaces rejected API requests to UI',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({detail:'Explicit consent required'})}))
  await expect(api('/memory',{})).rejects.toThrow('Explicit consent required')
})
