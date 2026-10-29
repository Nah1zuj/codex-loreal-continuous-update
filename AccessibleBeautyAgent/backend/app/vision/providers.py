import base64
from typing import Protocol
from app.schemas.models import VisualResult
from app.config import ROOT

class VisionProvider(Protocol):
    def evaluate(self, task: str, image: bytes, context: dict) -> dict: ...

class MockVisionProvider:
    def evaluate(self, task, image, context):
        status = context.get('mock_status','BOTH' if task=='blush_presence' else 'APPLIED')
        return VisualResult(task=task,status=status,confidence=.9 if status!='UNCERTAIN' else .3,simulated=True).model_dump()

class RemoteQwenVisionProvider:
    def __init__(self, settings):
        from app.services.qwen import QwenClient
        self.client = QwenClient(settings)
        self.model = settings.vision_model
    def evaluate(self, task, image, context):
        prompt = (ROOT/'prompts'/('vision_blush.md' if task=='blush_presence' else 'vision_lip.md')).read_text(encoding='utf-8')
        from app.policies.registry import PolicyRegistry
        prompt+='\n'+PolicyRegistry().system('accessibility_policy','visual_feedback_policy')
        content = [{'type':'text','text':f'Task: {task}. User left/right are anatomical, not image left/right.'}, {'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(image).decode()}}]
        raw = self.client.chat_json(self.model,prompt,content)
        raw['task'] = task
        raw['simulated'] = False
        return VisualResult.model_validate(raw).model_dump()

class RemoteDeepSeekVisionProvider(RemoteQwenVisionProvider):
    def __init__(self,settings):
        from app.services.model_client import RemoteModelClient
        self.client=RemoteModelClient(settings,'deepseek')
        self.model=settings.deepseek_vision_model
