/** Share one surface budget across a model's meshes, including small facial parts. */
export function surfaceBudget(total:number,weights:number[]){
 const sum=weights.reduce((a,b)=>a+b,0)
 if(!weights.length||sum<=0)return weights.map(()=>0)
 const exact=weights.map(w=>total*w/sum),counts=exact.map(Math.floor)
 const ranked=exact.map((value,index)=>({index,fraction:value-counts[index]})).sort((a,b)=>b.fraction-a.fraction)
 const remainder=total-counts.reduce((a,b)=>a+b,0)
 for(let i=0;i<remainder;i++)counts[ranked[i].index]++
 return counts
}
