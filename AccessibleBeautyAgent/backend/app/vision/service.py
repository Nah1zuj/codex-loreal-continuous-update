from app.vision.gate import LocalFaceGate, demo_gate
from app.vision.providers import MockVisionProvider, RemoteQwenVisionProvider,RemoteDeepSeekVisionProvider
from app.vision.consensus import aggregate
from app.schemas.models import VisualResult
from app.vision.language import accessible_result

class VisionService:
    def __init__(self, settings, gate=None, provider=None):
        self.settings = settings
        self.gate = gate or LocalFaceGate()
        self.provider = provider or (MockVisionProvider() if settings.vision_provider=='mock' else (RemoteDeepSeekVisionProvider(settings) if settings.vision_provider=='deepseek' else RemoteQwenVisionProvider(settings)))

    def check(self, task, images, context=None, demo=False):
        context = context or {}
        video_sample = context.get("capture_kind") == "video_sample"
        if len(images)!=(1 if video_sample else 3) and not demo:
            raise ValueError('请提交三帧图片。')
        if demo and (not self.settings.developer_mode or self.settings.vision_provider!='mock'):
            raise PermissionError('模拟场景仅在 mock 开发模式可用。')
        context = context or {}
        gates = [demo_gate()]*3 if demo else [self.gate.evaluate(x) for x in images]
        failed = next((g for g in gates if not g['gate_pass']),None)
        if failed:
            return {'gate':failed,'gates':gates,'visual':None,'message':failed['failure_reason']}
        frames = [self.provider.evaluate(task,x,context) for x in (images if not demo else [b'']*3)]
        if video_sample and not demo:
            frame = VisualResult.model_validate(frames[0])
            if frame.confidence < self.settings.confidence_min or frame.image_quality == "poor" or frame.status == "UNCERTAIN":
                frame = VisualResult(task=frame.task,status="UNCERTAIN",confidence=0,image_quality=frame.image_quality,simulated=frame.simulated)
            visual = {**frame.model_dump(), "frame_results": [frames[0]], "sampled": True}
        else:
            visual = aggregate(frames,self.settings.confidence_min)
        return {'gate':gates[0],'gates':gates,'visual':visual,'message':accessible_result(visual,self.settings)}
