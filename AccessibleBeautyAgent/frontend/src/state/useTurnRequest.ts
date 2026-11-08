import {useEffect,useRef} from 'react'

class TurnRequest {
  private controller:AbortController|null=null
  private epoch=0

  get version(){return this.epoch}

  invalidate(){
    this.epoch++
    this.controller?.abort()
    this.controller=null
  }

  begin(external?:AbortSignal){
    this.invalidate()
    const version=this.epoch
    const controller=new AbortController()
    this.controller=controller
    const signal=external?AbortSignal.any([controller.signal,external]):controller.signal
    return {
      signal,
      current:()=>version===this.epoch&&!signal.aborted,
      latest:()=>version===this.epoch,
    }
  }
}

export function useTurnRequest(){
  const request=useRef<TurnRequest|null>(null)
  request.current??=new TurnRequest()
  useEffect(()=>{
    const current=request.current
    return ()=>current?.invalidate()
  },[])
  return request.current
}
