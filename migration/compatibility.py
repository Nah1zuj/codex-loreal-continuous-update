"""Run identical scenarios in separate old/new processes and compare full evidence.

Synthetic identities, fixed clock/randomness and temporary databases are test-only.
No private dotenv, existing database, downloaded model or remote AI is used.
"""
import argparse
import base64
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import random
import secrets
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'migration/evidence'


def worker(application, destination):
    application = application.resolve()
    sys.path[:0] = [str(application), str(application/'backend'), str(application/'hardware/src')]
    os.chdir(application)
    from runtime import isolated_environment
    work = application/'work'
    work.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='compatibility-', dir=work) as temporary:
        directory = Path(temporary)
        os.environ.update(isolated_environment(directory))
        from app.main import create_app
        from app.config import Settings
        from fastapi.testclient import TestClient

        rng = random.Random(20261108)
        def token_bytes(n=32):
            return rng.randbytes(n)
        secrets.token_bytes = token_bytes
        secrets.token_hex = lambda n=32: token_bytes(n).hex()
        secrets.token_urlsafe = lambda n=32: base64.urlsafe_b64encode(token_bytes(n)).rstrip(b'=').decode()
        uuid.uuid4 = lambda: uuid.UUID(bytes=token_bytes(16), version=4)
        time.time = lambda: 1794096000.0

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls.fromtimestamp(1794096000, tz=tz)
        for name, module in list(sys.modules.items()):
            if name.startswith('app.') and getattr(module, 'datetime', None) is datetime:
                module.datetime = FixedDateTime

        result = {'scenarios': {}}
        current = []
        def request(client, label, method, path, expected=200, **kwargs):
            response = client.request(method, path, **kwargs)
            if response.headers.get('content-type', '').startswith('text/event-stream'):
                value = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
            else:
                value = response.json()
            current.append({'label':label, 'request':{'method':method, 'path':path, **kwargs},
                            'status':response.status_code, 'response':value})
            assert response.status_code == expected, (label, response.status_code, value)
            return value

        def start(name):
            nonlocal current
            current = []
            result['scenarios'][name] = {'requests':current}
            return Settings(memory_path=directory/(name+'.sqlite'))

        def state(client, sid):
            return request(client, 'state', 'GET', '/api/session/'+sid)

        def command(session, event, action='advance'):
            plan = session['makeup_plan']
            return {'session_id':session['session_id'], 'event_id':event, 'action':action,
                    'expected_plan_id':plan['id'], 'expected_revision':plan['revision'],
                    'expected_step_id':plan['steps'][plan['active_index']]['id']}

        def database(settings, name):
            with sqlite3.connect(settings.memory_path) as db:
                tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                data = {}
                for table in tables:
                    columns = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
                    rows = []
                    for row in db.execute(f'SELECT * FROM "{table}"'):
                        item = dict(zip(columns, row))
                        # This is SQLite's own wall-clock bookkeeping, not business data.
                        if table == 'schema_migrations':
                            item['applied_at'] = '<sqlite-migration-application-time>'
                        for key, value in item.items():
                            if isinstance(value, str) and value.startswith(('{','[')):
                                try: item[key] = json.loads(value)
                                except ValueError: pass
                        rows.append(item)
                    data[table] = sorted(rows, key=lambda v:json.dumps(v, sort_keys=True))
                result['scenarios'][name]['database'] = data

        settings = start('health_and_catalogue')
        app = create_app(settings)
        with TestClient(app) as c:
            result['openapi'] = app.openapi()
            request(c,'health','GET','/api/health')
            request(c,'unknown','GET','/api/session/missing',404)
            selected = request(c,'dinner','POST','/api/chat',json={'message':'今晚有一个正式 dinner，我想精致一点但别太成熟'})
            session = selected['session']; sid=session['session_id']
            assert session['selected_look']=='soft_formal' and session['scene']=='dinner'
            session = request(c,'catalogue_start','POST','/api/chat',json={'session_id':sid,'message':'开始步骤','event_id':'start-catalogue'})['session']
            request(c,'advance','POST','/api/makeup/command',json=command(session,'advance-catalogue'))
            request(c,'camera_denied','POST','/api/vision/check',403,json={'session_id':sid,'demo':True,'images':[]})
            request(c,'request_check','POST','/api/chat',json={'session_id':sid,'message':'check this'})
            request(c,'camera_grant','POST','/api/chat',json={'session_id':sid,'action':'camera_consent','consent':True})
            request(c,'demo_check','POST','/api/vision/check',json={'session_id':sid,'demo':True,'images':[]})
            request(c,'full_look_not_created','GET','/api/full-look/'+sid,404)
            state(c,sid)
        database(settings,'health_and_catalogue')

        settings=start('commands_restart_and_ownership');app=create_app(settings)
        with TestClient(app) as owner, TestClient(app) as other:
            session=request(owner,'reflect','POST','/api/experience/reflect',json={})['session'];sid=session['session_id']
            data=command(session,'once')
            moved=request(owner,'advance','POST','/api/makeup/command',json=data)
            assert moved['session']['makeup_plan']['active_index']==1
            replay=request(owner,'replay','POST','/api/makeup/command',json=data)
            assert replay['duplicate'] and replay['event']==moved['event']
            request(owner,'mismatched_event','POST','/api/makeup/command',409,json={**data,'action':'skip'})
            request(owner,'stale_version','POST','/api/makeup/command',409,json={**data,'event_id':'stale'})
            request(other,'foreign_get','GET','/api/session/'+sid,404)
            for content_type in ('application/json','Application/JSON','application/json; charset=utf-8','application/vnd.trace+json',''):
                request(other,'foreign_write_'+content_type,'POST','/api/makeup/command',404,
                        content=json.dumps(command(moved['session'],'foreign')),
                        headers={'Content-Type':content_type})
            session=request(owner,'pause','POST','/api/makeup/command',json=command(moved['session'],'pause','pause'))['session']
            request(owner,'advance_paused','POST','/api/makeup/command',409,json=command(session,'while-paused'))
            session=request(owner,'resume','POST','/api/makeup/command',json=command(session,'resume','resume'))['session']
            session=request(owner,'skip','POST','/api/makeup/command',json=command(session,'skip','skip'))['session']
            request(owner,'restore_clears_media','POST','/api/session/'+sid+'/restore')
            request(owner,'finish','POST','/api/makeup/command',json=command(session,'finish','finish'))
            cookies=dict(owner.cookies)
        with TestClient(create_app(settings)) as restarted:
            restarted.cookies.update(cookies)
            restored=request(restarted,'after_restart','POST','/api/session/'+sid+'/restore')
            assert not restored['camera_consent'] and restored['makeup_plan']['status']=='completed'
            request(restarted,'committed_receipt','GET',f'/api/makeup/events/{sid}/once')
        database(settings,'commands_restart_and_ownership')

        settings=start('memory');app=create_app(settings)
        with TestClient(app) as c, TestClient(app) as stranger:
            candidate={'feedback':'唇色稍强','preferred_saturation':'low'}
            request(c,'no_consent','POST','/api/memory',403,json={'user_id':'demo','candidate':candidate,'explicit_consent':False})
            request(c,'string_consent','POST','/api/memory',422,json={'user_id':'demo','candidate':candidate,'explicit_consent':'true'})
            draft=request(c,'preview','POST','/api/memory/preview',json={'user_id':'demo','candidate':candidate})
            save={'user_id':'demo',**draft,'explicit_consent':True}
            saved=request(c,'save','POST','/api/memory',json=save);mid=saved['memory_id']
            request(c,'replay','POST','/api/memory',json=save)
            request(c,'tamper','POST','/api/memory',409,json={**save,'candidate':{'feedback':'被改过'}})
            request(c,'profile','GET','/api/profile/demo')
            request(stranger,'private','DELETE',f'/api/memory/{mid}?user_id=demo&explicit_consent=true',404)
            request(c,'delete','DELETE',f'/api/memory/{mid}?user_id=demo&explicit_consent=true')
            request(c,'deleted_replay','POST','/api/memory',409,json=save)
            assert request(c,'empty_profile','GET','/api/profile/demo')['episodes']==[]
        database(settings,'memory')

        settings=start('styling_reading_stream');app=create_app(settings)
        with TestClient(app) as c:
            session=request(c,'select','POST','/api/chat',json={'message':'cafe meeting formal and natural'})['session'];sid=session['session_id']
            request(c,'create_plan','POST','/api/full-look/plan',json={'session_id':sid})
            plan=request(c,'plan','GET','/api/full-look/'+sid)['plan']
            body={'session_id':sid,'target_sections':['makeup'],'user_request':'妆容我想淡一点','expected_version':plan['version']}
            request(c,'revise','POST','/api/full-look/revise',json=body)
            request(c,'conflict','POST','/api/full-look/revise',409,json=body)
            request(c,'reading_availability','GET','/api/reading/availability')
            request(c,'reading_no_consent','POST','/api/reading/read',403,json={'demo':True})
            request(c,'reading_demo','POST','/api/reading/read',json={'demo':True,'explicit_consent':True})
            request(c,'stream','POST','/api/chat/stream',json={'session_id':sid,'message':'开始步骤','event_id':'stream-start'})
            request(c,'stream_end','POST','/api/chat/stream',json={'session_id':sid,'message':'stop session','event_id':'stream-end'})
            assert state(c,sid)['stage']=='COMPLETE'
        database(settings,'styling_reading_stream')

        with sqlite3.connect(settings.memory_path) as db:
            result['sqlite_schema'] = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name").fetchall()
        # Replace only filesystem roots, preserving all business values and references.
        encoded=json.dumps(result,ensure_ascii=False,sort_keys=True)
        encoded=encoded.replace(str(application),'<application-root>')
        destination.write_text(encoded+'\n')


def compare(python, baseline):
    EVIDENCE.mkdir(exist_ok=True)
    for name, application in (('old',baseline),('new',ROOT/'AccessibleBeautyAgent')):
        subprocess.run([str(python),str(Path(__file__).resolve()),'--worker',str(application),
                        '--output',str(EVIDENCE/(name+'-compatibility.json'))],check=True,timeout=90)
    old=json.loads((EVIDENCE/'old-compatibility.json').read_text())
    new=json.loads((EVIDENCE/'new-compatibility.json').read_text())
    differences=[]
    def walk(a,b,path='$'):
        if type(a) is not type(b):differences.append(path+': type');return
        if isinstance(a,dict):
            if a.keys()!=b.keys():differences.append(path+': keys')
            for key in a.keys() & b.keys():walk(a[key],b[key],path+'.'+key)
        elif isinstance(a,list):
            if len(a)!=len(b):differences.append(path+': length')
            for i,(x,y) in enumerate(zip(a,b)):walk(x,y,f'{path}[{i}]')
        elif a!=b:differences.append(path+': value')
    walk(old,new)
    count=sum(len(s['requests']) for s in new['scenarios'].values())
    report={'passed':not differences,'request_pairs':count,'scenario_groups':len(new['scenarios']),
            'openapi_equal':old['openapi']==new['openapi'],
            'sqlite_schema_equal':old['sqlite_schema']==new['sqlite_schema'],
            'differences':differences,
            'controls':'synthetic identities, fixed UUID/random/time, isolated SQLite, mock; only SQLite applied_at and filesystem roots normalized'}
    (EVIDENCE/'compatibility-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (EVIDENCE/'compatibility-samples.json').write_text(json.dumps(new['scenarios'],ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    if differences:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--python',type=Path,default=Path(sys.executable))
    parser.add_argument('--baseline',type=Path,default=ROOT.parent/'.baseline/fd6154a/AccessibleBeautyAgent')
    args=parser.parse_args()
    if args.worker:worker(args.worker,args.output)
    else:compare(args.python,args.baseline)
