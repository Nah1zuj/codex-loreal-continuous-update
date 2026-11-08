/** GPU point budget is real draw count, not a marketing estimate. */
export function particleBudget(width:number,reduced=false){return reduced?32768:width<760?131072:1048576}
export function localRipple(x:number,y:number,px:number,py:number,time:number,energy:number){
 const distance=Math.hypot(x-px,y-py)
 return Math.exp(-distance*distance*16)*Math.sin(distance*24-time*3)*(.018+energy*.075)
}
export function makeApplePoints(count:number){const points=new Float32Array(count*4);for(let i=0;i<count;i++){const a=(i*.61803398875)%1,b=(i*.754877666)%1,yy=b*2-1,r=Math.sqrt(1-yy*yy),theta=a*Math.PI*2;let x=r*Math.cos(theta)*(.88+.1*Math.cos(yy*3)),y=yy-.1*Math.exp(-x*x*25)*Math.max(0,(yy-.5)*2),z=r*Math.sin(theta);const part=(i*.569840291)%1;if(part>.985){x=.02+(b-.5)*.045;y=1+a*.25;z=0}else if(part>.96){x=.05+a*.46;y=1.15+Math.sin(a*Math.PI)*.13;z=(b-.5)*.04}const slot=(i*.43857921)%1;points.set([x,y,z,slot],i*4)}return points}
export const appleVertex=`#version 300 es
precision highp float;
layout(location=0) in vec4 aPoint;
uniform vec2 uSize;uniform vec2 uPointer;uniform float uTime;uniform float uEnergy;uniform float uMotion;
out float vLight;out float vAlpha;out float vKind;out vec2 vCoord;
void main(){
 float x=aPoint.x,y=aPoint.y,z=aPoint.z;vec2 center=vec2(.76,.40);float scale=min(uSize.y*.33,uSize.x*.23);
 bool slice=aPoint.w>.52;
 if(slice){center=vec2(.64,.94);scale*=1.25;z=abs(z)*.2;}
 vKind=slice?1.0:0.0;vCoord=vec2(x,y);
 vec2 pos=center*uSize+vec2(x,-y)*scale;
 float distance=length((pos-uPointer)/max(scale,1.0));float local=exp(-distance*distance*10.0);
 float wave=sin(distance*22.0-uTime*3.0)*local*(12.0+uEnergy*35.0);
 pos+=vec2(x,y)*(wave+sin(uTime*3.2+y*7.0)*uEnergy*scale*.055)*uMotion;
 pos.y+=sin(uTime*.7+x*3.0)*3.0*uMotion;
 gl_Position=vec4(pos/uSize*vec2(2.0,-2.0)+vec2(-1.0,1.0),0.0,1.0);
 gl_PointSize=1.25+(local*.9+uEnergy*.5)*uMotion;
 vLight=clamp(.35+z*.4+y*.16,0.0,1.0);vAlpha=(.36+.35*max(z,0.0))*(1.0+local*.7*uMotion);
 if(slice){vLight=.82;vAlpha=.28;}
 if(slice&&y>1.0){gl_Position=vec4(2.0,2.0,0.0,1.0);vAlpha=0.0;}
 if(aPoint.w>.92){
   vKind=2.0;vec2 curtain=vec2((x+1.0)*.5*uSize.x,(y+1.0)*.5*uSize.y);
   curtain.x+=sin(y*9.0+uTime*.45)*35.0*uMotion;
   float near=exp(-pow(length((curtain-uPointer)/max(scale,1.0)),2.0)*5.0);
   curtain+=vec2(sin(uTime*2.0+y*8.0),cos(uTime+x*7.0))*near*22.0*uMotion;
   gl_Position=vec4(curtain/uSize*vec2(2.0,-2.0)+vec2(-1.0,1.0),0.0,1.0);
   gl_PointSize=.8+near*uMotion;vAlpha=.1;
 }
}`
export const appleFragment=`#version 300 es
precision highp float;
in float vLight;in float vAlpha;in float vKind;in vec2 vCoord;out vec4 color;
void main(){float d=length(gl_PointCoord-.5);
 vec3 red=mix(vec3(.45,.04,.07),vec3(.97,.29,.18),vLight);
 if(vKind==1.0){
   float radius=length(vCoord);
   red=mix(vec3(1.0,.80,.52),vec3(.95,.30,.38),smoothstep(.15,.96,radius));
   if(radius>.93)red=vec3(.64,.02,.07);
   float seed1=length((vCoord-vec2(-.12,.02))*vec2(9.0,5.0));
   float seed2=length((vCoord-vec2(.12,-.04))*vec2(9.0,5.0));
   if(min(seed1,seed2)<1.0)red=mix(vec3(.18,.025,.025),vec3(.47,.07,.09),min(seed1,seed2));
 }
 if(vKind==2.0)red=vec3(.72,.06,.12);
 color=vec4(red,vAlpha*(1.0-smoothstep(.32,.5,d)));}
`
