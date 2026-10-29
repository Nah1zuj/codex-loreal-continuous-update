import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hardware'/'src'))
from trace_hardware.core import Gateway, Event, Simulator, UnsupportedAdapter

def paired(clock=None):
    gateway=Gateway(clock=clock or (lambda:1000))
    code=gateway.issue('owner','session')
    device,token=gateway.pair(code,'Browser mirror',['display'])
    return gateway,device,token

def test_one_time_pair_and_display_scope():
    g=Gateway(clock=lambda:1000);code=g.issue('a','s')
    d,token=g.pair(code,'mirror',['display','camera'])
    assert d.capabilities==('display',) and d.connection_state=='connected'
    assert g.authorize(token).session_id=='s'
    with pytest.raises(PermissionError):g.pair(code,'other',['display'])
    with pytest.raises(PermissionError):g.revoke('other',d.id)
    g.revoke('a',d.id)
    with pytest.raises(PermissionError):g.authorize(token)

def test_expiry_bounded_registry_and_audit():
    now=[1000];g,d,t=paired(lambda:now[0]);now[0]+=301
    with pytest.raises(PermissionError):g.authorize(t)
    code=g.issue('owner','s');now[0]+=121
    with pytest.raises(PermissionError):g.pair(code,'m',['display'])
    assert all('token' not in row and 'code' not in row for row in g.audit('owner'))

def test_event_permissions_replay_and_impersonation():
    g,d,t=paired()
    e=Event(d.id,'session',1000,'device.connected',{},'granted',1)
    assert g.accept(t,e)['accepted']
    for bad in [e,Event(d.id,'other',1000,'device.connected',{},'granted',2),
                Event(d.id,'session',1000,'camera.frame_available',{'image':'raw'},'granted',2),
                Event(d.id,'session',900,'device.connected',{},'granted',2)]:
        with pytest.raises((PermissionError,ValueError)):g.accept(t,bad)

def test_deterministic_simulator_and_unsupported_real_adapters():
    sim=Simulator();assert sim.get_status()['simulated']
    with pytest.raises(PermissionError):sim.set_lighting(50,4000,False)
    with pytest.raises(ValueError):sim.set_lighting(101,4000,True)
    sim.connect();r=sim.set_lighting(55,4200,True)
    assert r['verified'] and r['simulated'] and r['brightness']==55
    assert sim.camera_state()['capture']=='unsupported'
    assert sim.audio_event('audio.output_finished')['simulated']
    sim.display({'title':'test'});sim.disconnect()
    assert sim.get_status()['connection_state']=='disconnected'
    with pytest.raises(NotImplementedError):UnsupportedAdapter('ble').connect()

def test_http_mirror_scope_and_cross_owner(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.config import Settings
    from app.routes.hardware import build_hardware_router
    app=create_app(Settings(memory_path=tmp_path/'hardware.sqlite'))
    with TestClient(app) as owner, TestClient(app) as mirror:
        owner.get('/api/identity')
        response=owner.post('/api/chat',json={'message':'hello'})
        sid=response.json()['session']['session_id']
        code=owner.post('/api/hardware/pairing',json={'session_id':sid}).json()['code']
        assert mirror.post('/api/hardware/pairing',json={'session_id':sid}).status_code==404
        paired=mirror.post('/api/hardware/pair',json={'code':code,'name':'Test mirror','capabilities':['display','camera']}).json()
        headers={'Authorization':'Bearer '+paired['token']}
        display=mirror.get('/api/hardware/display',headers=headers)
        assert display.status_code==200
        assert set(display.json())=={'device','session_id','workflow','step','progress','illustration_only'}
        assert display.json()['session_id']==sid
        assert 'user_id' not in display.text and 'last_response' not in display.text
        assert mirror.get('/api/hardware/devices').json()['devices']==[]
        assert mirror.delete('/api/hardware/devices/'+paired['device']['id']).status_code==403
        assert owner.delete('/api/hardware/devices/'+paired['device']['id']).status_code==200
        assert mirror.get('/api/hardware/display',headers=headers).status_code==403

def test_hardware_requires_loopback_or_https(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.config import Settings
    with TestClient(create_app(Settings(memory_path=tmp_path/'https.sqlite')),base_url='http://remote.example') as client:
        assert client.get('/api/hardware/devices').status_code==403

def test_existing_app_works_without_optional_hardware_package(tmp_path,monkeypatch):
    import builtins
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.config import Settings
    original=builtins.__import__
    def without_hardware(name,*args,**kwargs):
        if name=='app.routes.hardware':raise ModuleNotFoundError('Optional package absent',name='trace_hardware')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',without_hardware)
    with TestClient(create_app(Settings(memory_path=tmp_path/'optional.sqlite'))) as client:
        assert client.get('/api/health').status_code==200
        assert client.get('/api/hardware/devices').json()['available'] is False

def test_hardware_http_rejects_ungranted_camera_and_unbounded_lighting(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.config import Settings
    import time
    with TestClient(create_app(Settings(memory_path=tmp_path/'events.sqlite'))) as client:
        s=client.post('/api/chat',json={'message':'hello'}).json()['session']
        code=client.post('/api/hardware/pairing',json={'session_id':s['session_id']}).json()['code']
        pair=client.post('/api/hardware/pair',json={'code':code,'name':'Mirror','capabilities':['display']}).json()
        event={'device_id':pair['device']['id'],'session_id':s['session_id'],'timestamp':time.time(),'event_type':'camera.frame_available','payload':{'image':'not-an-image'},'permission_status':'granted','sequence':1}
        assert client.post('/api/hardware/events',json={'event':event},headers={'Authorization':'Bearer '+pair['token']}).status_code==403
        assert client.post('/api/hardware/simulator',json={'operation':'lighting','brightness':101,'consent':True}).status_code==422
        assert client.post('/api/hardware/simulator',json={'operation':'connect'}).json()['simulated']
        assert client.post('/api/hardware/simulator',json={'operation':'lighting','consent':False}).status_code==403
        result=client.post('/api/hardware/simulator',json={'operation':'lighting','brightness':60,'consent':True}).json()
        assert result['simulated'] and result['physical_device_changed'] is False
