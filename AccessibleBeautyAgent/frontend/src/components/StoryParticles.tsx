import {useEffect,useRef,useState} from 'react'
import type {CallState} from '../realtime/callController'
import {LocalAudioEnergy} from '../realtime/localAudioEnergy'
import {StoryField,storyQuality,storyVertex,storyFragment,type StoryState,type QualityName} from '../realtime/storyField'

export function StoryParticles({enabled,state,audioReactive,onAudioError}:{enabled:boolean;state:CallState;audioReactive:boolean;onAudioError:()=>void}){
 const canvas=useRef<HTMLCanvasElement>(null),meter=useRef(new LocalAudioEnergy()),repaint=useRef<()=>void>(()=>{})
 const [contextVersion,setContextVersion]=useState(0)
 const latest=useRef({state,audioReactive,onAudioError}),changedAt=useRef(performance.now());latest.current={state,audioReactive,onAudioError}
 useEffect(()=>{
  const media=window.matchMedia?.('(prefers-reduced-motion: reduce)')
  if(enabled&&audioReactive&&state==='listening'&&!media?.matches&&!document.hidden)void meter.current.start().catch(()=>latest.current.onAudioError())
  else meter.current.stop()
  const stop=()=>meter.current.stop();document.addEventListener('visibilitychange',stop);media?.addEventListener('change',stop)
  return()=>{stop();document.removeEventListener('visibilitychange',stop);media?.removeEventListener('change',stop)}
 },[enabled,state,audioReactive])
 useEffect(()=>{changedAt.current=performance.now();repaint.current()},[state])
 useEffect(()=>{
  const el=canvas.current;if(!el)return
  const media=window.matchMedia?.('(prefers-reduced-motion: reduce)')
  let gl:WebGLRenderingContext|null=null,ctx:CanvasRenderingContext2D|null=null,program:WebGLProgram|null=null
  let positionBuffer:WebGLBuffer|null=null,styleBuffer:WebGLBuffer|null=null,raf=0,last=0,frames=0,statsAt=0,samples:number[]=[],costs:number[]=[],downgraded:QualityName|null=null
  const pointer={x:-100,y:-100};let hover=false,field:StoryField|null=null,width=0,height=0,dpr=1,quality:QualityName='HIGH',scroll=0
  const shaders:WebGLShader[]=[]
  try{if(typeof WebGLRenderingContext!=='undefined')gl=el.getContext('webgl',{alpha:true,antialias:false,powerPreference:'low-power'})}catch{gl=null}
  if(gl){try{
   const compile=(type:number,source:string)=>{const shader=gl!.createShader(type)!;shaders.push(shader);gl!.shaderSource(shader,source);gl!.compileShader(shader);if(!gl!.getShaderParameter(shader,gl!.COMPILE_STATUS))throw Error('Particle shader unavailable');return shader}
   program=gl.createProgram()!;gl.attachShader(program,compile(gl.VERTEX_SHADER,storyVertex));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,storyFragment));gl.linkProgram(program)
   if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Particle program unavailable')
   positionBuffer=gl.createBuffer();styleBuffer=gl.createBuffer();el.dataset.renderer='webgl-points'
  }catch{if(program)gl.deleteProgram(program);if(positionBuffer)gl.deleteBuffer(positionBuffer);if(styleBuffer)gl.deleteBuffer(styleBuffer);program=null;gl=null}
  finally{for(const shader of shaders)gl?.deleteShader(shader)}}
  if(!gl){try{if(typeof CanvasRenderingContext2D!=='undefined')ctx=el.getContext('2d')}catch{ctx=null}el.dataset.renderer=ctx?'canvas-points':'unavailable'}
  const uniforms=gl&&program?Object.fromEntries(['uSize','uDpr','uScroll'].map(name=>[name,gl!.getUniformLocation(program!,name)])):{}
  const isStatic=()=>!enabled||!!media?.matches
  function configure(){
   width=window.innerWidth;height=window.innerHeight;dpr=Math.min(window.devicePixelRatio||1,width<600?1:1.5)
   const desired=storyQuality(width,isStatic());quality=downgraded&&!isStatic()?downgraded:desired.name
   const count=quality==='HIGH'?12000:quality==='MEDIUM'?6000:quality==='LOW'?1800:1200
   if(!field||field.count!==count){field=new StoryField(count);if(gl&&styleBuffer){gl.bindBuffer(gl.ARRAY_BUFFER,styleBuffer);gl.bufferData(gl.ARRAY_BUFFER,field.style,gl.STATIC_DRAW)}}
   el!.width=Math.round(width*dpr);el!.height=Math.round(height*dpr)
   el!.dataset.quality=quality;el!.dataset.particleCount=String(count);el!.dataset.dpr=String(dpr)
   el!.dataset.bufferBytes=String(field.position.byteLength+field.velocity.byteLength+field.acceleration.byteLength+field.target.byteLength+field.home.byteLength+field.style.byteLength)
  }
  const artistState=():StoryState=>isStatic()?'REDUCED_MOTION':latest.current.state==='listening'?'LISTENING':latest.current.state==='thinking'?'THINKING':latest.current.state==='speaking'?'SPEAKING':(latest.current.state==='requesting_permission'||(['paused','ended'].includes(latest.current.state)&&performance.now()-changedAt.current<2500))?'TRANSITIONING':hover?'HOVER':'IDLE'
  function paint(time:number){
   if(!field)return
   const submittedAt=performance.now()
   const active=!isStatic()&&!document.hidden,dt=last?(time-last)/1000:0;last=time
   const mode=artistState();el!.dataset.state=mode;el!.dataset.running=String(active)
   if(!active){el!.dataset.fps='0';delete el!.dataset.frameMs;delete el!.dataset.frameP95Ms;delete el!.dataset.cpuSubmitMs}
   el!.dataset.scheduling=dt>.25?'throttled':'active'
   el!.dataset.audioSource=latest.current.audioReactive&&mode==='LISTENING'?'local-mic-rms':mode==='SPEAKING'?'speech-state-only':'none'
   field.step(dt,mode,mode==='LISTENING'&&latest.current.audioReactive?meter.current.read():0,hover?pointer:null)
   if(gl&&program&&positionBuffer&&styleBuffer){
    gl.useProgram(program);gl.viewport(0,0,el!.width,el!.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT)
    gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA)
    gl.bindBuffer(gl.ARRAY_BUFFER,positionBuffer);gl.bufferData(gl.ARRAY_BUFFER,field.position,gl.DYNAMIC_DRAW)
    const pos=gl.getAttribLocation(program,'aPosition');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,3,gl.FLOAT,false,0,0)
    gl.bindBuffer(gl.ARRAY_BUFFER,styleBuffer);const style=gl.getAttribLocation(program,'aStyle');gl.enableVertexAttribArray(style);gl.vertexAttribPointer(style,4,gl.FLOAT,false,0,0)
    gl.uniform2f(uniforms.uSize,width,height);gl.uniform1f(uniforms.uDpr,dpr);gl.uniform1f(uniforms.uScroll,scroll);gl.drawArrays(gl.POINTS,0,field.count)
   }else if(ctx){
    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);const scale=Math.min(height*.30,width*.34)
    for(let i=0;i<field.count;i++){
     const perspective=1/(1+field.position[i*3+2]*.22),x=width*.7+field.position[i*3]*scale*perspective,y=height*(.47+scroll*.025)-field.position[i*3+1]*scale*perspective
     const readingFade=Math.max(0,Math.min(1,(x/width-.26)/.29));ctx.fillStyle=`rgba(135,47,64,${field.style[i*4+3]*readingFade*.7})`
     ctx.beginPath();ctx.arc(x,y,field.style[i*4+2]*perspective*.5,0,Math.PI*2);ctx.fill()
    }
   }
   el!.dataset.drawFrames=String(++frames)
   costs.push(performance.now()-submittedAt);if(costs.length>60)costs.shift()
   // Background browser surfaces may throttle even while visibilityState says
   // visible. Do not mistake a one-second scheduler gap for GPU/CPU overload.
   if(active&&dt>0&&dt<.25){samples.push(dt*1000);if(samples.length>60)samples.shift()}
   if(time-statsAt>1000&&samples.length>=30){
    const average=samples.reduce((a,b)=>a+b,0)/samples.length,sorted=[...samples].sort((a,b)=>a-b)
    el!.dataset.frameMs=average.toFixed(2);el!.dataset.fps=(1000/average).toFixed(1);el!.dataset.frameP95Ms=sorted[Math.floor(sorted.length*.95)].toFixed(2);statsAt=time
    el!.dataset.cpuSubmitMs=(costs.reduce((a,b)=>a+b,0)/costs.length).toFixed(2)
    if(samples.length>=55&&average>30&&quality!=='LOW'&&quality!=='REDUCED'){downgraded=quality==='HIGH'?'MEDIUM':'LOW';configure();samples=[]}
   }
   if(active)raf=requestAnimationFrame(paint)
  }
  function update(){cancelAnimationFrame(raf);last=0;configure();paint(performance.now())}
  repaint.current=()=>{cancelAnimationFrame(raf);last=0;paint(performance.now())}
  const move=(event:PointerEvent)=>{if(isStatic())return;const scale=Math.min(height*.30,width*.34);pointer.x=(event.clientX-width*.7)/scale;pointer.y=-(event.clientY-height*(.47+scroll*.025))/scale;hover=event.clientX>width*.42}
  const leave=()=>{hover=false}
  const lost=(event:Event)=>{event.preventDefault();cancelAnimationFrame(raf);el!.dataset.renderer='context-lost';el!.dataset.running='false'}
  const restored=()=>setContextVersion(value=>value+1)
  window.addEventListener('pointermove',move,{passive:true});document.addEventListener('pointerleave',leave);window.addEventListener('resize',update);document.addEventListener('visibilitychange',update);media?.addEventListener('change',update)
  el.addEventListener('webglcontextlost',lost);el.addEventListener('webglcontextrestored',restored)
  const observer=typeof IntersectionObserver!=='undefined'?new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting)scroll=Number((entry.target as HTMLElement).dataset.storyDepth??0)},{threshold:.2}):null
  document.querySelectorAll('[data-story-depth]').forEach(section=>observer?.observe(section));update()
  return()=>{cancelAnimationFrame(raf);meter.current.stop();observer?.disconnect();repaint.current=()=>{};if(gl){if(program)gl.deleteProgram(program);if(positionBuffer)gl.deleteBuffer(positionBuffer);if(styleBuffer)gl.deleteBuffer(styleBuffer)}window.removeEventListener('pointermove',move);document.removeEventListener('pointerleave',leave);window.removeEventListener('resize',update);document.removeEventListener('visibilitychange',update);media?.removeEventListener('change',update);el.removeEventListener('webglcontextlost',lost);el.removeEventListener('webglcontextrestored',restored)}
 },[enabled,contextVersion])
 return <canvas ref={canvas} className="story-particles" aria-hidden="true" data-state="IDLE"/>
}
