"""Start local DeepSeek text coaching; all image services stay mock.

Pass an existing configuration only after the owner authorizes its use.
Credentials are loaded normally, never printed or written by this launcher.
"""
import argparse
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--config-path', type=Path)
parser.add_argument('--port', type=int, default=8002)
args = parser.parse_args()
for name in ('VISION_PROVIDER', 'READING_PROVIDER', 'REFERENCE_PROVIDER', 'EMBEDDING_PROVIDER', 'RERANKER_PROVIDER'):
    os.environ[name] = 'mock'
if args.config_path:
    from dotenv import load_dotenv
    load_dotenv(args.config_path, override=False)
from app.config import Settings
from app.main import create_app
import uvicorn

settings = Settings(model_provider='deepseek', allow_remote_ai=True,
                    vision_provider='mock', reading_provider='mock', reference_provider='mock',
                    embedding_provider='mock', reranker_provider='mock',
                    memory_path=root / 'work' / 'deepseek-voice-first.sqlite')
if not settings.deepseek_api_key:
    raise SystemExit('Configured text service unavailable. No credentials displayed.')
uvicorn.run(create_app(settings), host='127.0.0.1', port=args.port)
