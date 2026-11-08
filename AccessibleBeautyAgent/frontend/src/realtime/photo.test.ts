import {it,expect,vi,afterEach} from 'vitest'
import {preparePhoto} from './photo'
afterEach(()=>vi.unstubAllGlobals())
it('rejects unsupported or oversized files before decoding or transmitting',async()=>{
 const bitmap=vi.fn();vi.stubGlobal('createImageBitmap',bitmap)
 await expect(preparePhoto({type:'video/mp4',size:20} as File)).rejects.toThrow('JPEG')
 await expect(preparePhoto({type:'image/jpeg',size:16*1024*1024} as File)).rejects.toThrow('15 MB')
 expect(bitmap).not.toHaveBeenCalled()
})
