import {it,expect} from 'vitest'
import * as THREE from 'three'
import {refinePortrait} from './refinePortrait'

it('refines front jaw and lips while preserving the back and mesh connectivity',()=>{
 const geometry=new THREE.BufferGeometry()
 geometry.setAttribute('position',new THREE.Float32BufferAttribute([
  .7,-.18,.6, 0,.10,.7, -.7,-.18,.6,
  .7,-.18,-.6, 0,.5,-.6, -.7,-.18,-.6,
 ],3))
 geometry.setIndex([0,1,2,3,4,5])
 const original=geometry.getAttribute('position').array.slice()
 refinePortrait(geometry)
 const p=geometry.getAttribute('position')
 expect(p.getX(0)).toBeLessThan(.7)
 expect(p.getZ(1)).toBeGreaterThan(.7)
 expect([...p.array].every(Number.isFinite)).toBe(true)
 expect([...geometry.getAttribute('normal').array].every(Number.isFinite)).toBe(true)
 expect([...geometry.index!.array]).toEqual([0,1,2,3,4,5])
 expect([...p.array].slice(9)).toEqual([...original].slice(9))
 geometry.dispose()
})
