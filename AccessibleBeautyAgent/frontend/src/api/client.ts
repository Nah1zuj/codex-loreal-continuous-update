export async function api<T>(path:string, body?:unknown, method?:string,signal?:AbortSignal):Promise<T> {
  const response = await fetch('/api'+path,{method:method??(body===undefined?'GET':'POST'),headers:body===undefined?undefined:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:signal?AbortSignal.any([signal,AbortSignal.timeout(120_000)]):AbortSignal.timeout(120_000)})
  const json = await response.json()
  if(!response.ok) throw Object.assign(new Error(typeof json.detail==='string'?json.detail:JSON.stringify(json.detail??json)),{status:response.status})
  return json as T
}

export interface VideoSampleRequest {
 session_id:string; task:'blush_presence'|'lip_presence'; images:[string]
 capture_kind:'video_sample'; remote_frame_consent:boolean
}
export async function analyzeVideoSample(body:VideoSampleRequest,signal?:AbortSignal):Promise<unknown>{
 if(body.remote_frame_consent!==true)throw new Error('Explicit remote frame consent required')
 const response=await fetch('/api/vision/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:signal?AbortSignal.any([signal,AbortSignal.timeout(120_000)]):AbortSignal.timeout(120_000)})
 const json=await response.json()
 if(!response.ok)throw Object.assign(new Error(typeof json.detail==='string'?json.detail:JSON.stringify(json.detail??json)),{status:response.status})
 return json
}
