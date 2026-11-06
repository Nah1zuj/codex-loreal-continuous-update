export function stopStream(stream:MediaStream|null){stream?.getTracks().forEach(track=>track.stop())}
export async function openCamera(facingMode:'user'|'environment'='user'){
  if(!navigator.mediaDevices?.getUserMedia)throw new Error('相机不可用，请使用 localhost/HTTPS 或模拟演示。')
  return navigator.mediaDevices.getUserMedia({video:{facingMode,width:{ideal:1024},height:{ideal:768}},audio:false})
}
export function captureStillFrame(video:HTMLVideoElement):string{if(!video||video.readyState<2||!video.videoWidth)throw new Error('相机尚未准备好。');const canvas=document.createElement('canvas');const scale=Math.min(1,1024/Math.max(video.videoWidth,video.videoHeight));canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);const context=canvas.getContext('2d');if(!context)throw new Error('无法捕获画面。');context.drawImage(video,0,0,canvas.width,canvas.height);return canvas.toDataURL('image/jpeg',.8)}
