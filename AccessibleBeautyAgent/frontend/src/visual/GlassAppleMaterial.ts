import * as THREE from 'three'

/** Original procedural art material: rippled glass + frosted colour grain.
 * This is stylised translucency, not a screen-space refraction pass. */
export function glassAppleMaterial(offset=0){
 return new THREE.ShaderMaterial({
  transparent:true,depthWrite:false,side:THREE.FrontSide,
  uniforms:{time:{value:0},motion:{value:0},offset:{value:offset}},
  vertexShader:`
   varying vec3 vPosition;varying vec3 vNormal;varying vec3 vEye;
   void main(){vPosition=position;vNormal=normalize(normalMatrix*normal);
    vec4 eye=modelViewMatrix*vec4(position,1.);vEye=-eye.xyz;
    gl_Position=projectionMatrix*eye;}`,
  fragmentShader:`
   precision highp float;
   varying vec3 vPosition;varying vec3 vNormal;varying vec3 vEye;
   uniform float time;uniform float motion;uniform float offset;
   float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
   void main(){
    vec3 p=vPosition;float t=time*motion*.12;
    float bend=sin(p.y*2.1+p.x*1.8+t)*.16;
    float ridges=sin((p.x+bend)*68.+p.y*3.);
    vec3 n=normalize(vNormal+vec3(ridges*.055,sin(p.y*53.+p.x*8.)*.025,0.));
    vec3 eye=normalize(vEye);float edge=pow(1.-max(dot(n,eye),0.),2.2);
    vec3 rose=vec3(.98,.36,.39),amber=vec3(1.,.69,.24);
    vec3 green=vec3(.64,.79,.37),blue=vec3(.65,.82,.87);
    float gradient=sin(p.x*1.4+p.y*1.7+offset+t*.35)*.5+.5;
    vec3 pigment=mix(rose,amber,smoothstep(.1,.8,gradient));
    pigment=mix(pigment,green,smoothstep(.05,.9,-p.y*.55+p.x*.24+offset*.1));
    pigment=mix(pigment,blue,smoothstep(.4,1.2,p.y+p.x*.35)*.40);
    float key=pow(max(dot(reflect(-normalize(vec3(-.8,1.3,2.)),n),eye),0.),44.);
    float broad=pow(max(dot(n,normalize(vec3(-.4,.8,1.))),0.),3.);
    float grain=hash(floor(p*720.))-.5;
    vec3 tone=mix(vec3(.99,.95,.88),pigment,.54+edge*.16);
    tone+=grain*.07+vec3(ridges*.025)+vec3(key*.65+broad*.12);
    tone=mix(tone,vec3(1.,.98,.93),edge*.55);
    gl_FragColor=vec4(tone,.62+edge*.30);
   }`,
 })
}
