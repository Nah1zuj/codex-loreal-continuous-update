import {analyzeVideoSample, type VideoSampleRequest} from '../api/client'
export type FrameTask = 'blush_presence' | 'lip_presence'
export interface FrameAnalysisOptions {
 video: HTMLVideoElement; sessionId: string; task: FrameTask
 cameraConsent: boolean; remoteFrameConsent: boolean; intervalMs?: number
 onResult?: (result: unknown) => void; onError?: (error: unknown) => void
}
export interface CapturedFrame {image:string; pixels:Uint8ClampedArray}
interface Dependencies {
 capture?: (video: HTMLVideoElement) => string | CapturedFrame | null
 hasChanged?: (previous: string | null, current: string) => boolean
 send?: (request: VideoSampleRequest, signal: AbortSignal) => Promise<unknown>
 localAnalyze?: (image: string, task: FrameTask) => Promise<unknown>
}
/** Captures one downscaled JPEG in RAM; never records a video or persists pixels. */
export function captureVideoFrame(video: HTMLVideoElement): CapturedFrame | null {
 if(video.readyState < 2 || !video.videoWidth || !video.videoHeight || !video.srcObject) return null
 const scale=Math.min(1,1024/Math.max(video.videoWidth,video.videoHeight))
 const canvas=document.createElement('canvas');canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale)
 const ctx=canvas.getContext('2d');if(!ctx)return null
 ctx.drawImage(video,0,0,canvas.width,canvas.height)
 const image=canvas.toDataURL('image/jpeg',0.75)
 // Tiny RGB signature permits local noise rejection without retaining full pixels.
 const signature=document.createElement('canvas');signature.width=signature.height=32
 const small=signature.getContext('2d');if(!small)return null
 small.drawImage(canvas,0,0,32,32);const pixels=small.getImageData(0,0,32,32).data
 canvas.width=canvas.height=signature.width=signature.height=0
 return image.length<=3_000_000 ? {image,pixels} : null
}
export class FrameAnalysisScheduler {
 private options: FrameAnalysisOptions | null=null
 private timer: ReturnType<typeof setInterval> | null=null
 private generation=0;private busy=false;private lastAttempt=-Infinity;private previous:string|null=null;private previousPixels:Uint8ClampedArray|null=null
 private abort: AbortController|null=null
 constructor(private readonly dependencies: Dependencies={}){}
 start(options:FrameAnalysisOptions):void {
  this.stop();this.options={...options}
  this.timer=setInterval(()=>{void this.analyzeNow('interval')},Math.max(2500,options.intervalMs??2500))
 }
 async analyzeNow(reason:string):Promise<void>{
  const options=this.options
  if(!options || !options.cameraConsent || this.busy || Date.now()-this.lastAttempt<Math.max(2500,options.intervalMs??2500))return
  if(!options.remoteFrameConsent && !this.dependencies.localAnalyze)return
  this.busy=true;const generation=this.generation
  try{
   const captured=(this.dependencies.capture??captureVideoFrame)(options.video)
   if(!captured)return
   const frame=typeof captured==='string'?captured:captured.image
   let changed=this.previous!==frame
   if(this.dependencies.hasChanged)changed=this.dependencies.hasChanged(this.previous,frame)
   else if(typeof captured!=='string' && this.previousPixels && this.previousPixels.length===captured.pixels.length){
    let difference=0;let count=0
    for(let i=0;i<captured.pixels.length;i++)if(i%4!==3){difference+=Math.abs(captured.pixels[i]-this.previousPixels[i]);count++}
    changed=difference/Math.max(1,count)/255>=0.025
   }
   if(!changed && reason==='interval')return
   this.lastAttempt=Date.now()
   this.previous=frame;this.previousPixels=typeof captured==='string'?null:captured.pixels;this.abort=new AbortController()
   const result=options.remoteFrameConsent
    ? await (this.dependencies.send??analyzeVideoSample)({session_id:options.sessionId,task:options.task,images:[frame],capture_kind:'video_sample',remote_frame_consent:true},this.abort.signal)
    : await this.dependencies.localAnalyze!(frame,options.task)
   if(generation===this.generation)options.onResult?.(result)
  }catch(error){if(generation===this.generation)options.onError?.(error)}
  finally{this.busy=false;if(generation===this.generation)this.abort=null}
 }
 stop():void{
  this.generation++;if(this.timer!==null)clearInterval(this.timer)
  this.timer=null;this.options=null;this.abort?.abort();this.abort=null;this.previous=null;this.previousPixels=null
  // Keep the privacy rate cap across stop/restart cycles.
 }
}
