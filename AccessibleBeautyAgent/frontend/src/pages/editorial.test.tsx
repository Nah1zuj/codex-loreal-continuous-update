import {it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {LocaleProvider} from '../content/Locale'
import {Entry} from './Entry'
import {VoiceCall} from './VoiceCall'
import {isVisualRequest} from '../realtime/visualCommand'

it('keeps the real conversation inside the voice layout with explicit camera and workflow actions',()=>{
 const html=renderToStaticMarkup(<LocaleProvider initialLocale="en"><VoiceCall snapshot={{state:'idle',transcript:'',reply:'',error:''}} session={null} step={null} start={()=>{}} pause={()=>{}} resume={()=>{}} end={()=>{}} interrupt={()=>{}} send={()=>{}} memoryConsent={()=>{}} openCamera={()=>{}} conversation={<section aria-label="Real conversation">An actual session turn</section>}/></LocaleProvider>)
 expect(html).toContain('An actual session turn')
 expect(html).toContain('Open camera in this session')
 expect(html).toContain('Not finished yet')
 expect(html).not.toContain('Today I am meeting friends')
})
it('exposes the four real experience destinations without fake membership services',()=>{
 const html=renderToStaticMarkup(<LocaleProvider><Entry choose={()=>{}} busy={false} openLook={()=>{}} openMemory={()=>{}} openStory={()=>{}}/></LocaleProvider>)
 expect(html).toContain('听见你的美')
 expect(html).toContain('experience-card')
 expect(html).toContain('了解我们的故事')
 expect(html).not.toContain('登录 / 注册')
})
it('routes recheck commands conservatively and never turns negation into camera permission',()=>{
 expect(isVisualRequest('再检查一次。')).toBe(true)
 expect(isVisualRequest('帮我看看')).toBe(true)
 expect(isVisualRequest('不要再检查一次')).toBe(false)
 expect(isVisualRequest('我还没有完成')).toBe(false)
})
