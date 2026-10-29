import type {CameraState} from '../types'

export type CameraFacingMode = 'user' | 'environment'
type CameraDevices = Pick<MediaDevices, 'getUserMedia'>

/** Local preview only. Call request/switch from camera gestures and stop on route exit/unmount.
 * Camera permission is independent of microphone and remote frame-analysis consent.
 */
export class CameraStreamController {
  private generation = 0
  private stream: MediaStream | null = null
  private video: HTMLVideoElement | null = null
  private facingMode: CameraFacingMode = 'user'
  private currentState: CameraState = 'off'
  private currentError: string | null = null

  constructor(private readonly mediaDevices: CameraDevices | undefined = globalThis.navigator?.mediaDevices) {}

  get state(): CameraState { return this.currentState }
  get error(): string | null { return this.currentError }

  async requestPreview(video: HTMLVideoElement, facingMode: CameraFacingMode = 'user'): Promise<CameraState> {
    this.stop()
    const generation = this.generation
    this.video = video
    this.facingMode = facingMode
    this.currentState = 'requesting'
    if (!this.mediaDevices?.getUserMedia) {
      this.currentState = 'unavailable'
      this.currentError = '当前浏览器无法使用摄像头，请使用支持摄像头的浏览器。'
      return this.state
    }
    try {
      // ideal allows browsers with a single camera to provide their available camera.
      const stream = await this.mediaDevices.getUserMedia({audio:false, video:{facingMode:{ideal:facingMode}}})
      if (generation !== this.generation) {
        stream.getTracks().forEach(track => track.stop())
        return this.state
      }
      this.stream = stream
      video.srcObject = stream
      await video.play()
      if (generation === this.generation) this.currentState = 'live'
    } catch (error) {
      if (generation !== this.generation) return this.state
      this.releasePreview()
      const name = error && typeof error === 'object' && 'name' in error ? error.name : ''
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        this.currentState = 'denied'
        this.currentError = '摄像头权限被拒绝，请在浏览器设置中允许权限后手动重试。'
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError' || name === 'NotSupportedError') {
        this.currentState = 'unavailable'
        this.currentError = '未找到可用摄像头，请连接摄像头后手动重试。'
      } else {
        this.currentState = 'error'
        this.currentError = '无法启动摄像头预览，请检查摄像头是否被占用并手动重试。'
      }
    }
    return this.state
  }

  switchFacingMode(): Promise<CameraState> {
    if (!this.video || (this.state !== 'live' && this.state !== 'requesting')) return Promise.resolve(this.state)
    return this.requestPreview(this.video, this.facingMode === 'user' ? 'environment' : 'user')
  }

  stop(): void {
    ++this.generation
    this.releasePreview()
    this.currentState = 'off'
    this.currentError = null
  }

  private releasePreview(): void {
    this.stream?.getTracks().forEach(track => track.stop())
    this.stream = null
    if (this.video) this.video.srcObject = null
    this.video = null
  }
}
