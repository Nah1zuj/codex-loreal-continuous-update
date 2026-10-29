import {BilingualText} from '../components/BilingualText'
import {useTrace} from '../content/Locale'
import {traceBrand} from '../content/traceBrand'
import {TraceDotGrid} from '../components/TraceDotGrid'
export function Demo({start,busy}:{start:()=>void;busy:boolean}){const {c,t}=useTrace();return <section className="trace-demo"><TraceDotGrid activeDots={[1,3,5]}/><h1>TRACE</h1><p className="story-line">{t("听见你的美",traceBrand.tagline)}</p><blockquote><BilingualText text={c.dinner}/></blockquote><button className="primary" disabled={busy} onClick={start}><BilingualText text={c.demoStart}/></button><p><BilingualText text={c.demoExplain}/></p></section>}
