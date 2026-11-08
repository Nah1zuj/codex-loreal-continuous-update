import {hasLiveVideoTrack} from './cameraStream'

export interface CapturedFrame {image:string; pixels:Uint8ClampedArray}
/** Captures one downscaled JPEG in RAM; never records a video or persists pixels. */
export function captureVideoFrame(video: HTMLVideoElement): CapturedFrame | null {
 if(video.readyState < 2 || !video.videoWidth || !video.videoHeight || !hasLiveVideoTrack(video.srcObject)) return null
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
