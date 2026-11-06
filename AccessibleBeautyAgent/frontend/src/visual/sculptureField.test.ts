import {it,expect} from 'vitest'
import {qualityLayers,sculptureField} from './sculptureField'
it('bounds adaptive layers and seeds non-uniform anatomy-independent fields',()=>{
 expect(Object.values(qualityLayers.high).reduce((a,b)=>a+b,0)).toBe(325000)
 expect(Object.values(qualityLayers.low).reduce((a,b)=>a+b,0)).toBeLessThan(20000)
 for(const layer of ['apple','plume','orbit'] as const){const a=sculptureField(layer,1000),b=sculptureField(layer,1000);expect(a.position).toEqual(b.position);expect([...a.position,...a.velocity,...a.color].every(Number.isFinite)).toBe(true)}
 const plume=sculptureField('plume',1000);expect(Math.max(...[...plume.position].filter((_,i)=>i%3===1))).toBeGreaterThan(3)
})
