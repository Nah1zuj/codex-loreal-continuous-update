import pytest
from app.main import create_app
from app.config import Settings

def test_plan_is_durable_and_events_are_idempotent(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'coaching.sqlite'))
    agent=app.state.agent;s=agent.sessions.create('test-owner')
    plan=agent.coaching.create(s,{'style':'natural','minutes':15})
    assert len(plan.steps)>=4
    agent.coaching.act(s,'start','start-id')
    agent.coaching.act(s,'advance','one-id')
    agent.coaching.act(s,'advance','one-id')
    assert s.makeup_plan.active_index==1
    agent.coaching.act(s,'pause','pause-id')
    with pytest.raises(ValueError):agent.coaching.act(s,'advance','blocked-id')
    agent.coaching.act(s,'resume','resume-id')
    recovered=create_app(Settings(memory_path=tmp_path/'coaching.sqlite')).state.agent.sessions.get(s.session_id)
    assert recovered.makeup_plan.active_index==1
    assert recovered.camera_consent is False

def test_previous_keeps_completion_and_invalid_output_falls_back(tmp_path):
    agent=create_app(Settings(memory_path=tmp_path/'coaching.sqlite')).state.agent
    s=agent.sessions.create('owner')
    plan=agent.coaching.create(s,{'style':'natural'},candidate={'steps':'bad'})
    assert plan.generation_status=='fallback'
    agent.coaching.act(s,'start','a');agent.coaching.act(s,'advance','b')
    agent.coaching.act(s,'previous','c')
    assert s.makeup_plan.steps[0].status=='completed'
    assert s.makeup_plan.active_index==0
    assert agent.coaching.current(s)['instruction']

def test_skip_and_sync_chat_use_the_same_persistent_controller(tmp_path):
    from app.schemas.models import ChatRequest
    agent=create_app(Settings(memory_path=tmp_path/'coaching.sqlite')).state.agent
    s=agent.sessions.create('owner');agent.coaching.create(s,{})
    agent.chat(ChatRequest(session_id=s.session_id,message='好的，开始。'))
    agent.chat(ChatRequest(session_id=s.session_id,message='跳过这一步。'))
    assert s.makeup_plan.active_index==1 and s.makeup_plan.steps[0].status=='skipped'

def test_locale_switch_and_fresh_check_do_not_reuse_old_guidance_or_vision(tmp_path):
    agent=create_app(Settings(memory_path=tmp_path/'coaching.sqlite')).state.agent
    s=agent.sessions.create('owner');agent.coaching.create(s,{});agent.coaching.act(s,'start','a')
    original=agent.coaching.current(s)['step_id'];s.locale='en'
    assert agent.coaching.current(s)['step_id']==original
    assert not any('\u4e00'<=ch<='\u9fff' for ch in agent.coaching.current(s)['instruction'])
    s.visual_state={'frame_id':'older'};agent.coaching.act(s,'visual','b')
    assert s.visual_state is None
