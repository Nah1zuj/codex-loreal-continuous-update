"""Loopback-only speech worker; no persistence, provider keys or network inference."""
import asyncio,json
from contextlib import asynccontextmanager
from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from engine import Models,AudioSession

models=None
connections=0
@asynccontextmanager
async def lifespan(app):
    global models
    models=await asyncio.to_thread(Models)
    yield
    models=None
app=FastAPI(title='TRACE local voice',lifespan=lifespan)
@app.get('/voice/health')
def health():return {'ready':models is not None,'processing':'on_this_computer','engine':'sherpa-onnx','microphone_required':True,'audio_saved':False,'quiet_mode':'keyword_only','supported_languages':['zh-CN','en'],'connections':connections}
@app.websocket('/voice/stream')
async def stream(ws:WebSocket):
    global connections
    if ws.headers.get('origin') not in {'http://127.0.0.1:5180','http://localhost:5180','http://127.0.0.1:5174','http://localhost:5174','http://127.0.0.1:5173','http://localhost:5173'} or connections>=4 or models is None:
        await ws.close(code=1008);return
    await ws.accept();connections+=1
    session=AudioSession(models)
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
                    event=await asyncio.to_thread(session.begin_capture if command['action']=='start' else lambda:session.finish_capture(explicit=True))
                    if event:await ws.send_json(event)
                elif command.get('type')=='metrics':await ws.send_json({'type':'metrics',**session.metrics})
                else:raise ValueError('Unknown control message')
            elif message.get('bytes') is not None:
                event=await asyncio.to_thread(session.feed,message['bytes'])
                if event:await ws.send_json(event)
    except WebSocketDisconnect:pass
    except (ValueError,KeyError,TypeError):
        await ws.close(code=1008)
    finally:session.dispose();connections-=1
