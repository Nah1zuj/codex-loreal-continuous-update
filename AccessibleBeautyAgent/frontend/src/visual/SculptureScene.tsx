import {useEffect,useRef,useState} from 'react'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshSurfaceSampler} from 'three/addons/math/MeshSurfaceSampler.js'
import {LocalAudioEnergy} from '../realtime/localAudioEnergy'
import {fineTopology} from './fineTopology'
import {refinePortrait} from './refinePortrait'
import {surfaceBudget} from './surfaceBudget'
import {ParametricGeometry} from 'three/addons/geometries/ParametricGeometry.js'
import {appleBites,carveApple} from './appleBites'
import {glassAppleMaterial} from './GlassAppleMaterial'
import {applePoint,seeded,pointerRotation,poseForRegion} from './geometry'
import {qualityLayers,sculptureField,type ParticleLayer} from './sculptureField'
import {StaticSculpture,type SceneProps} from './SectionBackground'

const vertex=`attribute vec3 velocity;attribute vec3 anchor;attribute float phase;attribute float particleSize;attribute float particleAlpha;attribute vec3 tint;
uniform float time;uniform float motion;uniform float energy;uniform float force;uniform vec2 pointer;uniform float pixelRatio;uniform float detailGain;uniform float flow;
varying vec3 vColor;varying float vAlpha;
void main(){vec3 p=position;float clock=time*.24;float fade=1.;
vec3 drift=vec3(sin(clock+phase),cos(clock*.73+phase*1.7),sin(clock*.91+phase*2.3));
if(flow<.5){p+=motion*(drift*.018+velocity*sin(time*.35+phase));}
else {p+=motion*(drift*(flow<2.5?.030:.055)+vec3(sin(p.y*2.+time*.17+phase),cos(p.x*1.8+time*.14+phase),sin(p.z*2.+time*.19+phase))*.026);
 if(flow>2.5&&flow<3.5){float travel=fract(time*.032+phase/6.283185);p=anchor+motion*velocity*(.12+travel*2.0)+motion*drift*.045;fade=mix(1.,sin(travel*3.14159),motion);}
 if(flow>3.5&&flow<4.5){float travel=fract((position.y-.6)/2.8+time*.025);p.y=mix(position.y,.6+travel*2.8,motion);fade=mix(1.,smoothstep(0.,.09,travel)*(1.-smoothstep(.83,1.,travel)),motion);}
 if(flow>4.5&&flow<5.5){p.x=mix(position.x,mod(position.x+2.3+time*.085,4.6)-2.3,motion);}
 if(flow>5.5&&flow<6.5){float a=motion*sin(time*.09+phase)*.025;mat2 rotation=mat2(cos(a),-sin(a),sin(a),cos(a));p.xy=rotation*p.xy;}
 if(flow>6.5&&flow<7.5){p.x=mix(position.x,mod(position.x+2.3+time*.065,4.6)-2.3,motion);p.y+=motion*sin(p.x*1.5-time*.32+phase)*.055;p.z+=motion*cos(p.x*1.2-time*.22+phase)*.05;}
}
p+=normalize(p+vec3(.001))*motion*(energy*.035+force*.012)*sin(time*1.1+phase);
vec4 world=modelMatrix*vec4(p,1.);float d=length(world.xy-pointer);
world.xy+=motion*normalize(world.xy-pointer+vec2(.001))*.075*exp(-d*d*3.);
vec4 mv=viewMatrix*world;gl_Position=projectionMatrix*mv;
gl_PointSize=clamp(particleSize*pixelRatio*detailGain*(flow>.5&&flow<1.5?2.0:flow>5.5&&flow<6.5?1.5:1.)*(10./max(3.,-mv.z)),.45,7.5);if(flow>6.5&&flow<7.5)gl_PointSize=max(2.0,gl_PointSize);vColor=tint;
float shimmer=flow<.5?1.:mix(1.,.78+.22*sin(time*1.1+phase*3.),motion);
vAlpha=particleAlpha*fade*shimmer;}`
const fragment=`precision mediump float;varying vec3 vColor;varying float vAlpha;uniform float opacity;uniform float glow;
void main(){float d=length(gl_PointCoord-.5);if(d>.5)discard;
float core=1.-smoothstep(.15,.5,d);float halo=exp(-d*d*16.);vec3 tone=mix(vColor,vec3(1.,.98,.91),glow*halo*.25);
gl_FragColor=vec4(tone,vAlpha*opacity*mix(core,halo,glow));}`
const flowMode:Record<ParticleLayer,number>={human:0,apple:1,slice:2,burst:3,plume:4,ambient:8,highlight:5,orbit:6,ribbon:7,satellite:1,fragment:2}
function cloud(layer:ParticleLayer,count:number){const field=sculptureField(layer,count),g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(field.position,3));g.setAttribute('anchor',new THREE.BufferAttribute(field.anchor,3));g.setAttribute('velocity',new THREE.BufferAttribute(field.velocity,3));g.setAttribute('phase',new THREE.BufferAttribute(field.phase,1));g.setAttribute('particleSize',new THREE.BufferAttribute(field.size,1));g.setAttribute('particleAlpha',new THREE.BufferAttribute(field.alpha,1));g.setAttribute('tint',new THREE.BufferAttribute(field.color,3));return new THREE.Points(g,new THREE.ShaderMaterial({vertexShader:vertex,fragmentShader:fragment,transparent:true,depthWrite:false,uniforms:{time:{value:0},motion:{value:0},energy:{value:0},force:{value:0},opacity:{value:1},detailGain:{value:1},flow:{value:flowMode[layer]},glow:{value:layer==='ribbon'||layer==='highlight'?1:0},pointer:{value:new THREE.Vector2(100,100)},pixelRatio:{value:1}}}))}

/** The visual sculpture is licensed anatomy, never a scan of the current user. */
export default function SculptureScene({variant,composition,appleArtwork=false,showHuman=true,enabled=true,state='idle',region='base',modelUrl,view,audioReactive=false,onAudioError}:SceneProps){
 const hostRef=useRef<HTMLDivElement>(null),latest=useRef({enabled,state,region}),meter=useRef(new LocalAudioEnergy()),redraw=useRef<(()=>void)|null>(null),[failed,setFailed]=useState(false)
 latest.current={enabled,state,region}
 useEffect(()=>{const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');if(audioReactive&&enabled&&state==='listening'&&!reduced.matches&&!document.hidden)void meter.current.start().catch(()=>onAudioError?.());else meter.current.stop();return()=>meter.current.stop()},[audioReactive,enabled,state])
 useEffect(()=>{redraw.current?.()},[enabled,state,region])
 useEffect(()=>{
  if(!hostRef.current)return;const host:HTMLDivElement=hostRef.current
  let renderer:THREE.WebGLRenderer;try{renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'high-performance'})}catch{setFailed(true);return}
  const mobile=window.innerWidth<768,tier=mobile?qualityLayers.low:qualityLayers.high,hero=variant==='hero',bust=variant==='full-look',scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-4,4,2.75,-2.75,.1,40),human=new THREE.Group(),apple=new THREE.Group()
  camera.position.set(0,0,12);renderer.setPixelRatio(Math.min(window.devicePixelRatio,mobile?1:1.5));renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;host.appendChild(renderer.domElement)
  scene.add(human,apple);human.visible=showHuman&&variant!=='apple'
  const satelliteForms=hero?[[.95,.85,.49,-.20,1],[-.55,1.1,.32,.23,1],[1.1,-.65,.36,-.35,1],[-1.08,-.48,.29,.55,.72],[.22,1.55,.24,-.38,1.30],[-1.18,1.25,.20,.68,.84],[.28,-1.18,.31,-.24,1.15]]:[[.95,.85,.49,-.20,1],[-.65,1.45,.32,.23,1],[1.48,-.78,.36,-.35,1]]
  const clouds:THREE.Points<THREE.BufferGeometry,THREE.ShaderMaterial>[]=[]
  if(hero||bust||variant==='apple'){
   for(const layer of ['apple','slice','burst','plume','ambient','orbit','ribbon','highlight','fragment'] as const){const object=cloud(layer,tier[layer]);object.name=layer;if(layer==='orbit'){object.rotation.z=.42;object.scale.y=1.4}if(layer==='fragment'){object.scale.set(.48,.56,.48);object.position.set(-.45,-.85,.8);object.rotation.set(.05,-.35,-.35)}if(layer==='ribbon')object.position.z=-2;if(layer==='ambient'){object.scale.set(2.3,1.25,1.4);object.position.z=-1.5}if(layer==='highlight')object.scale.set(2,1,1.6);clouds.push(object);apple.add(object)}
   for(const [i,[x,y,size,turn,stretch]] of satelliteForms.entries()){const count=Math.floor(tier.satellite/satelliteForms.length)+(i<tier.satellite%satelliteForms.length?1:0),object=cloud('satellite',count);object.name='satellite';object.scale.set(size/stretch,size*stretch,size);object.position.set(x,y,.03);object.rotation.z=turn;clouds.push(object);apple.add(object)}
  }
  if(!hero&&!bust&&variant!=='apple')for(const layer of ['ambient','orbit'] as const){const object=cloud(layer,mobile?800:3000);object.name=layer;clouds.push(object);scene.add(object)}
  const glassSurfaces:THREE.Mesh<THREE.BufferGeometry,THREE.ShaderMaterial>[]=[]
  if(hero&&!appleArtwork){
   const form=new ParametricGeometry((u,v,out)=>out.set(...applePoint(u*Math.PI*2,v*Math.PI)),mobile?40:88,mobile?28:64)
   for(const [index,[x,y,size,turn,stretch]] of [[0,0,1,.05,1],...satelliteForms].entries()){
    const geometry=new ParametricGeometry((u,v,out)=>out.set(...carveApple(applePoint(u*Math.PI*2,v*Math.PI),appleBites(index))),mobile?48:100,mobile?36:72);const shell=new THREE.Mesh(geometry,glassAppleMaterial(index*1.6));shell.position.set(x,y,.02);shell.scale.set(size/stretch,size*stretch,size);shell.rotation.z=turn;shell.renderOrder=0;glassSurfaces.push(shell);apple.add(shell)
   }
   form.dispose()
   for(const object of clouds.filter(p=>['apple','slice','satellite','fragment'].includes(p.name))){const satelliteIndex=clouds.filter(p=>p.name==='satellite').indexOf(object),bites=appleBites(object.name==='satellite'?satelliteIndex+1:0),positions=object.geometry.getAttribute('position');for(let i=0;i<positions.count;i++){const p=carveApple([positions.getX(i),positions.getY(i),positions.getZ(i)],bites);positions.setXYZ(i,...p)}positions.needsUpdate=true}
  }
  const stemPath=new THREE.CatmullRomCurve3([new THREE.Vector3(0,.70,0),new THREE.Vector3(-.05,.94,0),new THREE.Vector3(.08,1.13,-.05)]),stem=new THREE.Mesh(new THREE.TubeGeometry(stemPath,24,.031,8,false),new THREE.MeshStandardMaterial({color:'#855745',roughness:.9}));apple.add(stem);for(const [x,y,size,turn,stretch] of satelliteForms){const extraStem=stem.clone();extraStem.scale.set(size/stretch,size*stretch,size);extraStem.position.set(x,y,.03);extraStem.rotation.z=turn;apple.add(extraStem)}
  const trails=new THREE.Group();for(let ring=0;ring<3;ring++){const pts=Array.from({length:180},(_,i)=>{const a=i/179*Math.PI*2;return new THREE.Vector3(Math.cos(a)*(1.2+ring*.15),Math.sin(a)*(.48+ring*.12)+Math.cos(a)*.3,Math.sin(a)*.5)});trails.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:'#fff4df',transparent:true,opacity:.42,depthWrite:false})))}trails.rotation.z=.42;trails.scale.y=1.4;apple.add(trails)
  for(let strand=0;strand<2;strand++){const path=Array.from({length:160},(_,i)=>{const t=i/159;return new THREE.Vector3(.35+t*3.8,-.55+Math.sin(t*Math.PI)*.65+(strand-1)*.24+t*(strand===1?.75:0),.25+Math.cos(t*Math.PI)*.48)});apple.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(path),new THREE.LineBasicMaterial({color:strand?'#fff3dc':'#ddbca1',transparent:true,opacity:.18,depthWrite:false})))}
  if(appleArtwork)apple.traverse(object=>{if(object instanceof THREE.Mesh||object instanceof THREE.Line)object.visible=false})
  const lightLines=new THREE.Group();scene.add(lightLines)
  if(composition==='centered-home')for(let strand=0;strand<3;strand++){
   const points=Array.from({length:220},(_,i)=>{const t=i/219;return new THREE.Vector3(-1+t*2,-.65+Math.sin(t*Math.PI*2+strand*.65)*(.30+strand*.08)-strand*.26,-5.5)})
   const geometry=new THREE.BufferGeometry().setFromPoints(points);geometry.setAttribute('along',new THREE.Float32BufferAttribute(points.map((_,i)=>i/219),1))
   const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{time:{value:0},motion:{value:0},tint:{value:new THREE.Color(['#ed3154','#ef780e','#bb2454'][strand])}},vertexShader:`precision mediump float;attribute float along;varying float vAlong;uniform float time;uniform float motion;void main(){vAlong=along;vec3 p=position;p.y+=motion*sin(time*.22+along*6.283)*.025;gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.);}`,fragmentShader:`precision mediump float;varying float vAlong;uniform float time;uniform float motion;uniform vec3 tint;void main(){float edge=smoothstep(0.,.08,vAlong)*(1.-smoothstep(.92,1.,vAlong));float shine=.35+.65*pow(.5+.5*sin(vAlong*18.-time*.8*motion),6.);gl_FragColor=vec4(tint,edge*shine*.85);}`})
   lightLines.add(new THREE.Line(geometry,material))
  }
  const stone=new THREE.MeshPhysicalMaterial({color:'#c4a293',roughness:.72,metalness:.025,transparent:true,opacity:.52,side:THREE.FrontSide,depthWrite:true,clearcoat:.08,clearcoatRoughness:.88,emissive:'#c38e76',emissiveIntensity:.04})
  const key=new THREE.DirectionalLight('#fffaf5',2.1);key.position.set(-4,5,6);const rim=new THREE.DirectionalLight('#fff5ee',2.15);rim.position.set(4,2,-3);const rose=new THREE.DirectionalLight('#c9988b',.45);rose.position.set(-3,-2,4);scene.add(key,rim,rose,new THREE.HemisphereLight('#fff9f5','#c9b0a4',.65))
  let disposed=false,frame=0,active=true,last=0,elapsed=0,frames=0,quality=1,loaded=false,paintedRegion=""
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)'),pointer=new THREE.Vector2(100,100),rotationPointer={x:0,y:0}
  const dispose=(root:THREE.Object3D)=>root.traverse(o=>{const m=o as THREE.Mesh;m.geometry?.dispose();(Array.isArray(m.material)?m.material:[m.material]).forEach(a=>a?.dispose())})
  const localModel=modelUrl?.startsWith('/models/')?modelUrl:'/models/human.glb'
  if(showHuman)new GLTFLoader().load(localModel,gltf=>{
   if(disposed){dispose(gltf.scene);return}
   gltf.scene.updateMatrixWorld(true);const meshes:THREE.Mesh[]=[];gltf.scene.traverse(o=>{if(o instanceof THREE.Mesh)meshes.push(o)})
   const bounds=new THREE.Box3().setFromObject(gltf.scene),center=bounds.getCenter(new THREE.Vector3()),height=bounds.getSize(new THREE.Vector3()).y,scale=2.9/height
   const meshWeights=meshes.map(m=>m.geometry.getAttribute('position').count),counts=surfaceBudget(tier.human,meshWeights),mediumCounts=surfaceBudget(qualityLayers.medium.human,meshWeights),lowCounts=surfaceBudget(qualityLayers.low.human,meshWeights)
   for(const [meshIndex,source] of meshes.entries()){const surfaceCount=counts[meshIndex];const geometry=source.geometry.clone().applyMatrix4(source.matrixWorld);geometry.translate(-center.x,-center.y,-center.z);geometry.scale(scale,scale,scale);if(localModel==='/models/human.glb')refinePortrait(geometry);else geometry.computeVertexNormals();const depthMask=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({colorWrite:false,depthWrite:true,side:THREE.FrontSide}));depthMask.renderOrder=-1;human.add(depthMask);const mesh=new THREE.Mesh(geometry,stone);mesh.renderOrder=1;human.add(mesh)
    const coarse=fineTopology(geometry),topology=mobile?coarse:fineTopology(coarse);if(!mobile)coarse.dispose();const wirePosition=topology.getAttribute('position'),wireNormal=topology.getAttribute('normal');for(let i=0;i<wirePosition.count;i++)wirePosition.setXYZ(i,wirePosition.getX(i)+wireNormal.getX(i)*.003,wirePosition.getY(i)+wireNormal.getY(i)*.003,wirePosition.getZ(i)+wireNormal.getZ(i)*.003);const wire=new THREE.LineSegments(new THREE.WireframeGeometry(topology),new THREE.LineBasicMaterial({color:'#eed5c7',transparent:true,opacity:.24,depthWrite:false}));topology.dispose();wire.scale.setScalar(1);wire.renderOrder=3;human.add(wire)
    const weights=new Float32Array(geometry.getAttribute('position').count);const surface=geometry.getAttribute('position');for(let i=0;i<weights.length;i++){const x=surface.getX(i),y=surface.getY(i);weights[i]=.18+.65*Math.exp(-((Math.abs(x)-.55)**2)/.055)+.35*Math.exp(-((y+.65)**2)/.06)}geometry.setAttribute('beautyDensity',new THREE.BufferAttribute(weights,1));
    const sample=cloud('human',surfaceCount),sampler=(new MeshSurfaceSampler(mesh) as MeshSurfaceSampler & {setRandomGenerator:(r:()=>number)=>MeshSurfaceSampler}).setRandomGenerator(seeded(910)).setWeightAttribute('beautyDensity').build(),p=new THREE.Vector3(),normal=new THREE.Vector3(),surfaceRandom=seeded(2110),positions=new Float32Array(surfaceCount*3),colors=sample.geometry.getAttribute('tint')
    for(let i=0;i<surfaceCount;i++){sampler.sample(p,normal);positions.set([p.x+normal.x*.004,p.y+normal.y*.004,p.z+normal.z*.004],i*3);normal.applyEuler(human.rotation);const edge=1-Math.abs(normal.z),light=i%50===0;colors.setXYZ(i,light?1:.94,light?.96:.78,light?.85:.66);(sample.geometry.getAttribute('particleSize') as THREE.BufferAttribute).setX(i,light?1.7+surfaceRandom():.35+surfaceRandom()*.65);(sample.geometry.getAttribute('particleAlpha') as THREE.BufferAttribute).setX(i,light?.88:.12+edge*.43)}sample.geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));sample.name='human';sample.userData.mediumCount=mediumCounts[meshIndex];sample.userData.lowCount=lowCounts[meshIndex];sample.renderOrder=2;clouds.push(sample);human.add(sample)
   }
   if(bust){const body=new ParametricGeometry((u,v,out)=>{const y=-1.30-v*1.65,r=.34+1.2*Math.sin(v*Math.PI*.62);out.set(Math.sin(u*Math.PI*2)*r,y,Math.cos(u*Math.PI*2)*(.28+v*.30)-.18)},100,50);human.add(new THREE.Mesh(body,stone),new THREE.LineSegments(new THREE.WireframeGeometry(body),new THREE.LineBasicMaterial({color:'#fff6e5',transparent:true,opacity:.20})))}
   loaded=true;host.dataset.model='LeePerrySmith-CC-BY-3';host.dataset.wireSubdivision=mobile?'1':'2';host.dataset.portraitMaterial='pearl-champagne';host.dataset.portraitShape=localModel==='/models/human.glb'?'sculpted-derivative':'custom-model';restart()
  },undefined,()=>{if(!disposed){setFailed(true);host.dataset.model='unavailable'}})
  if(!showHuman){loaded=true;host.dataset.model='reference-image-layer'}
  function layout(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);if(window.innerWidth<768){for(const field of clouds)field.geometry.setDrawRange(0,Math.min(field.geometry.getAttribute('position').count,field.parent===human?field.userData.lowCount:field.name==='satellite'?Math.floor(qualityLayers.low.satellite/satelliteForms.length):qualityLayers.low[field.name as ParticleLayer]));renderer.setPixelRatio(1);host.dataset.quality='low'}const half=hero?2.6:bust?2.5:variant==='voice'?1.55:1.95;camera.top=half;camera.bottom=-half;camera.left=-half*w/h;camera.right=half*w/h;camera.updateProjectionMatrix()
   human.position.set(hero?camera.right*.80:0,hero?.65:bust?1.05:variant==='voice'?-.32:variant==='makeup'?-.55:0,0);human.scale.setScalar(hero?1.75:bust?1.65:variant==='voice'||variant==='makeup'?2.0:1.2)
   apple.position.set(hero?camera.right*(composition==='centered-home'?-.62:.34):bust?-.82:-1.48,hero?(composition==='centered-home'?.85:-.1):bust?-.8:-.48,-4.5);apple.scale.set(hero?.74:bust?.68:.40,hero?.90:bust?.68:.40,hero?.82:bust?.68:.40);apple.visible=hero||bust||variant==='apple';for(const field of clouds){if(['ambient','ribbon','orbit'].includes(field.name)){scene.add(field);field.visible=hero||bust||variant==='apple'||!showHuman;if(field.name==='orbit'){field.position.set(human.position.x,human.position.y,-5);field.scale.set(hero?1.20:1,hero?2.05:1.5,1)}else{field.position.set(0,field.name==='ribbon'?.15:0,field.name==='ribbon'?-6:-6.5);field.scale.set(camera.right/2.3,1,1)}}}
   lightLines.scale.x=camera.right;restart()
  }
  function render(now:number){if(disposed||!active||document.hidden)return;const curr=latest.current,moving=curr.enabled&&!motion.matches,time=moving?now/1000:0,delta=last?(now-last)/1000:0;last=now
   const pose=variant==='makeup'?poseForRegion(curr.region):[view==='up'?-.16:view==='down'?.12:hero?-.30:bust?-.20:0,hero?-.95:bust?-.65:view==='left'?-1.1:view==='right'?1.1:-.55,0],pr=moving?pointerRotation(rotationPointer.x,rotationPointer.y):[0,0,0]
   human.rotation.set(pose[0]+pr[0],pose[1]+pr[1],0);human.position.y=(hero?.65:bust?1.05:variant==='voice'?-.32:variant==='makeup'?-.55:0)+(moving?Math.sin(time*.66)*.008:0)
   if(variant==='makeup'&&paintedRegion!==curr.region){for(const field of clouds.filter(p=>p.parent===human)){const pos=field.geometry.getAttribute('position'),tint=field.geometry.getAttribute('tint');for(let i=0;i<pos.count;i++){const x=Math.abs(pos.getX(i)),y=pos.getY(i),front=pos.getZ(i)>.35,inside=front&&(curr.region==='blush'?x>.28&&x<.68&&y>-.2&&y<.24:curr.region==='lips'?x<.28&&y>-.55&&y<-.25:curr.region==='eyes'?x>.17&&x<.60&&y>.3&&y<.55:false);tint.setXYZ(i,inside?.80:.92,inside?.43:.78,inside?.40:.68)}tint.needsUpdate=true}paintedRegion=curr.region}
   const energy=moving?meter.current.read():0,force=curr.state==='listening'?-1:curr.state==='thinking'?.35:curr.state==='speaking'?1:0
   stone.opacity=curr.state==='listening'?.22:hero?.76:.72
   for(const shell of glassSurfaces){shell.material.uniforms.time.value=time;shell.material.uniforms.motion.value=moving?1:0}
   for(const cloud of clouds){const u=cloud.material.uniforms;u.time.value=time;u.motion.value=moving?1:0;u.energy.value=energy;u.force.value=force;u.pointer.value.copy(pointer);u.pixelRatio.value=renderer.getPixelRatio();u.detailGain.value=cloud.parent===human?1:Math.min(2.6,Math.sqrt(cloud.geometry.getAttribute('position').count/Math.min(cloud.geometry.drawRange.count,cloud.geometry.getAttribute('position').count)));u.opacity.value=hero&&['apple','satellite','slice','fragment','burst','plume'].includes(cloud.name)?(cloud.name==='plume'?.26:cloud.name==='burst'?.40:.20):cloud.parent===human?.8:cloud.name==='slice'||cloud.name==='fragment'?.90:cloud.name==='ribbon'?.95:cloud.name==='burst'?.74:cloud.name==='ambient'?.72:cloud.name==='plume'?.34:cloud.name==='satellite'||cloud.name==='apple'?.86:cloud.name==='orbit'?.84:bust?.38:.68}
   for(const line of lightLines.children){const uniforms=(line as THREE.Line<THREE.BufferGeometry,THREE.ShaderMaterial>).material.uniforms;uniforms.time.value=time;uniforms.motion.value=moving?1:0}
   renderer.render(scene,camera);host.dataset.motion=moving?'gentle':'static';host.dataset.particleTime=time.toFixed(3);host.dataset.appleForms=apple.visible?String(satelliteForms.length+2):'0';host.dataset.appleMaterial=appleArtwork?'supplied-apple-artwork':hero?'rippled-glass-frosted-gradient':'particles';host.dataset.state=curr.state;host.dataset.pose=human.rotation.y.toFixed(3);host.dataset.particles=String(clouds.reduce((n,p)=>n+(p.visible&&p.parent?.visible?Math.min(p.geometry.drawRange.count,p.geometry.getAttribute('position').count):0),0));host.dataset.layers=JSON.stringify(clouds.reduce<Record<string,number>>((counts,p)=>{const key=p.parent===human?'human':p.name;counts[key]=(counts[key]??0)+(p.visible&&p.parent?.visible?Math.min(p.geometry.drawRange.count,p.geometry.getAttribute('position').count):0);return counts},{}));host.dataset.loaded=String(loaded)
   if(moving&&delta>0&&delta<.25){host.dataset.sampling='contiguous';elapsed+=delta;frames++;if(elapsed>3){const fps=frames/elapsed;host.dataset.fps=fps.toFixed(1);host.dataset.frameMs=(1000/fps).toFixed(1);if(fps<38&&quality>.2&&!mobile){quality=quality===1?.45:.2;const budget=quality===.45?qualityLayers.medium:qualityLayers.low;for(const p of clouds)p.geometry.setDrawRange(0,p.parent===human?(quality===.45?p.userData.mediumCount:p.userData.lowCount):p.name==='satellite'?Math.floor(budget.satellite/satelliteForms.length):budget[p.name as ParticleLayer]);renderer.setPixelRatio(1);host.dataset.quality=quality===.45?'medium':'low'}elapsed=0;frames=0}}
   if(delta>=.25){elapsed=0;frames=0;host.dataset.sampling='insufficient-contiguous-samples';delete host.dataset.fps;delete host.dataset.frameMs}
   if(moving)frame=requestAnimationFrame(render)
  }
  function restart(){cancelAnimationFrame(frame);last=0;render(performance.now())}redraw.current=restart
  const resize=new ResizeObserver(layout);resize.observe(host)
  const visibility=new IntersectionObserver(entries=>{active=entries.some(e=>e.isIntersecting);if(active)restart();else cancelAnimationFrame(frame)});visibility.observe(host)
  const hide=()=>{meter.current.stop();restart()},reduce=()=>{if(motion.matches)meter.current.stop();restart()};document.addEventListener('visibilitychange',hide);motion.addEventListener('change',reduce)
  const section=host.closest('section,article')??host.parentElement,onMove=(event:Event)=>{const e=event as PointerEvent,r=host.getBoundingClientRect();rotationPointer.x=(e.clientX-r.left)/r.width*2-1;rotationPointer.y=(e.clientY-r.top)/r.height*2-1;pointer.set(rotationPointer.x*camera.right,-rotationPointer.y*camera.top)},onLeave=()=>{pointer.set(100,100);rotationPointer.x=0;rotationPointer.y=0}
  section?.addEventListener('pointermove',onMove);section?.addEventListener('pointerleave',onLeave);layout()
  return()=>{disposed=true;redraw.current=null;cancelAnimationFrame(frame);resize.disconnect();visibility.disconnect();document.removeEventListener('visibilitychange',hide);motion.removeEventListener('change',reduce);section?.removeEventListener('pointermove',onMove);section?.removeEventListener('pointerleave',onLeave);dispose(scene);renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove()}
 },[variant,modelUrl,view,composition,showHuman,appleArtwork])
 return <div ref={hostRef} className="sculpture-canvas" data-visual={variant}>{failed&&showHuman?<StaticSculpture/>:null}</div>
}
