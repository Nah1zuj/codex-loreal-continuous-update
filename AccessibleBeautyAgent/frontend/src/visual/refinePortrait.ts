import * as THREE from 'three'

const bell=(value:number,center:number,width:number)=>Math.exp(-(((value-center)/width)**2))
/** Sculptural derivative of the attributed default mesh, in its normalized coordinates.
 * Preserve the original surface connectivity; never applied to a replacement model. */
export function refinePortrait(geometry:THREE.BufferGeometry){
 const p=geometry.getAttribute('position') as THREE.BufferAttribute
 for(let i=0;i<p.count;i++){
  const x=p.getX(i),y=p.getY(i),z=p.getZ(i),a=Math.abs(x)
  const front=THREE.MathUtils.smoothstep(z,-.05,.42)
  const jaw=bell(y,-.18,.27),chin=bell(x,0,.28)*bell(y,-.23,.16)
  const nose=bell(x,0,.18)*bell(y,.43,.25)*front
  const eye=bell(a,.22,.16)*bell(y,.62,.08)*front
  const brow=bell(a,.24,.22)*bell(y,.78,.09)*front
  const lip=bell(x,0,.26)*bell(y,.10,.10)*front
  const cheek=bell(a,.40,.20)*bell(y,.40,.20)*front
  const neck=bell(y,-.66,.25)*(1-THREE.MathUtils.smoothstep(y,-.42,-.3))
  const width=1-front*(.18*jaw+.04*bell(y,.85,.5))-.075*neck
  const nextX=x*width*(1-.20*nose)
  const nextY=y+.065*chin*front+.018*nose+.022*cheek
  const nextZ=z+.075*eye-.040*brow+.065*lip+.035*cheek-.060*nose-.025*chin*front
  p.setXYZ(i,nextX,nextY,nextZ)
 }
 p.needsUpdate=true
 geometry.computeVertexNormals()
 geometry.computeBoundingBox()
 geometry.computeBoundingSphere()
 return geometry
}
