"""Provider-neutral OpenAI-compatible transport; remote calls opt-in only."""
import json,logging
import httpx


class ModelServiceError(RuntimeError):
    """Public error text never includes credentials, URLs or provider response bodies."""
    def __init__(self,cause):
        status=cause.response.status_code if isinstance(cause,httpx.HTTPStatusError) else None
        if isinstance(cause,ImportError):message='模型代理组件缺失，请重新安装项目依赖。'
        elif isinstance(cause,httpx.TimeoutException):message='模型服务超时，请检查网络或稍后重试。'
        elif isinstance(cause,(httpx.ProxyError,httpx.ConnectError)):message='模型服务连接失败，请检查网络或代理。'
        elif status in (401,403):message='模型服务拒绝访问，请核对API Key和服务权限。'
        elif status==429:message='模型服务额度或请求频率受限，请检查账户后重试。'
        else:message='模型服务调用失败，请核对配置或稍后重试。'
        self.public_message=message
        logging.getLogger(__name__).warning('Model service failed: kind=%s status=%s',type(cause).__name__,status)
        super().__init__(message)

def parse_stream_line(line):
    if not line.startswith('data: '):return None
    payload=line[6:]
    if payload=='[DONE]':return None
    return json.loads(payload)

class RemoteModelClient:
    def __init__(self,settings,provider):
        self.settings=settings;self.provider=provider
    def request(self,path,body):
        if not self.settings.allow_remote_ai:raise PermissionError('外部 AI 调用已关闭（ALLOW_REMOTE_AI=false）。当前请使用 mock。')
        if self.provider=='deepseek':key,url=self.settings.deepseek_api_key,self.settings.deepseek_base_url
        elif self.provider=='qwen':key,url=self.settings.api_key,self.settings.base_url
        elif self.provider=='openai_compatible':key,url=self.settings.compatible_api_key,self.settings.compatible_base_url
        else:raise RuntimeError('Remote provider is not configured')
        if not key:raise RuntimeError(f'{self.provider}: API key is missing; use mock mode')
        if self.provider=='deepseek' and path=='/chat/completions':body={**body,'thinking':{'type':'disabled'}}
        try:
            with httpx.Client(timeout=self.settings.remote_timeout) as client:
                r=client.post(url.rstrip('/')+path,headers={'Authorization':f'Bearer {key}'},json=body)
                r.raise_for_status();return r.json()
        except (httpx.HTTPError,ImportError) as exc:raise ModelServiceError(exc) from exc
    def chat_json(self,model,system,content):
        if not model:raise RuntimeError('请先配置支持该任务的模型名称；图片模型与聊天模型可分别配置。')
        data=self.request('/chat/completions',{'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':content}],'response_format':{'type':'json_object'},'temperature':0})
        return json.loads(data['choices'][0]['message']['content'])

    async def stream_chat(self,model,messages,tools=None):
        """No transparent retry after output: duplicate speech/actions are unsafe."""
        if not self.settings.allow_remote_ai:raise PermissionError('Remote text calls are disabled')
        key,url=(self.settings.deepseek_api_key,self.settings.deepseek_base_url) if self.provider=='deepseek' else ((self.settings.compatible_api_key,self.settings.compatible_base_url) if self.provider=='openai_compatible' else (self.settings.api_key,self.settings.base_url))
        if not key or not model:raise RuntimeError('Text provider configuration is incomplete')
        body={'model':model,'messages':messages,'stream':True,'stream_options':{'include_usage':True},'max_tokens':1200,'temperature':0.5}
        if self.provider=='deepseek':body['thinking']={'type':'disabled'}
        if tools:body['tools']=tools
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.settings.remote_timeout,connect=10)) as client:
                async with client.stream('POST',url.rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+key},json=body) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        item=parse_stream_line(line)
                        if item is not None:yield item
        except (httpx.HTTPError,ValueError,KeyError,ImportError) as exc:
            # Never surface provider response bodies, headers or tokens.
            raise ModelServiceError(exc) from exc
