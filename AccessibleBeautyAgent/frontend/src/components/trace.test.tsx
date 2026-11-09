import {LocaleProvider} from '../content/Locale'
import {describe,it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {TraceDotGrid} from './TraceDotGrid'
import {ThreadProgress} from './ThreadProgress'
import {ModuleHeader} from './ModuleHeader'
import {BeautyMemory} from '../pages/BeautyMemory'
import {productCopy,verifiedBrailleStrings} from '../content/traceBrand'
import {pageFromPath} from '../state/routes'

describe('TRACE accessibility contract',()=>{
 it('decorative cells are hidden and never contain Braille Unicode',()=>{const html=renderToStaticMarkup(<TraceDotGrid activeDots={[1,3,5]}/>);expect(html).toContain('aria-hidden="true"');expect(html).not.toMatch(/[\u2800-\u28ff]/)})
 it('interactive dot navigation requires explicit names',()=>{expect(()=>renderToStaticMarkup(<TraceDotGrid interactive/>)).toThrow();const labels=['Speak','Read','Choose','Guide','Check','Remember'];const html=renderToStaticMarkup(<TraceDotGrid interactive labels={labels} ariaLabel="Capabilities"/>);labels.forEach(label=>expect(html).toContain(`aria-label="${label}"`));expect(html).not.toContain('aria-hidden="true" role="group"')})
 it('progress exposes a textual equivalent and current step',()=>{const html=renderToStaticMarkup(<ThreadProgress current={2} total={4}/>);expect(html).toContain('aria-current="step"');expect(html).toContain('第 2 步，共 4 步')})
 it('module header keeps a clear functional title with bilingual default',()=>{const html=renderToStaticMarkup(<ModuleHeader module="echo"/>);expect(html).toContain('映照 · 妆效检查');expect(html).toContain('Reflection · Makeup check');const en=renderToStaticMarkup(<LocaleProvider initialLocale="en"><ModuleHeader module="echo"/></LocaleProvider>);expect(en).toContain('Reflection · Makeup check');expect(en).not.toContain('映照 · 妆效检查')})
 it('memory candidate is human-readable with a decline action',()=>{const session={stage:'MEMORY_CONSENT',memory_candidate:{feedback:'唇色更浅',context:'dinner'}};const html=renderToStaticMarkup(<BeautyMemory session={session as never} busy={false} consent={async()=>{}} onError={()=>{}}/>);expect(html).toContain('唇色更浅');expect(html).toContain('不保存');expect(html).not.toContain('<pre>')})
 it('only controlled, unverified Braille placeholders exist',()=>{Object.values(verifiedBrailleStrings).forEach(row=>{expect(row.verified).toBe(false);expect(row.braille).toBeNull()})})
 it('bilingual copy has matching keys and direct module routes resolve',()=>{expect(Object.keys(productCopy.en).sort()).toEqual(Object.keys(productCopy['zh-CN']).sort());expect(pageFromPath('/dot')).toBe('dot');expect(pageFromPath('/thread')).toBe('session');expect(pageFromPath('/story')).toBe('story');expect(pageFromPath('/demo')).toBe('demo')})
})

import {pageUrl,initialPage} from '../state/routes'
import {humanError} from '../content/errors'
it('retains demo in module URLs and restores the module after refresh',()=>{
 expect(pageUrl('session',true)).toBe('/thread?demo=true')
 expect(initialPage('/thread','?demo=true')).toBe('session')
 expect(initialPage('/','?demo=true')).toBe('demo')
 expect(pageUrl('dot',false)).toBe('/dot')
})
it('normal errors do not expose technical provider flags or validation JSON',()=>{
 expect(humanError('ALLOW_REMOTE_AI=false','zh-CN')).not.toContain('ALLOW_REMOTE_AI')
 expect(humanError('[{"loc":["body"],"type":"invalid"}]','en')).not.toContain('loc')
})

import {BilingualText} from './BilingualText'
import {bilingual} from '../content/Locale'
it('renders one language with its explicit language tag',()=>{const zh=renderToStaticMarkup(<BilingualText text={bilingual('下一步','Next action')}/>);expect(zh).toContain('lang="zh-CN"');expect(zh).not.toContain('Next action');const en=renderToStaticMarkup(<BilingualText text={bilingual('下一步','Next action','en')}/>);expect(en).toContain('lang="en"');expect(en).not.toContain('下一步');expect(bilingual('下一步','Next action','en')).toBe('Next action')})

it('localizes recognition denial without leaking technical errors',()=>{expect(humanError('Recognition did not finish: not-allowed','en')).toContain('continue with text');expect(humanError('not-allowed','zh-CN')).not.toContain('not-allowed')})
