export type DeviceStatus={id:string;name:string;type:string;capabilities:string[];connection_state:string;expires:number}
export type DisplayState={device:DeviceStatus;session_id:string;workflow:string;step:{title:string;instruction:string;review_status:string}|null;progress:{completed:number;total:number}|null;illustration_only:boolean}
export async function hardwareRequest<T>(path:string,body?:unknown,token?:string,signal?:AbortSignal,method?:string):Promise<T>{
 const response=await fetch('/api/hardware'+path,{method:method??(body===undefined?'GET':'POST'),headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},body:body===undefined?undefined:JSON.stringify(body),signal:signal?AbortSignal.any([signal,AbortSignal.timeout(8000)]):AbortSignal.timeout(8000),cache:'no-store'})
 const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Hardware request rejected');return data as T
}
