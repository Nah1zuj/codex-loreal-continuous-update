import {BilingualHeading} from '../visual/BilingualHeading'
import {modules,type ModuleKey} from '../content/traceBrand'
import {useTrace,bilingual} from '../content/Locale'
import {TraceDotGrid} from './TraceDotGrid'
export function ModuleHeader({module,explanation}:{module:ModuleKey;explanation?:string}){const {locale}=useTrace();const m=modules[module];return <div className="module-header"><div className="module-sign"><TraceDotGrid activeDots={m.dots}/><span>{m.concept}</span></div><BilingualHeading zh={m.label['zh-CN']} en={m.label.en}/>{locale==='en'?<p className="module-descriptor" lang="en">{m.descriptor}</p>:null}<p className="module-explanation">{explanation??bilingual(m.description['zh-CN'],m.description.en,locale)}</p></div>}
