export type StoryState='IDLE'|'HOVER'|'LISTENING'|'THINKING'|'SPEAKING'|'TRANSITIONING'|'REDUCED_MOTION'
export type QualityName='HIGH'|'MEDIUM'|'LOW'|'REDUCED'
export function storyQuality(width:number,reduced:boolean):{name:QualityName;count:number}{return reduced?{name:'REDUCED',count:1200}:width<600?{name:'LOW',count:1800}:width<1000?{name:'MEDIUM',count:6000}:{name:'HIGH',count:12000}}
export function pointerForce(x:number,y:number,px:number,py:number):[number,number]{
 const dx=x-px,dy=y-py,d=Math.hypot(dx,dy),radius=.42
 if(d>=radius)return [0,0]
 const falloff=(1-d/radius)**2*.65/Math.max(d,.035)
 return [dx*falloff,dy*falloff]
}
/** Independent damped stochastic points; no shared wave or mesh. Units are local
 * scene units and seconds. Fixed seed makes stability regressions reproducible. */
export class StoryField {
 readonly position:Float32Array;readonly velocity:Float32Array;readonly acceleration:Float32Array
 readonly target:Float32Array;readonly home:Float32Array;readonly style:Float32Array
 private seed:number;private gather=0
 constructor(readonly count:number,seed=8191){
  this.seed=seed;this.position=new Float32Array(count*3);this.home=new Float32Array(count*3)
  this.velocity=new Float32Array(count*3);this.acceleration=new Float32Array(count*3);this.target=new Float32Array(count*3);this.style=new Float32Array(count*4)
  for(let i=0;i<count;i++){
   const p=i*3,angle=this.random()*Math.PI*2,radius=Math.sqrt(this.random()),layer=this.random()
   this.home[p]=Math.cos(angle)*radius*1.8+(this.random()-.5)*.32
   this.home[p+1]=Math.sin(angle)*radius*1.55+(this.random()-.5)*.22
   this.home[p+2]=layer*1.6-.8
   // Original apple silhouette with an inset top and a narrow open seam,
   // shared with the TRACE engraved symbol, not a corporate bitten logo.
   const theta=this.random()*Math.PI*2,depth=this.random()*2-1,ring=Math.sqrt(1-depth*depth)
   const x=Math.sin(theta)*.80*ring
   this.target[p]=x
   this.target[p+1]=Math.cos(theta)*.84*ring-.14*Math.exp(-x*x/.04)*Math.max(0,Math.cos(theta))
   this.target[p+2]=depth*.44
   if(i%30===0){this.target[p]=.02+this.random()*.15;this.target[p+1]=.76+this.random()*.29;this.target[p+2]=.02}
   this.position.set(this.home.subarray(p,p+3),p)
   this.style[i*4]=this.random();this.style[i*4+1]=layer
   this.style[i*4+2]=.70+this.random()*1.6+(layer>.85?.8:0);this.style[i*4+3]=.30+this.random()*.46
  }
 }
 private random(){this.seed=(Math.imul(this.seed,1664525)+1013904223)>>>0;return this.seed/4294967296}
 step(seconds:number,state:StoryState,energy:number,pointer:{x:number;y:number}|null){
  if(state==='REDUCED_MOTION'||seconds<=0)return
  const dt=Math.min(seconds,1/30),gatherTarget=state==='LISTENING'?1:state==='THINKING'?.65:state==='SPEAKING'?.8:0
  this.gather+=(gatherTarget-this.gather)*(1-Math.exp(-dt*1.7))
  const damping=Math.exp(-2.1*dt),sigma=.13*Math.sqrt(dt),rms=Math.min(1,Math.max(0,energy))
  for(let i=0;i<this.count;i++){
   const p=i*3,shaped=i%5!==0?this.gather:0
   const [fx,fy]=pointer?pointerForce(this.position[p],this.position[p+1],pointer.x,pointer.y):[0,0]
   for(let axis=0;axis<3;axis++){
    const index=p+axis,goal=this.home[index]*(1-shaped)+this.target[index]*shaped
    // A small individual orbit expresses processing; speech animation has no
    // fabricated audio envelope. Only local measured input changes sigma.
    const orbit=state==='THINKING'?(axis===0?-this.position[p+1]:axis===1?this.position[p]:0)*.07:0
    const force=(goal-this.position[index])*(.28+shaped*2.4)+orbit+(axis===0?fx:axis===1?fy:0)
    this.acceleration[index]=force
    const noise=(this.random()+this.random()+this.random()-1.5)*2
    const velocity=Math.max(-.65,Math.min(.65,this.velocity[index]*damping+force*dt+sigma*noise*(1+rms*1.3)))
    this.velocity[index]=velocity
    const limit=axis===0?2.6:axis===1?1.9:1
    this.position[index]=Math.max(-limit,Math.min(limit,this.position[index]+velocity*dt))
   }
  }
 }
}

export const storyVertex=`
attribute vec3 aPosition;
attribute vec4 aStyle;
uniform vec2 uSize;
uniform float uDpr;
uniform float uScroll;
varying vec4 vColor;
void main(){
 float perspective=1.0/(1.0+aPosition.z*.22);
 float scale=min(uSize.y*.30,uSize.x*.34);
 vec2 center=vec2(uSize.x*.70,uSize.y*(.47+uScroll*.025));
 vec2 point=center+vec2(aPosition.x,-aPosition.y)*scale*perspective;
 gl_Position=vec4(point/uSize*2.0-1.0,0.0,1.0);
 gl_Position.y=-gl_Position.y;
 gl_PointSize=clamp(aStyle.z*perspective*uDpr,1.0,3.1*uDpr);
 vec3 wine=vec3(.396,.118,.173),ruby=vec3(.702,.290,.349),copper=vec3(.737,.518,.459);
 vec3 color=aStyle.x<.6?mix(wine,ruby,aStyle.x/ .6):mix(ruby,copper,(aStyle.x-.6)/.4);
 // Keep the main reading column quiet without obscuring it with a panel.
 float clearText=smoothstep(.26,.55,point.x/uSize.x);
 vColor=vec4(color,aStyle.w*(.60+aStyle.y*.40)*clearText);
}`
export const storyFragment=`
precision mediump float;
varying vec4 vColor;
void main(){float radius=length(gl_PointCoord-.5);if(radius>.5)discard;
 float edge=1.0-smoothstep(.27,.5,radius);gl_FragColor=vec4(vColor.rgb,vColor.a*edge);
}`
