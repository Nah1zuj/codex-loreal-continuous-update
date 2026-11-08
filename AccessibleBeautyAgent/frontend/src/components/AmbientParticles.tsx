import type {CSSProperties} from 'react'
import type {CallState} from '../realtime/callController'
/** Fixed positions avoid runtime randomness and keep decoration silent. */
const positions=[[8,18],[22,76],[39,12],[57,84],[73,28],[91,68]] as const
export function AmbientParticles({reducedMotion=false,state='idle'}:{reducedMotion?:boolean;state?:CallState}){return <div className="ambient-particles" aria-hidden="true" data-call-state={state} data-motion={!reducedMotion&&['listening','thinking','speaking'].includes(state)?'gentle':'static'}>{positions.map(([x,y],i)=><i className="ambient-particle" key={i} style={{left:x+'%',top:y+'%','--delay':i*-3+'s'} as CSSProperties}/>)}</div>}
