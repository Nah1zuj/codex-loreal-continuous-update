import {seeded,applePoint} from './geometry'
// Adaptive budgets; preserve deterministic seeds across visual refinements.
export const qualityLayers={high:{apple:90000,plume:35000,human:45000,ambient:40000,orbit:5000,highlight:5000,slice:25000,burst:10000,ribbon:60000,satellite:8001,fragment:1999},medium:{apple:14000,plume:11000,human:18000,ambient:14000,orbit:4000,highlight:1000,slice:8000,burst:9000,ribbon:6000,satellite:5000,fragment:3000},low:{apple:2600,plume:1600,human:3500,ambient:2600,orbit:700,highlight:400,slice:1600,burst:1400,ribbon:2200,satellite:1000,fragment:600}} as const
export type ParticleLayer=keyof typeof qualityLayers.high
export function sculptureField(layer:ParticleLayer,count:number){
 const r=seeded(721+Object.keys(qualityLayers.high).indexOf(layer)),position=new Float32Array(count*3),anchor=new Float32Array(count*3),velocity=new Float32Array(count*3),phase=new Float32Array(count),size=new Float32Array(count),alpha=new Float32Array(count),color=new Float32Array(count*3)
 for(let i=0;i<count;i++){
  let x=0,y=0,z=0,seed=false,rim=false
  if(layer==='apple'||layer==='satellite'){
   const u=r()*Math.PI*2,v=Math.acos(r()*2-1),surface=applePoint(u,v),radius=i%5===0?Math.cbrt(r()):.96+r()*.04
   ;[x,y,z]=surface.map(a=>a*radius)
   // Open a slanted front section, without removing the whole silhouette.
   if(layer==='apple'&&z>.34-x*.23){z=.34-x*.23}
   if(x<-.5&&y>.1&&i%9===0){x-=r()*.22;y+=r()*.32}
  }else if(layer==='slice'||layer==='fragment'){
   const angle=r()*Math.PI*2,rad=Math.sqrt(r()),lobe=1+.035*Math.cos(angle*5)
   rim=rad>.88;x=Math.cos(angle)*rad*.87*lobe;y=Math.sin(angle)*rad*.76
   y-=.07*Math.exp(-((x/.18)**2))*Math.max(0,y)
   z=.37-x*.23+(r()-.5)*.018
   // Small seed pockets and a fine core, not a photographic fruit painting.
   if(i%13===0){const side=i%2?1:-1;x=side*.13+(r()-.5)*.075;y=-.08+(r()-.5)*.20;seed=true}
  }else if(layer==='burst'){
   const u=r()*Math.PI*2,v=Math.acos(r()*2-1),p=applePoint(u,v)
   x=p[0];y=p[1];z=p[2]
  }else if(layer==='plume'){
   const t=r(),width=.08+.22*Math.sin(t*Math.PI)+.08*Math.sin(t*19)
   x=Math.sin(t*9)*.16+(r()+r()+r()-1.5)*width;y=.6+t*2.8;z=(r()-.5)*.6
   if(i%7===0)x+=Math.sin(t*15)*.65
  }else if(layer==='ribbon'){
   const t=r(),strand=i%3
   x=-2.3+t*4.6;y=-.45+Math.sin(t*Math.PI*2)*.38+(strand-1)*.26;z=.25+Math.cos(t*Math.PI)*.48
   x+=(r()-.5)*.03;y+=(r()+r()-1)*.035;z+=(r()-.5)*.05
  }else if(layer==='orbit'){
   const t=r()*Math.PI*2,ring=i%3
   x=Math.cos(t)*(1.2+ring*.15);y=Math.sin(t)*(.48+ring*.12)+Math.cos(t)*.3;z=Math.sin(t)*.5
   x+=(r()-.5)*.025;y+=(r()-.5)*.018
  }else if(layer==='ambient'){
   const band=i%10
   if(band<5){x=(i%2?1:-1)*(1.72+r()*.55);y=(Math.floor(i/2)%2?1:-1)*(1.68+r()*.8)}
   else if(band<8){const t=r(),strand=i%3;x=-2.3+t*4.6;y=-.45+Math.sin(t*Math.PI*2)*.38+(strand-1)*.26+(r()-.5)*.18}
   else{x=(r()-.5)*4.6;y=(r()-.5)*5}
   z=(r()-.5)*2.6
  }else{x=(r()-.5)*4.6;y=(r()-.5)*5;z=(r()-.5)*2.6}
  position.set([x,y,z],i*3);anchor.set([x,y,z],i*3)
  if(layer==='burst'){const length=Math.hypot(x,y,z)||1,speed=.55+r()*.9;velocity.set([x/length*speed,y/length*speed*.8,z/length*speed],i*3)}
  else velocity.set([(r()-.5)*.02,.008+r()*.012,(r()-.5)*.01],i*3)
  phase[i]=r()*Math.PI*2
  const distribution=r();size[i]=distribution<.70?.4+r()*.6:distribution<.93?1+r():distribution<.99?2+r()*1.5:3.5+r()*2.5
  alpha[i]=layer==='ambient'?.30+r()*.30:layer==='plume'?.23+r()*.5:.35+r()*.55
  const warm=r(),bright=layer==='highlight'||layer==='orbit'||r()>.9
  if(layer==='slice'||layer==='fragment')color.set(seed?[.38,.20,.14]:rim?[.73,.37,.28]:layer==='fragment'?[.96,.79+warm*.05,.68+warm*.10]:[.97,.87+warm*.07,.74+warm*.14],i*3)
  else if(layer==='orbit')color.set([.67+warm*.10,.27+warm*.08,.23+warm*.07],i*3)
  else if(layer==='ambient')color.set(i%3===0?[.72,.36,.31]:[.82+warm*.10,.60+warm*.09,.43+warm*.12],i*3)
  else if(layer==='apple'||layer==='satellite')color.set(bright?[.92,.68,.55]:[.48+warm*.15,.17+warm*.14,.13+warm*.10],i*3)
  else if(layer==='ribbon')color.set(i%5===0?[.71,.48,.38]:[.77+warm*.08,.55+warm*.08,.37+warm*.12],i*3)
  else if(layer==='burst')color.set(i%3===0?[.97,.86,.76]:[.72+warm*.20,.44+warm*.25,.36+warm*.22],i*3)
  else color.set(bright?[.97,.86,.73]:[.42+warm*.28,.19+warm*.22,.14+warm*.17],i*3)
 }
 return {position,anchor,velocity,phase,size,alpha,color}
}
