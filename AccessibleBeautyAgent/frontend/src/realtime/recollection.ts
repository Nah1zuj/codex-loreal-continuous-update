export interface LookSummary{session_id:string;name:string;date:string;occasion:string;style:string;completed_steps:string[];all_steps_completed:boolean}
export interface RecollectionView{enabled:boolean;latest:LookSummary|null;entries:LookSummary[];retention_days:number}
export function returnGreeting(view:RecollectionView|null,locale:'zh-CN'|'en',includeBegin=true){
 if(!view?.enabled||!view.latest)return locale==='en'?'Welcome to TRACE. I will guide you by voice. Say let’s begin to enter Listen.':'欢迎来到TRACE。我会用声音陪你完成今天的装扮。说可以开始，我们进入倾听。'
 const item=view.latest,verb=item.completed_steps.length?(locale==='en'?'tried':'一起尝试了'):(locale==='en'?'discussed':'聊到了')
 return locale==='en'?`Welcome back. Last time we ${verb} ${item.name}. Would you like to keep that feeling or try something new? ${includeBegin?' Say let’s begin to enter Listen.':''}`:`又见面啦。上次我们${verb}${item.name}，今天想延续这个感觉，还是换个风格？${includeBegin?'说可以开始，我们进入倾听。':''}`
}
