import {useEffect,useRef} from 'react'
import {appleVertex,appleFragment,particleBudget,makeApplePoints} from '../realtime/appleField'
import {LocalAudioEnergy} from '../realtime/localAudioEnergy'
import type {CallState} from '../realtime/callController'

interface Props {enabled?:boolean;state?:CallState;audioReactive?:boolean;onAudioError?:()=>void}
export function ParticleApple({enabled=true,state='idle',audioReactive=false,onAudioError}:Props){
 const gpu=useRef<HTMLCanvasElement>(null),fallback=useRef<HTMLCanvasElement>(null),meter=useRef(new LocalAudioEnergy()),current=useRef({state,onAudioError})
 current.current={state,onAudioError}
 useEffect(()=>{const media=window.matchMedia?.('(prefers-reduced-motion: reduce)');if(audioReactive&&enabled&&state==='listening'&&!media?.matches&&!document.hidden)void meter.current.start().catch(()=>current.current.onAudioError?.());else meter.current.stop();const stop=()=>meter.current.stop();document.addEventListener('visibilitychange',stop);media?.addEventListener('change',stop);return()=>{stop();document.removeEventListener('visibilitychange',stop);media?.removeEventListener('change',stop)}},[audioReactive,state,enabled])
 useEffect(()=>{
  const el=gpu.current,back=fallback.current;if(!el||!back)return
  const media=window.matchMedia?.('(prefers-reduced-motion: reduce)'),pointer={x:-10000,y:-10000}
  let frame=0,last=-100,program:WebGLProgram|null=null,buffer:WebGLBuffer|null=null,gl:WebGL2RenderingContext|null=null
  try{gl=typeof WebGL2RenderingContext!=='undefined'?el.getContext('webgl2',{alpha:true,antialias:false,preserveDrawingBuffer:true,powerPreference:'low-power'}):null;if(!gl?.createShader)gl=null}catch{gl=null}
  const shaders:WebGLShader[]=[]
  if(gl){try{
   const compile=(kind:number,source:string)=>{const shader=gl!.createShader(kind)!;gl!.shaderSource(shader,source);gl!.compileShader(shader);if(!gl!.getShaderParameter(shader,gl!.COMPILE_STATUS)){gl!.deleteShader(shader);throw Error('shader unavailable')}shaders.push(shader);return shader}
   const vertex=compile(gl.VERTEX_SHADER,appleVertex),fragment=compile(gl.FRAGMENT_SHADER,appleFragment);program=gl.createProgram()!;gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);shaders.forEach(shader=>gl!.deleteShader(shader));shaders.length=0;if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('program unavailable');gl.useProgram(program);buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,makeApplePoints(1048576),gl.STATIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,4,gl.FLOAT,false,0,0);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);back.style.display='none';el.dataset.renderer='webgl2'
  }catch{shaders.forEach(shader=>gl!.deleteShader(shader));if(program)gl.deleteProgram(program);if(buffer)gl.deleteBuffer(buffer);program=null;buffer=null;gl=null}}
  if(!gl){el.style.display='none';back.style.display='block';back.dataset.renderer='canvas-fallback'}
  const fallbackPoints=makeApplePoints(6000)
  let ctx=!gl&&typeof CanvasRenderingContext2D!=='undefined'?back.getContext('2d'):null
  const uniforms=gl&&program?Object.fromEntries(['uSize','uPointer','uTime','uEnergy','uMotion'].map(name=>[name,gl!.getUniformLocation(program!,name)])):{}
  const paint=(time=0)=>{
   const motion=enabled&&!media?.matches,animate=motion&&!document.hidden
   if(animate&&time-last<40){frame=requestAnimationFrame(paint);return}last=time
   const width=window.innerWidth,height=window.innerHeight,dpr=Math.min(window.devicePixelRatio||1,1.25),count=particleBudget(width,!motion)
   const speaking=current.current.state==='speaking',energy=motion?(audioReactive?meter.current.read():0)+(speaking?.16+.12*Math.sin(time*.009):0):0
   if(gl&&program){const w=Math.round(width*dpr),h=Math.round(height*dpr);if(el.width!==w||el.height!==h){el.width=w;el.height=h}el.dataset.particleCount=String(count);gl.useProgram(program);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.uniform2f(uniforms.uSize,w,h);gl.uniform2f(uniforms.uPointer,pointer.x*dpr,pointer.y*dpr);gl.uniform1f(uniforms.uTime,time*.001);gl.uniform1f(uniforms.uEnergy,energy);gl.uniform1f(uniforms.uMotion,motion?1:0);gl.drawArrays(gl.POINTS,0,count);}
   else if(ctx){
    if(back.width!==width||back.height!==height){back.width=width;back.height=height}
    ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,width,height)
    const points=fallbackPoints,total=points.length/4;back.dataset.particleCount=String(total)
    for(let i=0;i<total;i++){
      const x=points[i*4],y=points[i*4+1],z=points[i*4+2],slot=points[i*4+3],slice=slot>.52,curtain=slot>.92
      if(slice&&!curtain&&y>1)continue
      const scale=Math.min(height*.33,width*.23)*(slice?1.25:1)
      let px=width*(slice?.64:.76)+x*scale,py=height*(slice?.94:.40)-y*scale
      if(curtain){px=(x+1)*width*.5;py=(y+1)*height*.5}
      const distance=Math.hypot(px-pointer.x,py-pointer.y)/Math.max(scale,1),local=Math.exp(-distance*distance*10)
      const wave=motion?Math.sin(distance*22-time*.003)*local*18+Math.sin(y*7-time*.003)*energy*scale*.055:0
      px+=x*wave;py+=y*wave
      const radius=Math.hypot(x,y),seed=Math.min(Math.hypot((x+.12)*9,(y-.02)*5),Math.hypot((x-.12)*9,(y+.04)*5))
      ctx.fillStyle=curtain?'rgba(176,22,40,.15)':slice?(seed<1?'rgba(67,12,16,.7)':radius>.93?'rgba(170,14,32,.8)':'rgba(241,140,139,.55)'):z>0?'rgba(157,18,29,.65)':'rgba(84,8,19,.5)'
      ctx.beginPath();ctx.arc(px,py,curtain?.7:slice?1.6:1.7,0,Math.PI*2);ctx.fill()
    }
   }
   if(animate)frame=requestAnimationFrame(paint)
  }
  const update=()=>{cancelAnimationFrame(frame);last=-100;paint(performance.now())}
  const move=(e:PointerEvent)=>{if(enabled&&!media?.matches){pointer.x=e.clientX;pointer.y=e.clientY}}
  const leave=()=>{pointer.x=-10000;pointer.y=-10000}
  const lost=(e:Event)=>{e.preventDefault();cancelAnimationFrame(frame);gl=null;program=null;buffer=null;el.style.display='none';back.style.display='block';back.dataset.renderer='canvas-fallback';ctx=typeof CanvasRenderingContext2D!=='undefined'?back.getContext('2d'):null;update()}
  window.addEventListener('pointermove',move,{passive:true});document.addEventListener('pointerleave',leave);window.addEventListener('resize',update);document.addEventListener('visibilitychange',update);media?.addEventListener('change',update);el.addEventListener('webglcontextlost',lost);paint()
  return()=>{cancelAnimationFrame(frame);if(gl&&program)gl.deleteProgram(program);if(gl&&buffer)gl.deleteBuffer(buffer);window.removeEventListener('pointermove',move);document.removeEventListener('pointerleave',leave);window.removeEventListener('resize',update);document.removeEventListener('visibilitychange',update);media?.removeEventListener('change',update);el.removeEventListener('webglcontextlost',lost)}
 },[enabled,audioReactive])
 return <div className="apple-particle-field" aria-hidden="true" data-wave-kind={state==='speaking'?'playback-state':audioReactive&&state==='listening'?'local-audio':'ambient'}><canvas ref={gpu} className="particle-apple" aria-hidden="true"/><canvas ref={fallback} className="particle-apple" aria-hidden="true"/></div>
}
