import {it,expect} from 'vitest'
import {surfaceBudget} from './surfaceBudget'
it('keeps the total budget across a head and small facial meshes at every quality',()=>{
 for(const total of [45000,18000,3500]){
  const counts=surfaceBudget(total,[20000,84,36])
  expect(counts.reduce((a,b)=>a+b,0)).toBe(total)
  expect(counts.every(n=>n>0&&Number.isInteger(n))).toBe(true)
  expect(counts[0]).toBeGreaterThan(counts[1]+counts[2])
 }
 expect(surfaceBudget(10,[])).toEqual([])
})
