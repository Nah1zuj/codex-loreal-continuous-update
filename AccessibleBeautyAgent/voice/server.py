"""Loopback-only speech worker; no persistence, provider keys or network inference."""
import asyncio,json,logging,os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from setup_local_voice_models import check

models=None
connections=0
model_status='not_loaded'
frontend_port=os.getenv('TRACE_FRONTEND_PORT')
default_frontend=json.loads((Path(__file__).resolve().parents[1]/'runtime.json').read_text(encoding='utf-8'))['frontend']
frontend_ports=[frontend_port] if frontend_port else [default_frontend,5174,5173]
allowed_origins={f'http://{host}:{port}' for host in ('localhost','127.0.0.1') for port in frontend_ports}
@asynccontextmanager
async def lifespan(app):
    global models,model_status
    try:
        if await asyncio.to_thread(check):
            model_status='assets_missing_or_invalid'
        else:
            from engine import Models
            models=await asyncio.to_thread(Models)
            model_status='loaded'
    except (ImportError,OSError,RuntimeError,ValueError):
        logging.getLogger(__name__).exception('Local speech model loading failed')
        model_status='load_failed'
    try:
        yield
    finally:
        models=None
        model_status='not_loaded'
app=FastAPI(title='TRACE local voice',lifespan=lifespan)
@app.get('/voice/health')
def health():return {'ready':models is not None,'model_status':model_status,'device_verified':False,'processing':'on_this_computer','engine':'sherpa-onnx','microphone_required':True,'audio_saved':False,'quiet_mode':'keyword_only','supported_languages':['zh-CN','en'],'connections':connections}
@app.websocket('/voice/stream')
async def stream(ws:WebSocket):
    global connections
    if ws.headers.get('origin') not in allowed_origins or connections>=4 or models is None:
        await ws.close(code=1008);return
    await ws.accept();connections+=1
    from engine import AudioSession
    session=AudioSession(models,defer_transcription=True)

    async def transcribe_capture(explicit=False):
        if not session.capturing:return
        await ws.send_json({'type':'transcribing','epoch':session.epoch})
        event=await asyncio.to_thread(session.finish_capture,explicit)
        if event:await ws.send_json(event)

    try:
        await ws.send_json({'type':'ready','processing':'on_this_computer'})
        while True:
            message=await ws.receive()
            if message['type']=='websocket.disconnect':break
            if message.get('text') is not None:
                if len(message['text'])>1024:raise ValueError('Oversized control message')
                command=json.loads(message['text'])
                if command.get('type')=='mode':
                    session.configure(command['mode'],command['epoch'])
                    await ws.send_json({'type':'mode','mode':session.mode,'epoch':session.epoch})
                elif command.get('type')=='capture':
                    if command.get('epoch')!=session.epoch or command.get('action') not in {'start','end'}:continue
                    if command['action']=='end':
                        await transcribe_capture(explicit=True)
                    elif event:=session.begin_capture():
                        await ws.send_json(event)
                elif command.get('type')=='metrics':await ws.send_json({'type':'metrics',**session.metrics})
                else:raise ValueError('Unknown control message')
            elif message.get('bytes') is not None:
                event=await asyncio.to_thread(session.feed,message['bytes'])
                if event and event['type']=='transcribing':
                    await transcribe_capture()
                elif event:
                    await ws.send_json(event)
    except WebSocketDisconnect:pass
    except (ValueError,KeyError,TypeError):
        await ws.close(code=1008)
    finally:session.dispose();connections-=1
