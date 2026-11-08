"""Protect the isolation boundaries introduced by the migration."""
import os
from pathlib import Path
import subprocess
import sys
from fastapi import APIRouter
from fastapi.testclient import TestClient
import pytest
from app.config import Settings
from app.factory import create_app
from app.extensions import ExtensionSpec


def test_import_factory_creates_no_default_database(tmp_path):
    target = tmp_path/'never-created.sqlite'
    subprocess.run([sys.executable, '-c', 'from app.factory import create_app'],
                   cwd=Path(__file__).resolve().parents[1],
                   env={**os.environ, 'MEMORY_PATH':str(target), 'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'backend')}, check=True)
    assert not target.exists()


def test_extensions_keep_core_identity_and_origin_checks(tmp_path):
    received=[]
    def build(services):
        received.append(services)
        router=APIRouter()
        @router.get('/health')
        def health():return {'mode':'extension-test'}
        return router
    app=create_app(Settings(memory_path=tmp_path/'extension.sqlite'),
                   extensions=(ExtensionSpec('probe',build),))
    with TestClient(app) as client:
        assert received==[app.state.services]
        assert client.get('/api/health').json()['provider_mode']=='mock'
        response=client.get('/api/extensions/probe/health')
        assert response.json()=={'mode':'extension-test'}
        assert 'trace_identity' in response.cookies
        assert response.headers['cache-control']=='no-store'
        assert client.get('/api/extensions/probe/health',headers={'Origin':'https://foreign.invalid'}).status_code==403


@pytest.mark.parametrize('name',['../chat','/api/chat','UPPER','','x'*41])
def test_namespace_cannot_escape_or_shadow_core(name,tmp_path):
    target=tmp_path/'invalid.sqlite'
    with pytest.raises(ValueError):
        create_app(Settings(memory_path=target),extensions=(ExtensionSpec(name,lambda _:APIRouter()),))
    assert not target.exists()


def test_duplicate_namespace_rejected_before_database_creation(tmp_path):
    extension=ExtensionSpec('same',lambda _:APIRouter());target=tmp_path/'duplicate.sqlite'
    with pytest.raises(ValueError,match='Duplicate'):
        create_app(Settings(memory_path=target),extensions=(extension,extension))
    assert not target.exists()


def test_factories_do_not_share_services_or_sessions(tmp_path):
    left=create_app(Settings(memory_path=tmp_path/'left.sqlite'))
    right=create_app(Settings(memory_path=tmp_path/'right.sqlite'))
    with TestClient(left) as a,TestClient(right) as b:
        sid=a.post('/api/session',json={}).json()['session_id']
        assert b.get('/api/session/'+sid).status_code==404
        assert left.state.services.agent is not right.state.services.agent
