import {expect,it} from 'vitest'
import {StoryField,storyQuality,pointerForce} from './storyField'

it('keeps independent stochastic velocities finite and bounded after long frames',()=>{
 const f=new StoryField(120,12)
 for(let i=0;i<600;i++)f.step(i===2?10:1/60,'IDLE',0,null)
 expect([...f.position,...f.velocity].every(Number.isFinite)).toBe(true)
 expect(Math.max(...f.velocity.map(Math.abs))).toBeLessThanOrEqual(.65)
 expect(f.velocity[0]).not.toBe(f.velocity[3])
 expect(Math.max(...f.position.map(Math.abs))).toBeLessThan(2.7)
})
it('uses a local pointer force and explicit reduced/mobile quality',()=>{
 expect(pointerForce(2,2,0,0)).toEqual([0,0])
 expect(Math.hypot(...pointerForce(.05,.05,0,0))).toBeGreaterThan(0)
 expect(storyQuality(390,false).count).toBeLessThan(storyQuality(1440,false).count)
 expect(storyQuality(1440,true).name).toBe('REDUCED')
})
it('does not integrate paused/reduced motion and listening gathers without fake volume',()=>{
 const f=new StoryField(200,12),before=f.position.slice()
 f.step(1/60,'REDUCED_MOTION',1,{x:0,y:0})
 expect(f.position).toEqual(before)
 const distance=()=>f.position.reduce((sum,value,i)=>sum+(value-f.target[i])**2,0)
 const initial=distance()
 for(let i=0;i<300;i++)f.step(1/60,'LISTENING',0,null)
 expect(distance()).toBeLessThan(initial)
})
