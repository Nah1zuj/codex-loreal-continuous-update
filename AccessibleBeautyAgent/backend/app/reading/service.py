"""Surface reading is independent of makeup checks; frames are never persisted."""
import base64
from typing import Literal
from pydantic import BaseModel,Field

class ReadingResult(BaseModel):
    status:Literal['READ','UNCERTAIN']='UNCERTAIN'
    label_kind:Literal['product','garment']='product'
    composition:str|None=None
    uncertain_characters:list[str]=Field(default_factory=list,max_length=20)
    summary:str
    shade:str|None=None
    instructions:str|None=None
    full_text:str|None=None
    confidence:float=Field(default=0,ge=0,le=1)
    simulated:bool=False

class ReadingService:
    def __init__(self,settings):self.settings=settings
    def read(self,image,demo=False,label_kind="product",locale="zh-CN"):
        if self.settings.reading_provider=='mock':
            if demo:
                if not self.settings.developer_mode:raise PermissionError('演示标签仅在本地开发演示中可用。')
                if label_kind=='garment':return ReadingResult(status='READ',label_kind='garment',summary='这是虚构衣物吊牌，仅演示读取流程：100% 棉。',composition='100% 棉（虚构演示）',instructions='洗护文字示例；真实洗护以你的衣物标签为准。',full_text='虚构 TRACE 吊牌：100% 棉。不是你真实衣服的成分。',simulated=True).model_dump()
                return ReadingResult(status='READ',summary='这是虚构的 TRACE 演示标签，仅用于体验阅读流程。色号为 02。',shade='02（虚构演示色号）',instructions='演示文字：先取少量，再按你的习惯使用。',full_text='TRACE 演示标签。色号 02。先取少量，再按你的习惯使用。此标签不是实际产品资料。',confidence=0,simulated=True).model_dump()
            return ReadingResult(label_kind=label_kind,summary='现在还不能读取这张图片。本地演示不会识别真实标签；可以选择示例标签体验，或稍后接入阅读服务。',simulated=True).model_dump()
        if not self.settings.allow_remote_ai:raise PermissionError('外部 AI 调用已关闭（ALLOW_REMOTE_AI=false）。')
        if demo:raise PermissionError('远程阅读不使用虚构演示标签。')
        from app.services.model_client import RemoteModelClient
        provider=self.settings.reading_provider
        model=self.settings.deepseek_vision_model if provider=='deepseek' else self.settings.vision_model
        system='Read only clearly visible printed product label or screen text. Do not infer product claims, identity or facts. Return JSON summary, shade, instructions, full_text, confidence (0..1). Unknown fields null. If not clearly readable confidence must be low. Never guess shade numbers. Preserve printed full_text in its original language.'
        from app.policies.registry import PolicyRegistry
        system+='\n'+PolicyRegistry().system('accessibility_policy','material_description_policy')+' Return composition (only for garment labels), uncertain_characters list, and no guessed percentages.'
        system += ' Write generated summary and instructions in English.' if locale=='en' else ' Write generated summary and instructions in simplified Chinese.'
        encoded=base64.b64encode(image).decode()
        data=RemoteModelClient(self.settings,provider).chat_json(model,system,[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+encoded}}])
        data['simulated']=False
        data['label_kind']=label_kind
        result=ReadingResult.model_validate(data)
        if result.confidence<self.settings.confidence_high or result.uncertain_characters:
            return ReadingResult(label_kind=label_kind,summary='这个信息我现在读不清楚，我不想随便猜。可以把包装靠近一点、保持平整，再试一次。').model_dump()
        result.status='READ'
        return result.model_dump()
