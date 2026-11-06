"""Replay disposable synthesized fixtures through the actual loopback websocket.
Run with: .venv-portable/bin/python voice/verify_stream.py voice/fixtures
This tests models and transport, not a human microphone or OS accessibility.
"""
import argparse,asyncio,json,wave
from pathlib import Path
import websockets
async def check(root, port, output):
    results=[]
    for name,mode,expected in [('chat','quiet',0),('wake','quiet',1),('pause','speaking',1),('chat','active',1),('wake2','quiet',1),('negative','quiet',0),('english','quiet',1)]:
        file=root/(name+'.wav')
        if not file.is_file():raise FileNotFoundError(file)
        with wave.open(str(file)) as audio:
            assert (audio.getnchannels(),audio.getsampwidth(),audio.getframerate())==(1,2,16000)
            data=audio.readframes(audio.getnframes())
        assert len(data)>3200,'Empty fixture'
        async with websockets.connect(f'ws://127.0.0.1:{port}/local-voice/stream',origin=f'http://127.0.0.1:{port}',proxy=None,max_size=1000000) as ws:
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
    if output:
        output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    runtime=json.loads((Path(__file__).resolve().parents[1]/'runtime.json').read_text(encoding='utf-8'))
    parser=argparse.ArgumentParser()
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('--port', type=int, default=runtime['frontend'])
    parser.add_argument('--output', type=Path)
    args=parser.parse_args()
    asyncio.run(check(args.fixtures,args.port,args.output))
