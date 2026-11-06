import {it,expect} from 'vitest'
import {cleanDraft,setPath,newRecord} from './fields'
it('keeps missing product claims unknown instead of adding claims',()=>{const p=cleanDraft({product_id:'new',claims:[''],finish:'',saturation:''});expect(p.claims).toEqual([]);expect(p.finish).toBeNull();expect(p.saturation).toBeNull()})
it('changes one reference attribute without changing provenance',()=>{const r={source_ids:['source_a'],blush:{visible:true,intensity:'medium'}};const revised=setPath(r,'blush.intensity','light_medium');expect(revised).toEqual({source_ids:['source_a'],blush:{visible:true,intensity:'light_medium'}});expect(r.blush.intensity).toBe('medium')})
it('new reference stays an unverified draft',()=>{const r=newRecord('REFERENCE_CASE');expect(r.human_verified).toBe(false);expect(r.verified).toBe(false);expect(r.status).toBe('DRAFT')})
