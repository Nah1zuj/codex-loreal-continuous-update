// Run against the isolated TRACE launcher and a disposable Chrome DevTools profile.
// Arguments: http://127.0.0.1:<frontend-port> <profile-directory>
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {setTimeout as sleep} from 'node:timers/promises'

const [origin,profile]=process.argv.slice(2)
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin??'')||!profile){
  throw Error('Expected an isolated loopback URL and Chrome profile directory')
}
async function until(read,description){
  for(let n=0;n<120;n++){
    try{const value=await read();if(value)return value}catch{}
    await sleep(250)
  }
  throw Error('Timed out: '+description)
}
const port=await until(async()=>(await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0],'Chrome debug port')
const target=await until(async()=>(await (await fetch('http://127.0.0.1:'+port+'/json/list')).json()).find(p=>p.type==='page'),'Chrome page')
const socket=new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject})
let id=0
const waiting=new Map(),events=new Map()
function call(method,params={}){
  const requestId=++id
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{waiting.delete(requestId);reject(Error('CDP timeout: '+method))},30000)
    waiting.set(requestId,{resolve,reject,timeout})
    socket.send(JSON.stringify({id:requestId,method,params}))
  })
}
socket.onmessage=({data})=>{
  const message=JSON.parse(data)
  if(message.id){
    const reply=waiting.get(message.id)
    if(!reply)return
    waiting.delete(message.id);clearTimeout(reply.timeout)
    if(message.error)reply.reject(Error(JSON.stringify(message.error)))
    else reply.resolve(message.result)
  }else events.get(message.method)?.(message.params)
}
async function js(expression){
  const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true})
  if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails))
  return result.result.value
}
async function submit(text,selector='#message'){
  const field=JSON.stringify(selector)
  await js(`(()=>{const input=document.querySelector(${field}); input.focus();
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(text)});
    input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:${JSON.stringify(text)}}));})()`)
  await until(()=>js(`!document.querySelector(${field}).form.querySelector('button').disabled`),'enabled text submit')
  await js(`document.querySelector(${field}).form.requestSubmit()`)
}
const session="(async()=>{const id=sessionStorage.getItem('trace.session_id');return id?await (await fetch('/api/session/'+id)).json():null})()"
try{
  await call('Page.enable')
  await call('Browser.grantPermissions',{origin,permissions:['audioCapture','videoCapture']})
  await call('Page.addScriptToEvaluateOnNewDocument',{source:`
    window.traceMediaRequests=[]
    const get=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices)
    navigator.mediaDevices.getUserMedia=constraints=>{window.traceMediaRequests.push(constraints);return get(constraints)}
    localStorage.setItem('trace.voice-enabled','on')
  `})
  await call('Page.navigate',{url:origin+'/thread'})
  await until(()=>js("!!document.querySelector('#message')"),'text form')
  await call('Input.dispatchKeyEvent',{type:'rawKeyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9})
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9})
  assert.equal(await js("document.activeElement.className"),'skip-link')
  await js("document.activeElement.click()")
  assert.equal(await js("document.activeElement.id"),'main-content')
  await js(`(()=>{const select=document.querySelector('.language-display select');select.focus();
    select.value='english';select.dispatchEvent(new Event('change',{bubbles:true}));})()`)
  await until(()=>js("document.documentElement.lang==='en'"),'English locale')
  assert.equal(await js("document.activeElement.matches('.language-display select')"),true)
  await call('Accessibility.enable')
  const tree=await call('Accessibility.getFullAXTree')
  assert.ok(tree.nodes.some(node=>node.role?.value==='textbox'&&node.name?.value==='Your day, feelings or desired look'))
  await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]})
  await call('Emulation.setDeviceMetricsOverride',{width:640,height:800,deviceScaleFactor:1,mobile:false})
  assert.equal(await js("matchMedia('(prefers-reduced-motion: reduce)').matches"),true)
  assert.equal(await js("document.documentElement.scrollWidth<=innerWidth&&document.querySelector('#message').getBoundingClientRect().width>0"),true)
  const originalFont=await js("parseFloat(getComputedStyle(document.querySelector('#message')).fontSize)")
  await js("document.querySelector('.display-preferences button').click()")
  await until(()=>js("document.querySelector('.trace-app').dataset.textSize==='large'"),'larger text preference')
  assert.ok(await js("parseFloat(getComputedStyle(document.querySelector('#message')).fontSize)")>originalFont)
  assert.equal(await js("document.documentElement.scrollWidth<=innerWidth"),true)
  await js("document.querySelector('.display-preferences button').click()")
  await call('Emulation.clearDeviceMetricsOverride')
  await js(`(()=>{const select=document.querySelector('.language-display select');select.value='chinese';
    select.dispatchEvent(new Event('change',{bubbles:true}));})()`)
  await until(()=>js("document.documentElement.lang==='zh-CN'"),'Chinese locale')
  console.log('PASS Chrome keyboard skip link, locale focus and textbox name, reduced-motion preference and larger text at 640px')
  assert.deepEqual(await js('window.traceMediaRequests'),[])
  await submit('我想画个十五分钟的自然日常妆')
  const draft=await until(async()=>{const s=await js(session);return s?.makeup_plan?.status==='draft'&&s},'draft lesson')
  await submit('开始')
  const active=await until(async()=>{const s=await js(session);return s?.makeup_plan?.status==='active'&&s},'active lesson')
  assert.equal(active.session_id,draft.session_id)
  await until(()=>js("!!document.querySelector('.step')&&!document.querySelector('.streaming-reply')"),'rendered lesson step')

  let interrupted=null,requests=0
  await call('Fetch.enable',{patterns:[{urlPattern:origin+'/api/chat/stream',requestStage:'Response'}]})
  events.set('Fetch.requestPaused',async event=>{
    try{
      const body=JSON.parse(event.request.postData??'{}')
      if(body.message==='下一步'||body.message==='next'){
        requests++
        const response=await call('Fetch.getResponseBody',{requestId:event.requestId})
        const raw=response.base64Encoded?Buffer.from(response.body,'base64').toString('utf8'):response.body
        interrupted=raw.split('\n').filter(x=>x.startsWith('data:')).map(x=>JSON.parse(x.slice(5))).find(x=>x.type==='committed')
        await call('Fetch.failRequest',{requestId:event.requestId,errorReason:'InternetDisconnected'})
      }else await call('Fetch.continueRequest',{requestId:event.requestId})
    }catch(error){console.error(error);process.exitCode=1}
  })
  await submit('下一步')
  await until(()=>js("document.body.innerText.includes('已同步当前进度')"),'recovery after severed stream')
  assert.equal(requests,1)
  assert.ok(interrupted?.event?.event_id)
  await call('Fetch.disable')
  const advanced=await js(session)
  assert.equal(advanced.makeup_plan.active_index,active.makeup_plan.active_index+1)
  assert.equal(advanced.makeup_plan.revision,active.makeup_plan.revision+1)
  console.log('PASS real browser: one committed Next after dropped streaming response; result recovered by event')

  await js("document.querySelector('[data-primary-voice]').click()")
  await until(()=>js("window.traceMediaRequests.some(request=>request.audio)"),'explicit microphone gesture')
  const connections="fetch('/local-voice/health').then(response=>response.json()).then(health=>health.connections)"
  await until(async()=>await js(connections)===1,'local WebSocket connected')
  await call('Page.reload')
  await until(()=>js("!!document.querySelector('#message')&&!!document.querySelector('.step')"),'restored lesson step')
  await sleep(400)
  assert.deepEqual(await js('window.traceMediaRequests'),[])
  await until(async()=>await js(connections)===0,'old local WebSocket released')
  const restored=await js(session)
  assert.equal(restored.makeup_plan.revision,advanced.makeup_plan.revision)
  assert.equal(restored.camera_consent,false)
  console.log('PASS real browser: reload restores step and does not request remembered microphone or camera permission')
  await submit('结束今天')
  await until(async()=>(await js(session))?.makeup_plan?.status==='completed','completed lesson')
  const button=label=>`[...document.querySelectorAll('button')].find(button=>button.textContent.trim()===${JSON.stringify(label)})`
  const click=async label=>{
    await until(()=>js(`Boolean(${button(label)})`),label)
    await js(`${button(label)}.click()`)
  }
  await click('查看本次小结')
  await until(()=>js("!!document.querySelector('#summary-review-title')"),'summary candidate')
  const counts="fetch('/api/recollection').then(response=>response.json()).then(data=>data.entries.length)"
  assert.equal(await js(counts),0)
  assert.equal(await js(`${button('保存此摘要')}.disabled`),true)
  await js(`(()=>{const note=document.querySelector('.look-recollection textarea');
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(note,'合成回归备注');
    note.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:'合成回归备注'}));})()`)
  await click('预览修改后的版本')
  await until(()=>js("document.body.innerText.includes('新版摘要已准备好')"),'edited summary review')
  assert.equal(await js(`${button('保存此摘要')}.disabled`),true)
  await js("document.querySelector('.look-recollection input[type=checkbox]').click()")
  await click('保存此摘要')
  await until(async()=>await js(counts)===1,'one stored summary')
  await until(()=>js("document.querySelector('.look-recollection ol')?.innerText.includes('合成回归备注')"),'edited summary displayed')
  await click('删除摘要')
  await click('确认删除摘要')
  await until(async()=>await js(counts)===0,'deleted summary')
  console.log('PASS Chrome: course summary requires a reviewed version, saves the edited note, and can be deleted')

  await call('Page.addScriptToEvaluateOnNewDocument',{source:`
    sessionStorage.removeItem('trace.session_id')
    localStorage.removeItem('trace.voice-enabled')
    window.traceSpoken=[]
    window.speechSynthesis.speak=utterance=>{
      window.traceSpoken.push(utterance.text)
      queueMicrotask(()=>{utterance.onstart?.();utterance.onend?.()})
    }
  `})
  await call('Page.navigate',{url:origin+'/story'})
  await until(()=>js("!!document.querySelector('.story-voice summary')"),'story dialogue disclosure')
  await js("document.querySelector('.story-voice summary').click()")
  assert.equal(await js("document.querySelector('.story-voice').open"),true)
  const storyStatus=".story-voice .story-reply[aria-live='polite'], .story-voice .story-reply[role='status']"
  assert.equal(await js(`!!document.querySelector(${JSON.stringify(storyStatus)})`),true)
  await submit('今天我想聊一件虚构的小事。','#story-message')
  await until(()=>js(`document.querySelector(${JSON.stringify(storyStatus)})?.textContent.trim()`),'accessible story reply')
  assert.deepEqual(await js('window.traceSpoken'),[])
  assert.deepEqual(await js('window.traceMediaRequests'),[])
  console.log('PASS Chrome: Story text shows an accessible reply without speech or microphone use')

  await call('Page.navigate',{url:origin+'/'})
  await click('朗读欢迎与操作说明')
  assert.equal(await js('window.traceSpoken.length'),1)
  assert.deepEqual(await js('window.traceMediaRequests'),[])
  console.log('PASS Chrome: explicit welcome reads aloud without microphone use')
}finally{
  socket.close()
}
