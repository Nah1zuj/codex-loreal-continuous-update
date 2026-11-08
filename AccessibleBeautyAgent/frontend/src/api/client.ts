export async function api<T>(path:string, body?:unknown, method?:string,signal?:AbortSignal,keepalive=false):Promise<T> {
  const response = await fetch('/api'+path,{method:method??(body===undefined?'GET':'POST'),headers:body===undefined?undefined:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),keepalive,signal:signal?AbortSignal.any([signal,AbortSignal.timeout(120_000)]):AbortSignal.timeout(120_000)})
  const json = await response.json()
  if(!response.ok) throw Object.assign(new Error(typeof json.detail==='string'?json.detail:JSON.stringify(json.detail??json)),{status:response.status})
  return json as T
}
