import io
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError
from PIL import Image, ImageOps

from app.reading.service import ReadingService
from app.vision.gate import decode_image


class ReadingRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    locale:Literal['zh-CN','en']='zh-CN'
    image:str|None=Field(default=None,max_length=3_000_000)
    label_kind:Literal['product','garment']='product'
    demo:StrictBool=False
    explicit_consent:StrictBool=False
    remote_upload_consent:StrictBool=False
    authorized_provider:Literal['qwen','deepseek']|None=None


def build_reading_router(settings):
    router = APIRouter(prefix='/api/reading')
    service = ReadingService(settings)

    @router.get('/availability')
    def availability():
        return service.availability()

    @router.post('/read')
    def read(body:ReadingRequest):
        if body.explicit_consent is not True:
            raise PermissionError('请先允许这一次读取。你也可以选择暂时不用。')
        if body.demo:
            if body.image:
                raise ValueError('演示标签不接收真实图片。')
            return service.read(b'',demo=True,label_kind=body.label_kind,locale=body.locale)

        status = service.availability()
        if status['provider']=='mock':
            return service.read(b'',label_kind=body.label_kind,locale=body.locale)
        if body.remote_upload_consent is not True or body.authorized_provider!=status['provider']:
            raise HTTPException(403, {'code':'LABEL_UPLOAD_NOT_AUTHORIZED','message':'请先同意将这张标签图发送给当前读取服务。'})
        if status['status']!='configured':
            raise HTTPException(503, {'code':'LABEL_PROVIDER_UNAVAILABLE','message':'标签读取服务尚未配置或已停用。'})
        if not body.image:
            raise ValueError('请拍摄一张标签画面。')

        raw = decode_image(body.image)
        try:
            with Image.open(io.BytesIO(raw)) as source:
                image = ImageOps.exif_transpose(source).convert('RGB')
                image.thumbnail((1600,1600))
                with io.BytesIO() as output:
                    image.save(output,format='JPEG',quality=88)
                    pixels = output.getvalue()
        except OSError as error:
            raise ValueError('图片格式无效，请重新拍摄。') from error
        try:
            return service.read(pixels,label_kind=body.label_kind,locale=body.locale)
        except (ValidationError, ValueError, KeyError, IndexError, TypeError) as error:
            raise HTTPException(502, {'code':'INVALID_LABEL_RESPONSE','message':'读取服务返回的数据无法确认，请重试。'}) from error

    return router
