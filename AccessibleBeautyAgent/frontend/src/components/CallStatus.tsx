import {humanError} from '../content/errors'
import {useTrace} from '../content/Locale'
import type {CallSnapshot} from '../realtime/callController'

export function CallStatus({snapshot,announce=true}:{snapshot:CallSnapshot;announce?:boolean}){
 const {t,locale}=useTrace()
 const labels={
  idle:t('准备就绪','Ready'),
  requesting_permission:t('正在连接麦克风与本地语音','Connecting microphone and local voice'),
  listening:t('正在聆听 · 本机识别','Listening · on this computer'),
  thinking:t('正在思考','Thinking'),
  speaking:t('正在回复','Speaking'),
  paused:t('语音尚未开启','Voice not enabled'),
  quiet_wake:t('暂停回应，仍在侦听唤醒词','Replies paused; listening for wake phrase'),
  ended:t('麦克风已关闭','Microphone closed'),
  error:t('语音暂不可用','Voice unavailable'),
 }
 const {state,recording,transcribing}=snapshot
 const progress=state==='requesting_permission'||state==='listening'?snapshot.progress:undefined
 let label=labels[state]
 if(recording)label=t('正在记录这一段','Recording this request')
 if(transcribing)label=progress||t('正在转写这一段','Transcribing this request')

 return <div data-call-state={state} role={announce?'status':undefined} aria-live={announce?'polite':undefined} aria-atomic={announce?true:undefined}>
  <strong>{label}</strong>
  {progress&&!transcribing?<p>{progress}</p>:null}
  {snapshot.error?<p>{humanError(snapshot.error,locale)}</p>:null}
 </div>
}
