/** Chrome fake camera smoke test against an isolated TRACE backend. */
import assert from 'node:assert/strict'
import {setTimeout as delay} from 'node:timers/promises'

const [appUrl, debugUrl, extra] = process.argv.slice(2)
const verifyMicrophone = extra === '--media'
assert(appUrl && debugUrl, 'Usage: node scripts/verify_local_vision_browser.mjs APP_URL CHROME_DEBUG_URL [--media]')
const targets = await (await fetch(new URL('/json/list', debugUrl))).json()
const target = targets.find(item => item.type === 'page')
assert(target, 'An isolated Chrome page must be open')
const cdp = new WebSocket(target.webSocketDebuggerUrl)
const pending = new Map()
let id = 0
await new Promise((resolve, reject) => {
  cdp.addEventListener('open', resolve, {once: true})
  cdp.addEventListener('error', reject, {once: true})
})
cdp.addEventListener('message', ({data}) => {
  const message = JSON.parse(data)
  const request = pending.get(message.id)
  if (request) {
    pending.delete(message.id)
    clearTimeout(request.timeout)
    if (message.error) request.reject(new Error(message.error.message))
    else request.resolve(message.result)
  }
})
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const next = ++id
    const timeout = setTimeout(() => { pending.delete(next); reject(new Error(method + ' timed out')) }, 10000)
    pending.set(next, {resolve, reject, timeout})
    cdp.send(JSON.stringify({id: next, method, params}))
  })
}
async function evaluate(expression) {
  const {result, exceptionDetails} = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true})
  if (exceptionDetails) throw new Error(exceptionDetails.exception?.description ?? exceptionDetails.text)
  return result.value
}
async function until(expression, description) {
  // A cold local MediaPipe start may spend more than ten seconds loading the\n  // model and building caches before the first observation reaches the UI.\n  for (let attempt = 0; attempt < 300; attempt++) {
    if (await evaluate(expression)) return
    await delay(100)
  }
  throw new Error('Timed out waiting for ' + description)
}
function click(label) {
  return evaluate(`button(${JSON.stringify(label)}).click()`)
}

try {
  await send('Page.enable')
  await send('Page.addScriptToEvaluateOnNewDocument', {source: `
    globalThis.button = (label) => [...document.querySelectorAll('button')].find(node => node.textContent.trim() === label)
    globalThis.visionRequests = []
    globalThis.traceDocumentId = crypto.randomUUID()
    globalThis.testStreams = []
    const media = navigator.mediaDevices
    if (media) {
      const getUserMedia = media.getUserMedia.bind(media)
      media.getUserMedia = async constraints => {
        const stream = await getUserMedia(constraints)
        testStreams.push(stream)
        return stream
      }
    }
    const watchedEvents = new Set(['pagehide','visibilitychange','online','offline','beforeunload'])
    const listeners = new Map()
    const add = EventTarget.prototype.addEventListener
    const remove = EventTarget.prototype.removeEventListener
    const track = (target, type, listener, shouldAdd) => {
      if ((target !== document && target !== globalThis) || !watchedEvents.has(type)) return
      const key = (target === document ? 'document' : 'window') + ':' + type
      if (!listeners.has(key)) listeners.set(key, new Set())
      const callbacks = listeners.get(key)
      if (shouldAdd) callbacks.add(listener)
      else callbacks.delete(listener)
    }
    EventTarget.prototype.addEventListener = function(type, listener, options) {
      track(this,type,listener,true)
      return add.call(this,type,listener,options)
    }
    EventTarget.prototype.removeEventListener = function(type, listener, options) {
      track(this,type,listener,false)
      return remove.call(this,type,listener,options)
    }
    globalThis.mediaListenerCounts = () => Object.fromEntries([...listeners.entries()]
      .filter(([,callbacks]) => callbacks.size > 0)
      .sort(([first],[second]) => first.localeCompare(second))
      .map(([key,callbacks]) => [key,callbacks.size]))
    const original = globalThis.fetch
    globalThis.fetch = (input, options) => {
      const path = new URL(input, location.href).pathname
      if (path.startsWith('/api/vision/')) visionRequests.push({path, method: options?.method ?? 'GET'})
      return original(input, options)
    }
  `})
  await send('Page.navigate', {url: new URL('/explore', appUrl).toString()})
  await until("!!globalThis.button?.('开启摄像头')", 'camera controls')
  await click('开启摄像头')
  await until("document.querySelector('video')?.readyState >= 2 && !button('同意本地单帧检查')?.disabled", 'live fake camera')
  assert.deepEqual(await evaluate('visionRequests'), [], 'preview must send zero vision requests')
  await click('同意本地单帧检查')
  await until("button('检查新画面')?.disabled === false", 'scoped manual grant')
  await click('检查新画面')
  await until("['quality', 'uncertain', 'observed'].includes(document.querySelector('.local-vision-controls')?.dataset.analysisState)", 'local observation')
  const sid = await evaluate("sessionStorage.getItem('trace.session_id')")
  assert(sid, 'session created')
  const observationsUrl = JSON.stringify('/api/vision/local/' + encodeURIComponent(sid))
  const observation = await evaluate(`fetch(${observationsUrl}).then(r=>r.json()).then(r=>r.observations[0])`)
  assert.equal(observation.source, 'local_mediapipe')
  assert.equal(observation.orientation, 'unmirrored')
  assert.equal(observation.comparison, null)
  assert.equal(observation.calibrated, false)
  assert(observation.frame_id && observation.quality)
  assert.equal(await evaluate("visionRequests.some(entry=>entry.path==='/api/vision/check')"), false)
  await click('关闭摄像头')
  await until("!document.querySelector('video')?.srcObject && button('检查新画面')?.disabled", 'released video and controls')
  await until(`fetch(${observationsUrl}).then(r=>r.json()).then(r=>r.observations.length===0)`, 'server evidence cleared')

  await click('开启摄像头')
  await until("document.querySelector('video')?.readyState >= 2 && !button('同意本地单帧检查')?.disabled", 'reopened fake camera')
  await click('同意本地单帧检查')
  await until("button('检查新画面')?.disabled === false", 'new manual grant before device loss')
  await click('检查新画面')
  await until(`fetch(${observationsUrl}).then(r=>r.json()).then(r=>r.observations.length===1)`, 'server observation before device loss')
  const priorRevocations = await evaluate("visionRequests.filter(entry=>entry.method==='DELETE').length")
  await evaluate(`(()=>{
    const track=document.querySelector('video').srcObject.getVideoTracks()[0]
    track.stop()
    track.dispatchEvent(new Event('ended'))
  })()`)
  await until("!document.querySelector('video')?.srcObject && button('检查新画面')?.disabled", 'detached camera after device loss')
  await until(`visionRequests.filter(entry=>entry.method==='DELETE').length > ${priorRevocations}`, 'permit revocation after device loss')
  await until(`fetch(${observationsUrl}).then(r=>r.json()).then(r=>r.observations.length===0)`, 'server evidence cleared after device loss')
  await click('开启摄像头')
  await until("document.querySelector('video')?.readyState >= 2 && !button('同意本地单帧检查')?.disabled", 'manual restart after device loss')
  assert.equal(await evaluate("button('检查新画面')?.disabled"), true, 'restarted preview needs fresh consent')
  await click('关闭摄像头')
  await until("!document.querySelector('video')?.srcObject", 'camera released before reload')
  console.log('PASS Chrome fake camera: track end clears local permit and observation; restart needs fresh consent')

  const documentId = await evaluate('traceDocumentId')
  await send('Page.reload')
  await until(`globalThis.traceDocumentId && globalThis.traceDocumentId!==${JSON.stringify(documentId)} && !!globalThis.button?.('开启摄像头')`, 'restored page')
  assert.equal(await evaluate("!!document.querySelector('video')?.srcObject"), false)
  assert.equal(await evaluate("button('检查新画面')?.disabled"), true)
  if (verifyMicrophone) {
    const listeners = await evaluate('mediaListenerCounts()')
    for (let cycle = 0; cycle < 3; cycle++) {
      await click('开启语音引导')
      await until("testStreams.some(s=>s.getAudioTracks().some(t=>t.readyState==='live'))", 'live fake microphone')
      await until("fetch('/local-voice/health').then(r=>r.json()).then(r=>r.connections===1)", 'local voice socket')
      await click('关闭麦克风')
      await until("testStreams.flatMap(s=>s.getTracks()).every(t=>t.readyState==='ended')", 'all local tracks ended')
      await until("fetch('/local-voice/health').then(r=>r.json()).then(r=>r.connections===0)", 'voice socket released')
      assert.deepEqual(await evaluate('mediaListenerCounts()'), listeners, 'media cycles must not accumulate window/document listeners')
    }
    console.log('PASS Chrome fake microphone: three start/close cycles ended tracks, released sockets and kept listener counts stable')
  }
  console.log('PASS Chrome fake camera: preview isolated, scoped local POST, native quality, close clears evidence, reload requires consent')
} finally {
  cdp.close()
}
