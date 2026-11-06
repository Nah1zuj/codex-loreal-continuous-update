import {afterEach, expect, it, vi} from 'vitest'
import {FrameAnalysisScheduler} from './frameAnalysis'
import {analyzeVideoSample} from '../api/client'
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals()})
const setup = (extra = {}) => {
  const capture = vi.fn(()=> 'data:image/png;base64,synthetic')
  const send = vi.fn(async()=>({visual:{status:'UNCERTAIN'}}))
  const onResult = vi.fn()
  const scheduler = new FrameAnalysisScheduler({capture,send,hasChanged:()=>true})
  scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'blush_presence',cameraConsent:true,remoteFrameConsent:true,onResult,intervalMs:100,...extra})
  return {scheduler,capture,send,onResult}
}
it('manual initial analysis is immediate but every attempt respects minimum 2500ms',async()=>{
 vi.useFakeTimers();const x=setup();await x.scheduler.analyzeNow('manual');expect(x.send).toHaveBeenCalledTimes(1)
 await x.scheduler.analyzeNow('manual');await vi.advanceTimersByTimeAsync(2499);expect(x.send).toHaveBeenCalledTimes(1)
 await vi.advanceTimersByTimeAsync(1);expect(x.send).toHaveBeenCalledTimes(2);x.scheduler.stop()
})
it('single flight drops busy attempts without a queued request',async()=>{
 vi.useFakeTimers();let resolve!:(x:unknown)=>void
 const send=vi.fn(()=>new Promise(r=>{resolve=r}));const scheduler=new FrameAnalysisScheduler({capture:()=> 'frame',send,hasChanged:()=>true})
 scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence',cameraConsent:true,remoteFrameConsent:true})
 const first=scheduler.analyzeNow('manual');await Promise.resolve();await vi.advanceTimersByTimeAsync(5000);await scheduler.analyzeNow('manual');expect(send).toHaveBeenCalledTimes(1)
 resolve({});await first;expect(send).toHaveBeenCalledTimes(1);scheduler.stop()
})
it('unchanged frames skip sending and stop cancels timers',async()=>{
 vi.useFakeTimers();const send=vi.fn(async()=>({}));const scheduler=new FrameAnalysisScheduler({capture:()=> 'same',send,hasChanged:(a,b)=>a!==b})
 scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence',cameraConsent:true,remoteFrameConsent:true})
 await scheduler.analyzeNow('manual');await vi.advanceTimersByTimeAsync(2500);expect(send).toHaveBeenCalledTimes(1);scheduler.stop();await vi.advanceTimersByTimeAsync(10000);expect(send).toHaveBeenCalledTimes(1)
})
it('stop rejects late result even when transport ignores cancellation',async()=>{
 vi.useFakeTimers();let resolve!:(x:unknown)=>void;const onResult=vi.fn()
 const scheduler=new FrameAnalysisScheduler({capture:()=> 'frame',send:()=>new Promise(r=>{resolve=r}),hasChanged:()=>true})
 scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence',cameraConsent:true,remoteFrameConsent:true,onResult})
 const first=scheduler.analyzeNow('manual');await Promise.resolve();scheduler.stop();resolve({});await first;expect(onResult).not.toHaveBeenCalled()
})
it('local preview consent does not capture or transmit without remote consent',async()=>{
 vi.useFakeTimers();const x=setup({remoteFrameConsent:false});await x.scheduler.analyzeNow('manual');await vi.advanceTimersByTimeAsync(5000);expect(x.capture).not.toHaveBeenCalled();expect(x.send).not.toHaveBeenCalled();x.scheduler.stop()
})
it('API helper refuses false remote consent before fetch',async()=>{
 const fetch=vi.fn();vi.stubGlobal('fetch',fetch)
 await expect(analyzeVideoSample({session_id:'s',task:'lip_presence',images:['frame'],capture_kind:'video_sample',remote_frame_consent:false})).rejects.toThrow(/consent/i);expect(fetch).not.toHaveBeenCalled()
})

it('small pixel noise skips analysis while a meaningful local change is sent',async()=>{
 vi.useFakeTimers();let pixel=100;const send=vi.fn(async()=>({}))
 const scheduler=new FrameAnalysisScheduler({capture:()=>({image:'jpeg-'+pixel,pixels:new Uint8ClampedArray([pixel,pixel,pixel,255])}),send})
 scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence',cameraConsent:true,remoteFrameConsent:true})
 await scheduler.analyzeNow('manual');pixel=101;await vi.advanceTimersByTimeAsync(2500);expect(send).toHaveBeenCalledTimes(1)
 pixel=150;await vi.advanceTimersByTimeAsync(2500);expect(send).toHaveBeenCalledTimes(2);scheduler.stop()
})
it('injected local analysis works without permitting remote transmission',async()=>{
 vi.useFakeTimers();const localAnalyze=vi.fn(async()=>({local:true}));const send=vi.fn();const onResult=vi.fn()
 const scheduler=new FrameAnalysisScheduler({capture:()=> 'frame',localAnalyze,send})
 scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence',cameraConsent:true,remoteFrameConsent:false,onResult})
 await scheduler.analyzeNow('manual');expect(localAnalyze).toHaveBeenCalledTimes(1);expect(send).not.toHaveBeenCalled();expect(onResult).toHaveBeenCalledWith({local:true});scheduler.stop()
})
it('manual analysis can revisit unchanged pixels after the configured interval',async()=>{
 vi.useFakeTimers();const send=vi.fn(async()=>({}));const scheduler=new FrameAnalysisScheduler({capture:()=> 'same',send})
 scheduler.start({video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence',cameraConsent:true,remoteFrameConsent:true,intervalMs:3000})
 await scheduler.analyzeNow('manual');await vi.advanceTimersByTimeAsync(2500);await scheduler.analyzeNow('manual');expect(send).toHaveBeenCalledTimes(1)
 await vi.advanceTimersByTimeAsync(500);await scheduler.analyzeNow('manual');expect(send).toHaveBeenCalledTimes(2);scheduler.stop()
})
it('restart does not overlap a transport that ignores abort',async()=>{
 vi.useFakeTimers();let resolve!:(x:unknown)=>void;const send=vi.fn(()=>new Promise(r=>{resolve=r}));const scheduler=new FrameAnalysisScheduler({capture:()=> 'frame',send})
 const options={video:{} as HTMLVideoElement,sessionId:'s',task:'lip_presence' as const,cameraConsent:true,remoteFrameConsent:true}
 scheduler.start(options);const first=scheduler.analyzeNow('manual');await Promise.resolve();scheduler.stop();scheduler.start(options)
 await vi.advanceTimersByTimeAsync(2500);expect(send).toHaveBeenCalledTimes(1);resolve({});await first;const second=scheduler.analyzeNow('manual');expect(send).toHaveBeenCalledTimes(2);resolve({});await second;scheduler.stop()
})
