/* Mono 16 kHz PCM; only transient buffers, no recording or storage. */
class TracePCM extends AudioWorkletProcessor{
 constructor(){super();this.phase=0;this.sum=0;this.count=0;this.frame=new Int16Array(640);this.offset=0}
 process(inputs,outputs){
  const input=inputs[0]?.[0]
  if(input)for(const value of input){this.sum+=value;this.count++;this.phase+=16000;if(this.phase>=sampleRate){this.phase-=sampleRate;const mean=this.sum/this.count;this.sum=0;this.count=0;this.frame[this.offset++]=Math.max(-32768,Math.min(32767,Math.round(mean*32767)));if(this.offset===640){this.port.postMessage(this.frame.buffer,[this.frame.buffer]);this.frame=new Int16Array(640);this.offset=0}}}
  for(const output of outputs)for(const channel of output)channel.fill(0)
  return true
 }
}
registerProcessor('trace-pcm',TracePCM)
