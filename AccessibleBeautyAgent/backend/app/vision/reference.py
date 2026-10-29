"""Shared reference analysis adapter; extends existing vision architecture."""
from typing import Protocol
from app.config import ROOT
from app.services.model_client import RemoteModelClient
import base64

class ReferenceAnalyzer(Protocol):
    def analyze(self,image:bytes)->dict:...

class MockReferenceAnalyzer:
    def analyze(self,image):
        return {'scene':[],'overall':{'intensity':None,'contrast':None},'base':{'finish':None,'coverage':None},'blush':{'visible':None,'placement':None,'intensity':None,'finish':None},'lip':{'visible':None,'saturation':None,'finish':None},'eye':{'definition':None},'quality':{'face_visible':None,'lighting':None,'pose':None},'confidence':None,'notes':'MOCK DRAFT — no actual visual interpretation performed.','uncertainty_notes':'所有属性未知，待人工填写；未调用外部 AI。','ai_generated_draft':True,'human_verified':False,'verified':False,'status':'AI_GENERATED'}

class RemoteVisionReferenceAnalyzer:
    def __init__(self,settings,provider=None):
        self.provider=provider or settings.reference_provider
        self.client=RemoteModelClient(settings,self.provider)
        self.model=settings.deepseek_vision_model if self.provider=='deepseek' else settings.vision_model
    def analyze(self,image):
        from app.knowledge.vocabulary import Vocabulary
        import json
        prompt=(ROOT/'prompts/reference_analysis.md').read_text(encoding='utf-8')+'\nControlled vocabulary: '+json.dumps(Vocabulary().values,ensure_ascii=False)
        result=self.client.chat_json(self.model,prompt,[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(image).decode()}}])
        result.update(human_verified=False,verified=False,ai_generated_draft=True,status='AI_GENERATED')
        return result

VisionReferenceAnalyzer=ReferenceAnalyzer
MockVisionReferenceAnalyzer=MockReferenceAnalyzer
class QwenVisionReferenceAnalyzer(RemoteVisionReferenceAnalyzer):
    def __init__(self,settings):super().__init__(settings,'qwen')

def reference_analyzer(settings):
    return MockReferenceAnalyzer() if settings.reference_provider=='mock' else RemoteVisionReferenceAnalyzer(settings)
