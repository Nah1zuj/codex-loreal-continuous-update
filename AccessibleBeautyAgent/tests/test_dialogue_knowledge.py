import json
from pathlib import Path
from shutil import copytree

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.knowledge.repository import KnowledgeRepository
from app.main import create_app


FIXTURES = Path(__file__).parent / 'fixtures'
LESSONS = ('prep', 'foundation', 'blush', 'lips', 'finish')


def frames(client, message, sid=None, locale='zh-CN'):
    result = client.post('/api/chat/stream', json={'session_id':sid,'message':message,'locale':locale})
    result.raise_for_status()
    return [json.loads(line.removeprefix('data: ')) for line in result.text.splitlines() if line.startswith('data: ')]


def say(client, message, sid=None, locale='zh-CN'):
    events = frames(client, message, sid, locale)
    assert events[-1]['type']=='final', events[-1]
    return events[-1]['reply']


def test_draft_clarifies_user_inputs_and_stays_unchanged_during_casual_chat(tmp_path):
    with TestClient(create_app(Settings(memory_path=tmp_path/'dialogue.sqlite'))) as client:
        first = say(client, '我想画自然的日常妆，大概十五分钟。')
        sid = first['session']['session_id']
        assert '熟悉的工具或产品' in first['message']
        assert first['session']['makeup_plan']['needs']['minutes']==15
        draft = say(client, '场合：晚宴；妆感：自然；时间：12 分钟；工具：熟悉的口红、手指；避讳：底妆', sid)
        needs = draft['session']['makeup_plan']['needs']
        assert needs['occasion']=='dinner' and needs['minutes']==12
        assert needs['own_products']==['熟悉的口红','手指'] and needs['avoid']==['底妆']
        assert all(step['id']!='coaching_foundation_zh' for step in draft['session']['makeup_plan']['steps'])
        start = say(client, '开始。', sid)
        plan = start['session']['makeup_plan']
        assert plan['active_index']==0
        for message in ('下一步怎么做？', '前一步怎么做的？', '如果下一步呢？', '还没完成，下一步', '讲讲今天的森林'):
            reply = say(client, message, sid)
            assert reply['session']['makeup_plan']['revision']==plan['revision']
            assert reply['session']['makeup_plan']['active_index']==0
        assert '树林' in reply['message']
        assert '保留这一步' in say(client,'可以进入下一步吗？',sid)['message']
        assert say(client,'下一步。',sid)['session']['makeup_plan']['active_index']==1


def test_only_complete_grounded_course_candidates_are_applied(tmp_path):
    agent = create_app(Settings(memory_path=tmp_path/'candidates.sqlite')).state.agent
    session = agent.sessions.create('owner')
    expected = [f'coaching_{name}_zh' for name in LESSONS]
    for ids in (expected[::4], expected[::-1], [*expected[:-1], 'imaginary'], [*expected[:-1], expected[0]]):
        plan = agent.coaching.create(session, {}, {'lesson_ids':ids})
        assert plan.generation_status=='fallback'
        assert [step.id for step in plan.steps]==expected
    plan = agent.coaching.create(session, {}, {'lesson_ids':expected})
    assert plan.generation_status=='grounded'
    assert all(step.lesson_provenance.version==1 for step in plan.steps)
    assert all(step.lesson_provenance.sources[0].source_id=='trace_original_phase4' for step in plan.steps)


def test_provider_cannot_execute_undisclosed_tools_or_invent_course_steps(tmp_path,monkeypatch):
    from app.agent import conversation

    class Transport:
        def __init__(self,*_):
            self.round = 0

        async def stream_chat(self, model, messages, tools=None):
            self.round += 1
            if self.round == 1:
                offered = {tool['function']['name'] for tool in tools}
                assert 'propose_makeup_course' in offered and 'advance_makeup_step' not in offered
                assert 'sessionId' not in messages[0]['content'] and 'userId' not in messages[0]['content']
                yield {'choices':[{'delta':{'tool_calls':[
                    {'index':0,'id':'bad-course','function':{'name':'propose_makeup_course',
                    'arguments':json.dumps({'lesson_ids':['invented_prep','invented_finish']})}},
                    {'index':1,'id':'bad-action','function':{'name':'advance_makeup_step','arguments':'{}'}},
                ]}}]}
            else:
                yield {'choices':[{'delta':{'content':'You completed two invented lessons and already started my new course.'}}]}

    monkeypatch.setattr(conversation,'RemoteModelClient',Transport)
    app = create_app(Settings(memory_path=tmp_path/'provider.sqlite'))
    app.state.agent.settings.model_provider='deepseek'
    with TestClient(app) as client:
        result = frames(client,'I want natural makeup',locale='en')
    assert [row['ok'] for row in result if row['type']=='tool']==[False,False]
    assert all('invented' not in row.get('text','') for row in result)
    assert 'occasion' in result[-1]['reply']['message']
    plan = result[-1]['reply']['session']['makeup_plan']
    assert plan['status']=='draft' and plan['active_index']==0 and plan['revision']==0
    assert [step['id'] for step in plan['steps']]==[f'coaching_{topic}_en' for topic in LESSONS]


def test_trials_require_complete_approved_course_and_translation(tmp_path):
    settings = Settings(memory_path=tmp_path/'trial.sqlite')
    kb = tmp_path/'knowledge'
    copytree(settings.knowledge_dir,kb)
    repository = KnowledgeRepository(kb)
    settings.knowledge_dir=kb
    settings.developer_mode=False
    app = create_app(settings)
    agent = app.state.agent
    with pytest.raises(ValueError,match='reviewed'):
        agent.coaching.create(agent.sessions.create('owner'),{})
    for topic in LESSONS:
        row=repository.get('ACCESSIBILITY_GUIDANCE',f'coaching_{topic}_zh')
        if topic=='prep':
            with pytest.raises(ValueError,match='来源'):
                repository.save('ACCESSIBILITY_GUIDANCE',{**row,'source_ids':[]},row['version'],reviewed=True,reviewer='TEST REVIEWER')
        repository.save('ACCESSIBILITY_GUIDANCE',row,row['version'],reviewed=True,reviewer='TEST REVIEWER')
    agent=create_app(settings).state.agent
    session=agent.sessions.create('owner')
    plan=agent.coaching.create(session,{})
    assert plan.knowledge_status=='reviewed'
    assert plan.steps[0].lesson_provenance.reviewed_by=='TEST REVIEWER'
    agent.coaching.act(session,'start','start')
    session.locale='en'
    # A translated but unreviewed lesson cannot replace the reviewed lesson.
    assert agent.coaching.current(session)['source_id']=='coaching_prep_zh'
    row=repository.get('ACCESSIBILITY_GUIDANCE','coaching_foundation_zh')
    repository.deprecate('ACCESSIBILITY_GUIDANCE',row['guidance_id'],row['version'])
    restarted=create_app(settings).state.agent
    saved=restarted.sessions.get(session.session_id)
    assert restarted.coaching.current(saved) is None
    with pytest.raises(ValueError,match='版本已变更'):
        restarted.coaching.act(saved,'advance','unsafe')
    assert saved.makeup_plan.active_index==0


def test_retrieval_examples_check_source_applicability_and_admission(tmp_path):
    app=create_app(Settings(memory_path=tmp_path/'retrieval.sqlite'))
    agent=app.state.agent
    for case in json.loads((FIXTURES/'lesson_retrieval.json').read_text()):
        filters={'subtype':'makeup_lesson','language':case['language'],'makeup_area':case['area']}
        hits=agent.retriever.search(case['query'],filters,limit=3)['results']
        assert hits and hits[0]['document_id']==case['expected']
        assert case['task_evidence'] in hits[0]['content'].casefold()
        metadata=hits[0]['metadata']
        assert metadata['source_ids']==['trace_original_phase4']
        assert metadata['sources'][0]['use_permission']=='original'
        assert metadata['status']=='DRAFT' and metadata['version']==1
        agent.settings.developer_mode=False
        assert agent.retriever.search(case['query'],filters,limit=3)['results']==[]
        agent.settings.developer_mode=True


def test_provider_can_select_an_available_same_topic_alternative(tmp_path,monkeypatch):
    from app.agent import conversation

    class Transport:
        def __init__(self,*_):
            self.round=0

        async def stream_chat(self, model, messages, tools=None):
            self.round+=1
            if self.round==1:
                ids=[f'coaching_{topic}_en' for topic in LESSONS]
                ids[1]='coaching_foundation_alt_en'
                yield {'choices':[{'delta':{'tool_calls':[{
                    'index':0,'id':'grounded','function':{'name':'propose_makeup_course',
                    'arguments':json.dumps({'lesson_ids':ids})},
                }]}}]}
            else:
                yield {'choices':[{'delta':{'content':'The candidate is ready.'}}]}

    monkeypatch.setattr(conversation,'RemoteModelClient',Transport)
    app=create_app(Settings(memory_path=tmp_path/'proposal.sqlite'))
    agent=app.state.agent
    agent.settings.model_provider='deepseek'
    base=next(row for row in agent.store.guidance if row['guidance_id']=='coaching_foundation_en')
    agent.store.guidance.append({**base,'guidance_id':'coaching_foundation_alt_en'})
    with TestClient(app) as client:
        result=frames(client,'I want natural makeup',locale='en')
    assert [row['ok'] for row in result if row['type']=='tool']==[True]
    plan=result[-1]['reply']['session']['makeup_plan']
    assert plan['status']=='draft' and plan['steps'][1]['id']=='coaching_foundation_alt_en'
