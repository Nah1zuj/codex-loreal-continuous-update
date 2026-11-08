// @vitest-environment jsdom
import {it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {LocaleProvider,useTrace,bilingual} from './Locale'
function Copy(){const {c}=useTrace();return <p>{c.home}</p>}
it('renders only active locale catalog',()=>{const en=renderToStaticMarkup(<LocaleProvider initialLocale="en"><Copy/></LocaleProvider>);expect(en).not.toMatch(/[\u3400-\u9fff]/);expect(bilingual('下一步','Next','en')).toBe('Next')})

import {Entry} from '../pages/Entry'
import {VoiceCall} from '../pages/VoiceCall'
import {FullLook} from '../pages/FullLook'
import {Reading} from '../pages/Reading'
import {Pair} from '../pages/Pair'
import {Story} from '../pages/Story'
import {Demo} from '../pages/Demo'
import {Session} from '../pages/Session'
import {BeautyMemory} from '../pages/BeautyMemory'
import {CameraCheck} from '../pages/CameraCheck'
import App from '../App'
const noop=()=>{}
const section={state:'proposed',materials:[],suggestions:[{id:'prep',display_name_zh:'保留你已知可耐受的基础妆前准备',display_name_en:'Your familiar prep',reason:'可省略；不诊断皮肤，也不推断过敏安全。',verified_status:'unreviewed',source_refs:[]}]}
const populated:any={session_id:'test',stage:'GUIDE',selected_look:'soft_formal',selected_products:[],routine_step:0,routine_total_steps:4,scene:'cafe_meeting',todays_look:{version:1,scene:'cafe_meeting',uncertainties:['人工策划演示草稿，尚未作为真实商品推荐审核。'],sections:Object.fromEntries(['skincare','makeup','hair','outfit','accessories','fragrance'].map(k=>[k,section]))}}
const step:any={name:'准备与底妆',instruction:'先把常用底妆薄薄涂在脸中央，再向外轻轻推开。'}
it('renders every normal page without Chinese in English including populated look and safety',()=>{const props:any={snapshot:{state:'error',error:'麦克风权限未允许'},session:populated,step,start:noop,pause:noop,resume:noop,end:noop,interrupt:noop,send:noop,memoryConsent:noop};const pages=[<Entry choose={noop} busy={false}/>,<VoiceCall {...props}/>,<FullLook session={populated} busy={false} apply={noop} startCafe={noop} onError={noop}/>,<Reading health={null} onError={noop}/>,<Pair session={populated} start={noop} onError={noop}/>,<Story start={noop} navigate={noop}/>,<Demo start={noop} busy={false}/>,<Session session={populated} step={step} busy={false} send={noop} compare={noop}/>,<BeautyMemory session={null} busy={false} consent={async()=>{}} onError={noop}/>,<CameraCheck session={null} step={null} health={null} busy={false} consent={async()=>{}} check={async()=>{}} stop={noop} send={noop}/>];for(const page of pages){const html=renderToStaticMarkup(<LocaleProvider initialLocale="en">{page}</LocaleProvider>);expect(html).not.toMatch(/[\u3400-\u9fff]/)}const look=renderToStaticMarkup(<LocaleProvider initialLocale="en"><FullLook session={populated} busy={false} apply={noop} startCafe={noop} onError={noop}/></LocaleProvider>);expect(look).toContain('does not diagnose skin');expect(look).toContain('allergy safety')})
it('renders App navigation titles and all initial routes in the active locale',()=>{for(const path of ['/','/voice','/explore','/full-look','/dot','/pair','/thread','/imprint','/echo','/story','/demo','/devices','/mirror']){window.history.replaceState({},'',path);const html=renderToStaticMarkup(<LocaleProvider initialLocale="en"><App/></LocaleProvider>);expect(html).not.toMatch(/[\u3400-\u9fff]/)}})

it('renders Chinese populated suggestions without their English duplicate names',()=>{const look={...populated,todays_look:{...populated.todays_look,sections:{makeup:{...section,suggestions:[{...section.suggestions[0],display_name_zh:'Soft Formal · 柔和正式',display_name_en:'Soft Formal'}]}}}};const html=renderToStaticMarkup(<LocaleProvider><FullLook session={look} busy={false} apply={noop} startCafe={noop} onError={noop}/></LocaleProvider>);expect(html).toContain('柔和正式');expect(html).not.toContain('Soft Formal');expect(html).not.toContain('Version')})
