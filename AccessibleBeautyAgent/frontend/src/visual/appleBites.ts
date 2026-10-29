import type {Vec3} from './geometry'
export interface AppleBite {center:Vec3;radius:number}
/** Circular bites run through the depth so each missing edge reads in silhouette. */
export function carveApple(point:Vec3,bites:AppleBite[]):Vec3 {
 const radius=Math.hypot(point[0],point[1])
 if(radius<1e-8)return point
 const direction:Vec3=[point[0]/radius,point[1]/radius,0]
 let cut=radius
 for(const bite of bites){
  const along=direction.reduce((sum,v,i)=>sum+v*bite.center[i],0)
  const disc=along*along-(bite.center[0]**2+bite.center[1]**2-bite.radius*bite.radius)
  if(disc<0)continue
  const near=along-Math.sqrt(disc),far=along+Math.sqrt(disc)
  if(near>0&&near<cut&&far>cut)cut=near
 }
 return [direction[0]*cut,direction[1]*cut,point[2]]
}
export function appleBites(index:number):AppleBite[]{
 const side=index%3===0?-1:1,count=[1,2,1,3,2,1,2,3][index%8]
 const r=.39+(index%4)*.045
 return Array.from({length:count},(_,i)=>({center:[side*(.88+i*.015),.34-i*.30,.10] as Vec3,radius:r-i*.025}))
}
