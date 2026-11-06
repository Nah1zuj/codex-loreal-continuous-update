/** Local RMS only. No audio destination, recording, upload or persistent samples. */
export class LocalAudioEnergy {
 value=0
 private generation=0
 private stream:MediaStream|null=null
 private context:AudioContext|null=null
 private analyser:AnalyserNode|null=null
 private samples:Uint8Array<ArrayBuffer>|null=null
 async start(){
  this.stop();const token=this.generation
  let stream:MediaStream
  try{stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false})}
  catch(error){if(token!==this.generation)return;throw error}
  if(token!==this.generation){stream.getTracks().forEach(t=>t.stop());return}
  this.stream=stream
  try{const context=new AudioContext();this.context=context;const analyser=context.createAnalyser();analyser.fftSize=256;context.createMediaStreamSource(stream).connect(analyser);this.analyser=analyser;this.samples=new Uint8Array(256);await context.resume()}
  catch(e){if(token!==this.generation)return;this.stop();throw e}
 }
 read(){if(!this.analyser||!this.samples)return 0;this.analyser.getByteTimeDomainData(this.samples);let sum=0;for(const n of this.samples)sum+=((n-128)/128)**2;this.value=this.value*.72+Math.min(1,Math.sqrt(sum/this.samples.length)*6)*.28;return this.value}
 stop(){this.generation++;this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;const context=this.context;this.context=null;if(context)void context.close().catch(()=>{});this.analyser=null;this.samples=null;this.value=0}
}
