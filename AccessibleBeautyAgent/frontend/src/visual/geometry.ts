/** Original TRACE geometry. No scan, biometric data or third-party model. */
export type Vec3 = [number,number,number]
const bell=(v:number,c:number,w:number)=>Math.exp(-(((v-c)/w)**2))
export function facePoint(u:number,v:number):Vec3 {
  const y=Math.cos(v)*1.42, s=Math.sin(v)
  const jaw=1-.17*bell(y,-1.03,.40)-.045*bell(y,.65,.5)
  const x=Math.sin(u)*s*.92*jaw
  let z=Math.cos(u)*s*.82
  if(Math.cos(u)>0){
    const front=Math.pow(Math.cos(u),5)
    const nose=.24*bell(x,0,.10)*bell(y,.14,.40)+.22*bell(x,0,.14)*bell(y,-.09,.12)+.055*(bell(x,.13,.05)+bell(x,-.13,.05))*bell(y,-.13,.06)
    const sockets=-.10*(bell(x,.33,.19)+bell(x,-.33,.19))*bell(y,.27,.13)
    const lids=.045*(bell(x,.33,.18)+bell(x,-.33,.18))*bell(y,.22,.035)
    const brows=.047*(bell(x,.32,.22)+bell(x,-.32,.22))*bell(y,.43,.08)
    const cupid=-.45+.017*bell(x,0,.055)-.009*(bell(x,.08,.04)+bell(x,-.08,.04))
    const lips=.075*bell(x,0,.24)*bell(y,cupid,.035)+.085*bell(x,0,.23)*bell(y,-.53,.047)-.03*bell(x,0,.24)*bell(y,-.485,.012)
    const cheeks=.085*(bell(x,.49,.24)+bell(x,-.49,.24))*bell(y,-.02,.21)
    const chin=.06*bell(x,0,.32)*bell(y,-.88,.18)
    z+=front*(nose+sockets+lids+brows+lips+cheeks+chin)
  }
  return [x,y,z]
}
export function applePoint(u:number,v:number):Vec3 {
  const s=Math.sin(v),y=Math.cos(v)
  const lobes=1+.045*Math.cos(u*5)*s*s
  const notch=1-.13*Math.exp(-(((u-1.0)/.25)**2))*Math.exp(-(((v-1.0)/.3)**2))
  return [Math.sin(u)*s*lobes*notch, y*.92-.20*bell(y,1,.22)+.10*bell(y,-1,.22), Math.cos(u)*s*.86*lobes*notch]
}
export function seeded(seed=19){return ()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296}}
export function particleTargets(count:number){const random=seeded();const face=new Float32Array(count*3),apple=new Float32Array(count*3),scatter=new Float32Array(count*3),phase=new Float32Array(count);for(let i=0;i<count;i++){const u=random()*Math.PI*2,v=Math.acos(2*random()-1);face.set(facePoint(u,v),i*3);apple.set(applePoint(u,v),i*3);scatter.set([(random()-.5)*4.8,(random()-.5)*4.5,(random()-.5)*3.6],i*3);phase[i]=random()*Math.PI*2}return {face,apple,scatter,phase}}
export function particleBudget(width:number,quality=1){return Math.round((width<768?4000:20000)*Math.max(.5,Math.min(1,quality)))}
export function poseForRegion(region:string):Vec3 {return region==='blush'?[0,-.46,0]:region==='eyes'?[.025,.35,0]:region==='lips'?[0,0,0]:[0,-.14,0]}
export function pointerRotation(x:number,y:number):Vec3{return [Math.max(-1,Math.min(1,y))*Math.PI/90,Math.max(-1,Math.min(1,x))*Math.PI/36,0]}
