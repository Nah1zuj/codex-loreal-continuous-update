import assert from 'node:assert/strict'
import {setTimeout as delay} from 'node:timers/promises'

const [origin, debugUrl] = process.argv.slice(2)
assert(/^http:\/\/127\.0\.0\.1:\d+$/.test(origin ?? ''), 'Expected loopback app URL')
assert(/^http:\/\/127\.0\.0\.1:\d+$/.test(debugUrl ?? ''), 'Expected Chrome debug URL')

const targets = await (await fetch(new URL('/json/list', debugUrl))).json()
const target = targets.find(item => item.type === 'page')
assert(target, 'An isolated Chrome page must be open')
const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, {once: true})
  socket.addEventListener('error', reject, {once: true})
})

let nextId = 0
const pending = new Map()
socket.addEventListener('message', ({data}) => {
  const message = JSON.parse(data)
  if (!message.id) return
  const request = pending.get(message.id)
  if (!request) return
  pending.delete(message.id)
  clearTimeout(request.timeout)
  if (message.error) request.reject(new Error(message.error.message))
  else request.resolve(message.result)
})

function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++nextId
    const timeout = setTimeout(() => {
      pending.delete(id)
      reject(new Error(`${method} timed out`))
    }, 15000)
    pending.set(id, {resolve, reject, timeout})
    socket.send(JSON.stringify({id, method, params}))
  })
}

async function js(expression) {
  const {result, exceptionDetails} = await call('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  })
  if (exceptionDetails) throw new Error(exceptionDetails.exception?.description ?? exceptionDetails.text)
  return result.value
}

async function until(expression, description) {
  for (let attempt = 0; attempt < 120; attempt++) {
    try {
      const value = await js(expression)
      if (value) return value
    } catch {}
    await delay(100)
  }
  throw new Error(`Timed out waiting for ${description}`)
}

const button = label => `[...document.querySelectorAll('button')].find(node=>node.textContent.trim()===${JSON.stringify(label)})`

try {
  await call('Page.enable')
  await call('Browser.setPermission', {origin, permission: {name: 'microphone'}, setting: 'denied'})
  await call('Browser.setPermission', {origin, permission: {name: 'camera'}, setting: 'denied'})
  await call('Page.addScriptToEvaluateOnNewDocument', {source: `
    globalThis.traceMediaAttempts = []
    const original = navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices)
    if (original) navigator.mediaDevices.getUserMedia = async constraints => {
      try {
        const stream = await original(constraints)
        traceMediaAttempts.push({constraints, result: 'granted'})
        return stream
      } catch (error) {
        traceMediaAttempts.push({constraints, result: error?.name ?? 'error'})
        throw error
      }
    }
  `})

  await call('Page.navigate', {url: `${origin}/thread`})
  await until(`!!${button('按键语音输入')}`, 'microphone control')
  assert.equal(await js("navigator.permissions.query({name:'microphone'}).then(p=>p.state)"), 'denied')
  await js(`${button('按键语音输入')}.click()`)
  await until("traceMediaAttempts.some(item=>item.constraints?.audio && item.result!=='granted')", 'denied microphone request')
  assert.match(await js("traceMediaAttempts.find(item=>item.constraints?.audio)?.result"), /NotAllowed|PermissionDenied/)
  await until("document.body.innerText.includes('继续通过文字操作') || document.body.innerText.includes('麦克风许可') || document.body.innerText.includes('麦克风权限')", 'microphone denial guidance')
  assert.equal(await js("document.body.innerText.includes('正在连接麦克风与本地语音')"), false)

  await call('Page.navigate', {url: `${origin}/explore`})
  await until(`!!${button('开启摄像头')}`, 'camera control')
  assert.equal(await js("navigator.permissions.query({name:'camera'}).then(p=>p.state)"), 'denied')
  await js(`${button('开启摄像头')}.click()`)
  await until("traceMediaAttempts.some(item=>item.constraints?.video && item.result!=='granted')", 'denied camera request')
  assert.match(await js("traceMediaAttempts.find(item=>item.constraints?.video)?.result"), /NotAllowed|PermissionDenied/)
  await until("document.body.innerText.includes('摄像头权限被拒绝')", 'camera denial guidance')

  await call('Page.navigate', {url: `${origin}/thread`})
  await until("!!document.querySelector('#message')", 'text input after media denial')
  const initialAgentMessages = await js("document.querySelectorAll('.messages .agent').length")
  await js(`(()=>{const input=document.querySelector('#message');
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,'权限拒绝后继续文字');
    input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:'权限拒绝后继续文字'}));})()`)
  await until(`!${button('发送')}.disabled`, 'enabled text submission')
  await js(`${button('发送')}.click()`)
  await until(`document.querySelectorAll('.messages .agent').length>${initialAgentMessages}`, 'text reply after media denial')
  assert.equal(await js("[...document.querySelectorAll('.messages .user')].some(node=>node.textContent.includes('权限拒绝后继续文字'))"), true)
  assert.deepEqual(await js("traceMediaAttempts.map(item=>({audio:!!item.constraints?.audio,video:!!item.constraints?.video,result:item.result}))"), [])

  console.log('PASS Chrome denied microphone and camera permissions; denial guidance ended and text remained usable')
} finally {
  socket.close()
}
