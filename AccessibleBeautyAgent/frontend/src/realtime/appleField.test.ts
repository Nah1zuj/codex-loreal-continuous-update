import {expect,it} from 'vitest'
import {particleBudget,localRipple} from './appleField'
it('uses a genuine million point desktop budget with bounded mobile and static budgets',()=>{expect(particleBudget(1440)).toBe(1048576);expect(particleBudget(390)).toBe(131072);expect(particleBudget(1440,true)).toBe(32768)})
it('keeps mouse effects local and increases wave amplitude with audio energy',()=>{const quiet=localRipple(.1,0,0,0,0,0),loud=localRipple(.1,0,0,0,0,1);expect(Math.abs(loud)).toBeGreaterThan(Math.abs(quiet));expect(Math.abs(localRipple(3,3,0,0,1,1))).toBeLessThan(.00001)})
