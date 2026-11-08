import {describe,it,expect,vi,afterEach} from 'vitest'
import {streamChat} from './stream'
afterEach(()=>vi.unstubAllGlobals())
describe('streaming conversation',()=>{
 it('preserves pre-stream HTTP status for safe expired-session recovery',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('missing',{status:404})))
  await expect(streamChat({session_id:'expired'})).rejects.toMatchObject({status:404})
 })
 it('handles split unicode chunks, deltas and final result',async()=>{
  const encoder=new TextEncoder(),raw='data: {"type":"delta","text":"你好"}\n\ndata: {"type":"final","reply":{"message":"你好"}}\n\n'
  const bytes=encoder.encode(raw)
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(new ReadableStream({start(c){c.enqueue(bytes.slice(0,40));c.enqueue(bytes.slice(40));c.close()}}))))
  const deltas:string[]=[]
  expect((await streamChat({},v=>deltas.push(v))).message).toBe('你好')
  expect(deltas.join('')).toBe('你好')
 })
 it('does not treat incomplete or failed stream as a successful answer',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('data: {"type":"error","message":"unavailable"}\n\n')))
  await expect(streamChat({})).rejects.toThrow('unavailable')
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('data: {"type":"delta","text":"partial"}\n\n')))
  await expect(streamChat({})).rejects.toThrow('incomplete')
 })
})
