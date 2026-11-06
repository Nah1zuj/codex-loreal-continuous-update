"""Compatibility wrapper. No Qwen call is made while remote AI is disabled."""
from app.services.model_client import RemoteModelClient
class QwenClient(RemoteModelClient):
    def __init__(self,settings):super().__init__(settings,'qwen')
