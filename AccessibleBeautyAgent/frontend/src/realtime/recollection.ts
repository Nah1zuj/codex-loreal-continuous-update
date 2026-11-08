export interface LookSummary{session_id:string;name:string;date:string;occasion:string;style:string;completed_steps:string[];all_steps_completed:boolean;id?:string;version?:string;note?:string;origin?:'confirmed_course'|'legacy_automatic'|'legacy_reconfirmed';reusable?:boolean}
export interface RecollectionView{enabled:boolean;latest:LookSummary|null;entries:LookSummary[];retention_days:number}
export function returnGreeting(view:RecollectionView|null,locale:'zh-CN'|'en',includeBegin=true){
 if(!view?.enabled||!view.latest?.reusable)return locale==='en'
  ?'Welcome to TRACE. I will guide you by voice. Say let’s begin to enter Listen.'
  :'欢迎来到TRACE。我会用声音陪你完成今天的装扮。说可以开始，我们进入倾听。'
 return locale==='en'
  ?'Welcome back. You selected a previous style to reuse. Would you like to keep it or try a new one?'+(includeBegin?' Say let’s begin to enter Listen.':'')
  :'又见面啦。你选了下次沿用上一次的风格。今天要沿用，还是换一种？'+(includeBegin?'说可以开始，我们进入倾听。':'')
}
