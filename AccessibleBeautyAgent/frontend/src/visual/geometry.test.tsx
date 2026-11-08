import {describe,it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {facePoint,applePoint,particleTargets,particleBudget,pointerRotation,poseForRegion} from './geometry'
import {BilingualHeading} from './BilingualHeading'
import {LocaleProvider} from '../content/Locale'
describe('original sensory geometry',()=>{
 it('keeps all morph targets finite and aligned with deterministic particle identity',()=>{const a=particleTargets(5000),b=particleTargets(5000);expect(a.face).toEqual(b.face);for(const buffer of [a.face,a.apple,a.scatter]){expect(buffer.length).toBe(15000);expect([...buffer].every(Number.isFinite)).toBe(true)}for(const fn of [facePoint,applePoint]){expect(fn(0,0).every(Number.isFinite)).toBe(true);expect(fn(Math.PI,Math.PI).every(Number.isFinite)).toBe(true)}})
 it('respects device budgets and can halve quality without changing target identity',()=>{expect(particleBudget(375)).toBe(4000);expect(particleBudget(1280)).toBe(20000);expect(particleBudget(375,.5)).toBe(2000);expect(particleBudget(1280,.5)).toBe(10000)})
 it('clamps pointer drift to two and five degrees and uses purposeful makeup poses',()=>{const rotation=pointerRotation(100,-100);expect(rotation[0]).toBeCloseTo(-Math.PI/90);expect(rotation[1]).toBeCloseTo(Math.PI/36);expect(poseForRegion('lips')[1]).toBe(0);expect(Math.abs(poseForRegion('blush')[1])).toBeGreaterThan(.3)})
 it('shows both key languages by default, and respects English first',()=>{const zh=renderToStaticMarkup(<LocaleProvider><BilingualHeading zh="今天的你" en="Today's Full Look"/></LocaleProvider>);expect(zh).toContain('今天的你');expect(zh).toContain("Today&#x27;s Full Look");const en=renderToStaticMarkup(<LocaleProvider initialLocale="en"><BilingualHeading zh="今天的你" en="Today's Full Look"/></LocaleProvider>);expect(en).not.toContain('今天的你');expect(en).toContain('lang="en"')})
})
