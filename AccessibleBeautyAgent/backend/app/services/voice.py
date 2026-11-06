from typing import Protocol

class RealtimeVoiceProvider(Protocol):
    def connect(self, session_id: str) -> dict: ...

class BrowserVoiceFallback:
    def connect(self, session_id):
        return {'provider':'browser','session_id':session_id,'realtime':False,'capabilities':['text_chat','browser_tts','push_to_talk'], 'notice':'浏览器语音识别依浏览器支持，可能使用浏览器厂商的云服务；文本模式始终可用。'}

class QwenRealtimePlaceholder:
    def connect(self, session_id):
        return {'provider':'qwen','session_id':session_id,'realtime':False,'status':'PLACEHOLDER','capabilities':['text_chat','browser_tts','push_to_talk'],'notice':'Qwen realtime transport is not implemented. Use browser fallbacks.'}
