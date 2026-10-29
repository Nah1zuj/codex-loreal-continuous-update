import io
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel,StrictBool,Field
from PIL import Image
from app.vision.gate import decode_image
from app.reading.service import ReadingService

class ReadingRequest(BaseModel):
    locale:Literal['zh-CN','en']='zh-CN'
    image:str|None=Field(default=None,max_length=6_000_000)
    label_kind:Literal['product','garment']='product'
    demo:StrictBool=False
    explicit_consent:StrictBool=False

def build_reading_router(settings):
    router=APIRouter(prefix='/api/reading');service=ReadingService(settings)
    @router.post('/read')
    def read(body:ReadingRequest):
        if body.explicit_consent is not True:raise PermissionError('请先允许这一次读取。你也可以选择暂时不用。')
        if body.demo:
            if body.image:raise ValueError('演示标签不接收真实图片。')
            return service.read(b'',demo=True,label_kind=body.label_kind,locale=body.locale)
        if not body.image:raise ValueError('请拍摄一张标签画面。')
        raw=decode_image(body.image)
        with Image.open(io.BytesIO(raw)) as im:
            im=im.convert('RGB');im.thumbnail((1024,1024));out=io.BytesIO();im.save(out,format='JPEG',quality=85)
        return service.read(out.getvalue(),demo=False,label_kind=body.label_kind,locale=body.locale)
    return router
