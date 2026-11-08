import {LocaleProvider} from '../content/Locale'
import {describe,it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {Entry} from '../pages/Entry'
import {FullLook} from '../pages/FullLook'
import {MemoryFacts} from './MemoryFacts'
import {pageFromPath,pageUrl} from '../state/routes'
describe('V4 experience contracts',()=>{
 it('preserves all three input modes in the editorial entry',()=>{const html=renderToStaticMarkup(<Entry choose={()=>{}} busy={false}/>);expect((html.match(/<button/g)??[]).length).toBeGreaterThanOrEqual(4);['开始体验','实时妆教','文字输入'].forEach(label=>expect(html).toContain(label));expect(html).toContain('Voice Companion');const en=renderToStaticMarkup(<LocaleProvider initialLocale="en"><Entry choose={()=>{}} busy={false}/></LocaleProvider>);expect(en).toContain('Voice Companion');expect(en).not.toMatch(/[\u3400-\u9fff]/);expect(html).not.toContain('autofocus')})
 it('retains every legacy route and new direct routes',()=>{for(const [path,page] of Object.entries({'/':'home','/speak':'speak','/thread':'session','/echo':'camera','/imprint':'memory','/dot':'dot','/pair':'pair','/story':'story','/demo':'demo','/voice':'voice','/explore':'explore','/full-look':'full-look'}))expect(pageFromPath(path)).toBe(page);expect(pageUrl('voice',true)).toBe('/voice?demo=true')})
 it('allows starting the plan before a session and communicates material limits',()=>{const html=renderToStaticMarkup(<FullLook session={null} busy={false} apply={()=>{}} startCafe={()=>{}} onError={()=>{}}/>);expect(html).toContain("规划今日造型");expect(html).toContain('照片不能确定纤维成分');expect(html).toContain('比较两种材质');expect(html).not.toContain('autoplay')})
 it('renders material and domain memory preferences as readable facts',()=>{const html=renderToStaticMarkup(<MemoryFacts candidate={{material_preferences:['棉'],domain_preferences:{fragrance:['不要甜香']}}}/>);expect(html).toContain('材质偏好');expect(html).toContain('棉');expect(html).toContain('香氛');expect(html).toContain('不要甜香');expect(html).not.toContain('[object Object]')})
})
