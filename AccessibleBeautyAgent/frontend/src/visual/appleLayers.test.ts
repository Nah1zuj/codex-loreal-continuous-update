import {it,expect} from 'vitest'
import {qualityLayers,sculptureField} from './sculptureField'
it('keeps a readable section and bounded dissolving flow through every quality tier',()=>{
 for(const tier of Object.values(qualityLayers)){expect(tier.slice).toBeGreaterThan(0);expect(tier.burst).toBeGreaterThan(0);expect(tier.ribbon).toBeGreaterThan(0);expect(tier.satellite).toBeGreaterThan(0);expect(tier.fragment).toBeGreaterThan(0)}
 for(const layer of ['slice','burst','ribbon'] as const){const a=sculptureField(layer,1000),b=sculptureField(layer,1000);expect(a.position).toEqual(b.position);expect(a.anchor.length).toBe(3000);expect([...a.position,...a.anchor,...a.velocity].every(Number.isFinite)).toBe(true)}
 const ribbon=sculptureField('ribbon',1000);expect(Math.max(...[...ribbon.position].filter((_,i)=>i%3===0))).toBeGreaterThan(2);expect(Math.min(...[...ribbon.position].filter((_,i)=>i%3===0))).toBeLessThan(-2)
 const slice=sculptureField('slice',1000);expect(Math.max(...[...slice.color])).toBeGreaterThan(.9)
})
