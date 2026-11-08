import {describe,it,expect} from 'vitest'
import {carveApple,appleBites} from './appleBites'
describe('apple sculpture cut-outs',()=>{
 it('carves an intersecting surface without moving the opposite side',()=>{
  const bite={center:[.85,.2,.45] as [number,number,number],radius:.48}
  const original:[number,number,number]=[.85,.2,.45]
  expect(Math.hypot(...carveApple(original,[bite]))).toBeLessThan(Math.hypot(...original))
  expect(carveApple([-1,0,0],[bite])).toEqual([-1,0,0])
 })
 it('provides varied one-to-three bites and finite results',()=>{
  expect(new Set(Array.from({length:8},(_,i)=>appleBites(i).length))).toEqual(new Set([1,2,3]))
  for(let i=0;i<8;i++)for(const p of [[0,0,0],[.8,.3,.4],[-.9,.2,.4]] as [number,number,number][])
   expect(carveApple(p,appleBites(i)).every(Number.isFinite)).toBe(true)
 })
})
