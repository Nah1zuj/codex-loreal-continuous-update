/** Keep language changes explicit for assistive technology. */
export function BilingualText({text}:{text:string}){return <span className="bilingual-copy">{text.split('\n').map((line,i)=><span key={i} lang={/[\u3400-\u9fff]/.test(line)?'zh-CN':'en'} className={i===0?'language-primary':'language-secondary'}>{line}</span>)}</span>}
