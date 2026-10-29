import type {Reply,Session} from '../types'
/** SSE over POST: cancellation closes the reader and aborts the provider connection. */
export async function streamChat(body:unknown,onDelta?:(text:string)=>void,signal?:AbortSignal,onSession?:(session:Session)=>void):Promise<Reply>{
 const response=await fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:signal?AbortSignal.any([signal,AbortSignal.timeout(120_000)]):AbortSignal.timeout(120_000)})
 if(!response.ok)throw Object.assign(new Error('Conversation request failed ('+response.status+')'),{status:response.status})
 const reader=response.body?.getReader();if(!reader)throw new Error('Streaming unavailable')
 const decoder=new TextDecoder();let buffer='',final:Reply|undefined
 try{
  while(true){
   const {done,value}=await reader.read();buffer+=decoder.decode(value,{stream:!done})
   let boundary:number
   while((boundary=buffer.indexOf('\n\n'))>=0){
    const frame=buffer.slice(0,boundary);buffer=buffer.slice(boundary+2)
    for(const line of frame.split('\n')){
     if(!line.startsWith('data: '))continue
     const event=JSON.parse(line.slice(6))
     if(event.type==='delta'&&typeof event.text==='string')onDelta?.(event.text)
     if(event.type==='session'&&event.session)onSession?.(event.session)
     if(event.type==='final')final=event.reply
     if(event.type==='error')throw new Error(event.message)
    }
   }
   if(buffer.length>100_000)throw new Error('Stream exceeded limit')
   if(done)break
  }
  if(!final)throw new Error('Conversation stream incomplete')
  return final
 }finally{await reader.cancel().catch(()=>{});reader.releaseLock()}
}
