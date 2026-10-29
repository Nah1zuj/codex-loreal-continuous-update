from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')

class Settings(BaseModel):
    model_provider: Literal['mock', 'qwen','deepseek','openai_compatible'] = Field(default_factory=lambda: os.getenv('MODEL_PROVIDER', 'mock'))
    compatible_api_key:str=Field(default_factory=lambda:os.getenv('COMPATIBLE_API_KEY',''),repr=False)
    compatible_base_url:str=Field(default_factory=lambda:os.getenv('COMPATIBLE_BASE_URL',''))
    compatible_model:str=Field(default_factory=lambda:os.getenv('COMPATIBLE_MODEL',''))
    vision_provider: Literal['mock', 'qwen','deepseek'] = Field(default_factory=lambda: os.getenv('VISION_PROVIDER', 'mock'))
    reading_provider: Literal['mock','qwen','deepseek'] = Field(default_factory=lambda: os.getenv('READING_PROVIDER','mock'))
    reference_provider: Literal['mock','qwen','deepseek'] = Field(default_factory=lambda: os.getenv('REFERENCE_PROVIDER','mock'))
    allow_remote_ai: bool = Field(default_factory=lambda: os.getenv('ALLOW_REMOTE_AI','false').lower()=='true')
    research_mode: bool = Field(default_factory=lambda: os.getenv('RESEARCH_MODE','false').lower()=='true')
    admin_enabled: bool = Field(default_factory=lambda: os.getenv('ADMIN_ENABLED','true').lower()=='true')
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv('DEEPSEEK_API_KEY',''),repr=False)
    deepseek_base_url: str = Field(default_factory=lambda: os.getenv('DEEPSEEK_BASE_URL','https://api.deepseek.com'))
    deepseek_model: str = Field(default_factory=lambda: os.getenv('DEEPSEEK_MODEL','deepseek-flash'))
    deepseek_vision_model: str = Field(default_factory=lambda: os.getenv('DEEPSEEK_VISION_MODEL',''))
    media_dir: Path = ROOT / 'data/references'
    history_dir: Path = ROOT / 'data/history'
    reports_dir: Path = ROOT / 'reports'
    embedding_provider: Literal['mock', 'qwen'] = Field(default_factory=lambda: os.getenv('EMBEDDING_PROVIDER', 'mock'))
    reranker_provider: Literal['mock', 'remote'] = Field(default_factory=lambda: os.getenv('RERANKER_PROVIDER', 'mock'))
    voice_provider: str = Field(default_factory=lambda: os.getenv('VOICE_PROVIDER', 'browser'))
    developer_mode: bool = Field(default_factory=lambda: os.getenv('DEVELOPER_MODE', 'true').lower() == 'true')
    api_key: str = Field(default_factory=lambda: os.getenv('DASHSCOPE_API_KEY', ''),repr=False)
    base_url: str = Field(default_factory=lambda: os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'))
    chat_model: str = Field(default_factory=lambda: os.getenv('QWEN_CHAT_MODEL', 'qwen-plus'))
    vision_model: str = Field(default_factory=lambda: os.getenv('QWEN_VISION_MODEL', 'qwen-vl-plus'))
    embedding_model: str = Field(default_factory=lambda: os.getenv('QWEN_EMBEDDING_MODEL', 'text-embedding-v3'))
    remote_timeout: float = Field(default_factory=lambda: float(os.getenv('REMOTE_TIMEOUT', '30')), gt=0)
    confidence_high: float = Field(default_factory=lambda: float(os.getenv('CONFIDENCE_HIGH', '.8')), ge=0, le=1)
    confidence_min: float = Field(default_factory=lambda: float(os.getenv('CONFIDENCE_MIN', '.6')), ge=0, le=1)
    memory_path: Path = Field(default_factory=lambda: ROOT / os.getenv('MEMORY_PATH', 'data/users/beauty.sqlite'))
    knowledge_dir: Path = ROOT / 'data/knowledge'
    index_path: Path = ROOT / 'data/index.json'
    product_weights: dict[str, float] = Field(default_factory=lambda: {
        'scene': float(os.getenv('PRODUCT_SCENE_WEIGHT', 3)),
        'look': float(os.getenv('PRODUCT_LOOK_WEIGHT', 4)),
        'finish': float(os.getenv('PRODUCT_FINISH_WEIGHT', 2)),
        'preference': float(os.getenv('PRODUCT_PREFERENCE_WEIGHT', 2)),
        'risk': float(os.getenv('PRODUCT_RISK_PENALTY', 5)),
    })

    @model_validator(mode='after')
    def thresholds(self):
        if self.confidence_min > self.confidence_high:
            raise ValueError('CONFIDENCE_MIN must not exceed CONFIDENCE_HIGH')
        # Honor the brief: application artifacts may only be written inside the project.
        if not self.memory_path.resolve().is_relative_to(ROOT.resolve()):
            # Tests explicitly pass a path under the project work directory.
            raise ValueError('MEMORY_PATH must stay inside project directory')
        for path in (self.knowledge_dir,self.index_path,self.media_dir,self.history_dir,self.reports_dir):
            if not path.resolve().is_relative_to(ROOT.resolve()):raise ValueError('All data paths must stay inside project directory')
        return self
