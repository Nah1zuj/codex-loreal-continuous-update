import {afterEach,expect,it,vi} from 'vitest'
import {CameraStreamController} from './cameraStream'
import {captureVideoFrame} from './frameAnalysis'
afterEach(()=>vi.unstubAllGlobals())
function stream(){
 const tracks=Array.from({length:2},()=>{
  const track=Object.assign(new EventTarget(),{readyState:'live'})
  return Object.assign(track,{stop:vi.fn(()=>{track.readyState='ended'})})
 })
 return {media:{getTracks:()=>tracks,getVideoTracks:()=>tracks} as unknown as MediaStream,tracks}
}
function video(){return {srcObject:null,play:vi.fn(async()=>{})} as unknown as HTMLVideoElement}
function deferred<T>(){let resolve!:(v:T)=>void;let reject!:(e:unknown)=>void;const promise=new Promise<T>((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject}}
it('explicit request uses video-only ideal facing constraints',async()=>{const s=stream(),v=video(),getUserMedia=vi.fn(async()=>s.media),c=new CameraStreamController({getUserMedia});expect(c.state).toBe('off');expect(getUserMedia).not.toHaveBeenCalled();const p=c.requestPreview(v,'environment');expect(c.state).toBe('requesting');expect(await p).toBe('live');expect(v.srcObject).toBe(s.media);expect(v.play).toHaveBeenCalledOnce();expect(getUserMedia).toHaveBeenCalledWith({audio:false,video:{facingMode:{ideal:'environment'}}})})
it.each(['NotAllowedError','PermissionDeniedError'])('%s denies without retry',async name=>{const getUserMedia=vi.fn(async()=>{throw {name}}),c=new CameraStreamController({getUserMedia});expect(await c.requestPreview(video())).toBe('denied');expect(c.error).toMatch(/权限/);await Promise.resolve();expect(getUserMedia).toHaveBeenCalledOnce()})
it.each(['NotFoundError','DevicesNotFoundError','NotSupportedError'])('%s unavailable',async name=>{const c=new CameraStreamController({getUserMedia:async()=>{throw {name}}});expect(await c.requestPreview(video())).toBe('unavailable');expect(c.error).toMatch(/摄像头/)})
it('missing mediaDevices unavailable',async()=>{vi.stubGlobal('navigator',{});expect(await new CameraStreamController().requestPreview(video())).toBe('unavailable')})
it('switch stops old tracks before replacement request',async()=>{const a=stream(),b=stream(),v=video(),getUserMedia=vi.fn().mockResolvedValueOnce(a.media).mockImplementationOnce(async()=>{a.tracks.forEach(t=>expect(t.stop).toHaveBeenCalledOnce());expect(v.srcObject).toBeNull();return b.media}),c=new CameraStreamController({getUserMedia});await c.requestPreview(v);expect(await c.switchFacingMode()).toBe('live');expect(getUserMedia).toHaveBeenLastCalledWith({audio:false,video:{facingMode:{ideal:'environment'}}});expect(v.srcObject).toBe(b.media)})
it('switch while off does not request hardware',async()=>{const getUserMedia=vi.fn(),c=new CameraStreamController({getUserMedia});expect(await c.switchFacingMode()).toBe('off');expect(getUserMedia).not.toHaveBeenCalled()})
it.each(['route exit','unmount'])('caller cleanup on %s stops all tracks and detaches',async()=>{const s=stream(),v=video(),c=new CameraStreamController({getUserMedia:async()=>s.media});await c.requestPreview(v);const cleanup=()=>c.stop();cleanup();cleanup();expect(c.state).toBe('off');expect(v.srcObject).toBeNull();s.tracks.forEach(t=>expect(t.stop).toHaveBeenCalledOnce())})
it('permission after stop never attaches and stops tracks',async()=>{const d=deferred<MediaStream>(),s=stream(),v=video(),c=new CameraStreamController({getUserMedia:()=>d.promise});const p=c.requestPreview(v);c.stop();d.resolve(s.media);expect(await p).toBe('off');expect(v.srcObject).toBeNull();expect(v.play).not.toHaveBeenCalled();s.tracks.forEach(t=>expect(t.stop).toHaveBeenCalledOnce())})
it.each(['resolve','reject'])('old permission %s cannot override latest request',async action=>{const d=deferred<MediaStream>(),a=stream(),b=stream(),v=video(),c=new CameraStreamController({getUserMedia:vi.fn().mockReturnValueOnce(d.promise).mockResolvedValueOnce(b.media)});const p=c.requestPreview(v);await c.requestPreview(v,'environment');if(action==='resolve')d.resolve(a.media);else d.reject({name:'NotAllowedError'});expect(await p).toBe('live');expect(c.error).toBeNull();expect(v.srcObject).toBe(b.media);if(action==='resolve')a.tracks.forEach(t=>expect(t.stop).toHaveBeenCalledOnce())})
it('play failure stops tracks and gives actionable error',async()=>{const s=stream(),v=video();vi.mocked(v.play).mockRejectedValue(new Error('blocked'));const c=new CameraStreamController({getUserMedia:async()=>s.media});expect(await c.requestPreview(v)).toBe('error');expect(c.error).toMatch(/重试|重新/);expect(v.srcObject).toBeNull();s.tracks.forEach(t=>expect(t.stop).toHaveBeenCalledOnce())})
it('late play rejection leaves replacement live',async()=>{const d=deferred<void>(),a=stream(),b=stream(),v=video();vi.mocked(v.play).mockReturnValueOnce(d.promise);const c=new CameraStreamController({getUserMedia:vi.fn().mockResolvedValueOnce(a.media).mockResolvedValueOnce(b.media)});const p=c.requestPreview(v);await Promise.resolve();await c.requestPreview(v,'environment');d.reject(new Error('late'));expect(await p).toBe('live');expect(v.srcObject).toBe(b.media);b.tracks.forEach(t=>expect(t.stop).not.toHaveBeenCalled())})
it('unexpected hardware failure provides manual retry guidance',async()=>{const c=new CameraStreamController({getUserMedia:async()=>{throw new Error('busy')}});expect(await c.requestPreview(video())).toBe('error');expect(c.error).toMatch(/重试|重新/)})
it('a queued end event from a replaced camera cannot close the current preview',async()=>{
 const old=stream(),current=stream(),element=video(),onEnded=vi.fn()
 const addListener=vi.spyOn(old.tracks[0],'addEventListener')
 const controller=new CameraStreamController({getUserMedia:vi.fn().mockResolvedValueOnce(old.media).mockResolvedValueOnce(current.media)})
 controller.onUnexpectedEnd=onEnded
 await controller.requestPreview(element)
 const queued=addListener.mock.calls.find(([type])=>type==='ended')?.[1]
 expect(typeof queued).toBe('function')
 await controller.switchFacingMode()
 if(typeof queued==='function')queued.call(old.tracks[0],new Event('ended'))
 expect(controller.state).toBe('live')
 expect(element.srcObject).toBe(current.media)
 expect(current.tracks[0].stop).not.toHaveBeenCalled()
 expect(onEnded).not.toHaveBeenCalled()
})
it('does not capture cached video after all tracks have ended',()=>{
 const {media,tracks}=stream()
 tracks.forEach(track=>{track.readyState='ended'})
 const createElement=vi.fn()
 vi.stubGlobal('document',{createElement})
 const retained={srcObject:media,readyState:2,videoWidth:320,videoHeight:240} as HTMLVideoElement
 expect(captureVideoFrame(retained)).toBeNull()
 expect(createElement).not.toHaveBeenCalled()
})
