"""Replay disposable synthesized fixtures through the actual loopback websocket.
Run with: .venv-voice/bin/python voice/verify_stream.py work/voice-checks
This tests models and transport, not a human microphone or OS accessibility.
"""
import asyncio,json,sys,wave
from pathlib import Path
import websockets
async def check(root):
    results=[]
    for name,mode,expected in [('chat','quiet',0),('wake','quiet',1),('pause','speaking',1),('chat','active',1),('wake2','quiet',1),('negative','quiet',0),('english','quiet',1)]:
        file=root/(name+'.wav')
        if not file.exists():continue
        with wave.open(str(file)) as audio:
            assert (audio.getnchannels(),audio.getsampwidth(),audio.getframerate())==(1,2,16000)
            data=audio.readframes(audio.getnframes())
        assert len(data)>3200,'Empty fixture'
        async with websockets.connect('ws://127.0.0.1:5174/local-voice/stream',origin='http://127.0.0.1:5174',proxy=None,max_size=1000000) as ws:
            assert json.loads(await ws.recv())['type']=='ready'
            await ws.send(json.dumps({'type':'mode','mode':mode,'epoch':1}));ack=json.loads(await ws.recv());assert ack['type']=='mode' and ack['epoch']==1
            for offset in range(0,len(data),1280):await ws.send(data[offset:offset+1280])
            for _ in range(25):await ws.send(bytes(1280))
            await ws.send(json.dumps({'type':'metrics'}))
            events=[]
            while True:
                event=json.loads(await asyncio.wait_for(ws.recv(),timeout=60))
                if event['type']=='metrics':metrics=event;break
                if event['type']=='transcript':events.append(event)
            assert len(events)==expected,(name,events,metrics)
            assert metrics['remote_asr_requests']==0 and not metrics['audio_saved']
            if name=='chat' and mode=='quiet':assert metrics['asr_utterances']==0
            if expected and mode=='quiet':assert events[0]['kind']=='wake'
            results.append({'input':name,'mode':mode,'events':events,'metrics':metrics})
            print(name,mode,'PASS',flush=True)
    (root/'websocket-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':asyncio.run(check(Path(sys.argv[1])))
