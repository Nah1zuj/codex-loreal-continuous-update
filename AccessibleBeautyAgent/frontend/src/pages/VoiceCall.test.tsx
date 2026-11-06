import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import {LocaleProvider} from '../content/Locale'
import {VoiceCall} from './VoiceCall'
const props={snapshot:{state:'paused',transcript:'',reply:'Which tool do you have?',error:''} as const,session:null,step:{instruction:'Static reference'} as any,start(){},pause(){},resume(){},end(){},interrupt(){},send(){},memoryConsent(){}}
it('prioritizes the current answer and keeps recommendations outside pure voice',()=>{
 const html=renderToStaticMarkup(<LocaleProvider initialLocale="en"><VoiceCall {...props}/></LocaleProvider>)
 expect(html).toContain('<p class="instruction">Which tool do you have?</p>')
 expect(html).not.toContain('aria-label="Recommendations"')
 const visual=renderToStaticMarkup(<LocaleProvider initialLocale="en"><VoiceCall {...props} showRecommendations/></LocaleProvider>)
 expect(visual).toContain('aria-label="Recommendations"')
})
