import type { Session } from '../types'
export const stageLabels:Record<Session['stage'],string>={INIT:'初始化',ONBOARDING:'欢迎',INTENT:'了解你的意图',CLARIFY:'确认使用场景',LOOK_SELECTED:'妆容方向已选',GUIDE:'一步一步引导',CHECK_REQUESTED:'请求检查',CAMERA_CONSENT:'等待相机同意',VISION_GATE:'图像质量检查',VISION_CHECK:'视觉检查',VERIFY:'检查完成',FEEDBACK:'你的体验反馈',MEMORY_CONSENT:'等待记忆同意',COMPLETE:'会话已结束'}
export function canAdvance(s:Session|null){return !!s&&['LOOK_SELECTED','GUIDE','VERIFY'].includes(s.stage)}
