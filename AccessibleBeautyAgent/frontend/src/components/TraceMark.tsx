import {traceBrand} from '../content/traceBrand'
import {AppleMark} from './AppleMark'
export function TraceMark(){return <span className="trace-mark"><span>{traceBrand.name}</span><AppleMark/></span>}
