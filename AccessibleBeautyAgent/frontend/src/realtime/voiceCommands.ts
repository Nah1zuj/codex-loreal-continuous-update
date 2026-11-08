export const normalizeVoice=(text:string)=>text.trim().replace(/[\s，,。.!！?？：:；;“”"、]+/g,'').toLowerCase()
export function wakeInput(text:string):string|null{
 const match=text.trim().match(/^(重新启动语音交流功能|重新开启语音功能|resume\s+voice)[\s，,。.!！?？：:；;]*([\s\S]*)$/i)
 if(!match||/(是什么意思|这个词|这句话)/.test(match[2]))return null
 return match[2].trim()
}
export function isSoftPause(text:string){return ['请终止对话','暂停语音','暂停回应','停止语音播报','停止','stop','pause replies','pause voice','stop speaking'].some(word=>normalizeVoice(text)===normalizeVoice(word))}
export function isMicrophoneClosePhrase(text:string){return ['关闭麦克风','完全停止聆听','退出语音','close microphone'].some(word=>normalizeVoice(text)===normalizeVoice(word))}
export function routeVoice(text:string,page:string):{page?:'home'|'voice'|'explore'|'memory'|'full-look'|'story';command?:'begin'|'reflect'|'finish'|'help'|'repeat'|'next'|'previous'|'skip'|'clearRecall'|'disableRecall'|'enableRecall'}|null{
 // Keep questions intact so the server can ask for clarification.
 if(/[?？]/.test(text))return null
 const value=normalizeVoice(text)
 if(page==='voice'&&/^(?:请|我要|我想)?(?:进入|去|开始)(?:映照|应照|硬照|印照)(?:环节)?(?:完?完成|了)?$/.test(value))return {command:'reflect'}
 if(['可以开始','开始体验',"let'sbegin",'letsbegin','let’sbegin'].includes(value))return {command:'begin'}
 if(['完成','倾听完成','我说完了','说完了','好了','可以进入映照了','进入映照环节','进入应照环节','开始化妆','开始上妆','done'].includes(value)&&page==='voice')return {command:'reflect'}
 if(['结束本次装扮','结束今天的装扮','finishthislook','finishsession'].includes(value))return {command:'finish'}
 if(['帮助','我可以说什么','help'].includes(value))return {command:'help'}
 if(['再说一次','再说一遍','重复','repeat'].includes(value))return {command:'repeat'}
 if(['下一步','这一步完成','完成','next'].includes(value))return {command:'next'}
 if(['上一步','previous'].includes(value))return {command:'previous'}
 if(['跳过','跳过这一步','skip'].includes(value))return {command:'skip'}
 if(['清除拾光记忆','清除上次妆容','clearlookmemory'].includes(value))return {command:'clearRecall'}
 if(['关闭拾光回忆','不要再提上次','disablelookmemory'].includes(value))return {command:'disableRecall'}
 if(['开启拾光回忆','enablelookmemory'].includes(value))return {command:'enableRecall'}
 const names={home:['go home','open home','去首页','回首页','进入第一步','进入第1步'],voice:['open listen','enter listen','进入倾听','去倾听','进入第二步','进入第2步'],explore:['enter reflect','open reflect','进入映照','进入应照','去应照','去映照','进入第三步','进入第3步'],memory:['open trace','open memory','打开拾光','进入拾光','进入第四步','进入第4步'], 'full-look':['open full look','打开今天的你','进入今天的你','进入第五步','进入第5步'],story:['open story','打开故事','进入故事','进入第六步','进入第6步']}
 for(const [target,words] of Object.entries(names))if(words.some(word=>normalizeVoice(word)===value))return target==='explore'?{command:'reflect'}:{page:target as 'home'}
 return null
}
