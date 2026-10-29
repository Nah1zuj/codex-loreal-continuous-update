"""Local text journal. Generated drafts are ephemeral; storage needs explicit consent."""
from datetime import date,datetime,timezone
import uuid,json,time
from fastapi import APIRouter,Query,Request
from pydantic import BaseModel,Field,StrictBool,ConfigDict,model_validator
from typing import Literal

class DraftMessage(BaseModel):
    model_config=ConfigDict(extra='forbid')
    role:Literal['user','agent']
    text:str=Field(min_length=1,max_length=2000)

class JournalDraftRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    messages:list[DraftMessage]=Field(min_length=1,max_length=30)
    locale:Literal['zh-CN','en']='zh-CN'
    @model_validator(mode='after')
    def bounded(self):
        if sum(len(m.text) for m in self.messages)>12000:raise ValueError('Draft transcript is too long')
        return self

class JournalDraft(BaseModel):
    model_config=ConfigDict(extra='forbid')
    look:str=Field(max_length=80)
    feeling:str=Field(max_length=200)
    reflection:str=Field(max_length=2000)
    traits:str=Field(max_length=400)

class JournalOwner(BaseModel):
    model_config=ConfigDict(extra='forbid')
    user_id:str=Field(default='demo',min_length=1,max_length=80)
    explicit_consent:StrictBool

class JournalEntry(JournalOwner):
    date:date
    look:str=Field(min_length=1,max_length=80)
    feeling:str=Field(default='',max_length=200)
    reflection:str=Field(default='',max_length=2000)
    traits:str=Field(default='',max_length=400)
    session_id:str|None=None
    save_transcript:StrictBool=False
    occasion:str=Field(default='',max_length=100)

def build_journal_router(memory,agent,conversation=None):
    with memory.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS journal (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, payload TEXT NOT NULL, timestamp TEXT NOT NULL)')
    router=APIRouter(prefix='/api/journal')
    @router.post('/draft')
    def draft(body:JournalDraftRequest):
        # Ephemeral output only. No journal write and no preference consent inference.
        return JournalDraft.model_validate(agent.language.journal_draft([m.model_dump() for m in body.messages],body.locale))
    @router.get('')
    def entries(user_id:str=Query(default='demo',min_length=1,max_length=80)):
        with memory.connect() as db:rows=db.execute('SELECT id,payload,timestamp FROM journal WHERE user_id=? ORDER BY timestamp DESC,id',(user_id,)).fetchall()
        return {'entries':[{'id':mid,**json.loads(raw),'timestamp':stamp} for mid,raw,stamp in rows]}
    @router.post('')
    def save(body:JournalEntry):
        if body.explicit_consent is not True:raise PermissionError('请确认保存这份私人文字记录。')
        payload=body.model_dump(mode='json',exclude={'user_id','explicit_consent','save_transcript'})
        transcript=None
        if body.session_id:
            s=agent.sessions.get(body.session_id)
            if s.user_id!=body.user_id:raise PermissionError('Session owner mismatch')
            payload['completed_step_count']=s.routine_step if s.routine_started else 0
        if body.save_transcript:
            if not body.session_id or not conversation:raise ValueError('Transcript requires a conversation')
            transcript=conversation.history(body.session_id)
            if not transcript:raise ValueError('No transcript available')
            payload['transcript_id']=str(uuid.uuid4())
        mid=str(uuid.uuid4());stamp=datetime.now(timezone.utc).isoformat()
        with memory.connect() as db:
            db.execute('DELETE FROM transcript_records WHERE expires_at<?',(time.time(),))
            if transcript:db.execute('INSERT INTO transcript_records VALUES (?,?,?,?,?)',(payload['transcript_id'],body.user_id,json.dumps(transcript,ensure_ascii=False),time.time(),time.time()+30*86400))
            db.execute('INSERT INTO journal VALUES (?,?,?,?)',(mid,body.user_id,json.dumps(payload,ensure_ascii=False),stamp))
        return {'id':mid,**payload,'timestamp':stamp}
    @router.delete('/{entry_id}')
    def remove(entry_id:str,body:JournalOwner):
        if body.explicit_consent is not True:raise PermissionError('请明确确认删除这份记录。')
        with memory.connect() as db:
            row=db.execute('SELECT payload FROM journal WHERE id=? AND user_id=?',(entry_id,body.user_id)).fetchone()
            if row:
                tid=json.loads(row[0]).get('transcript_id')
                if tid:db.execute('DELETE FROM transcript_records WHERE id=? AND user_id=?',(tid,body.user_id))
            result=db.execute('DELETE FROM journal WHERE id=? AND user_id=?',(entry_id,body.user_id))
            if result.rowcount!=1:raise KeyError('Journal entry not found')
        return {'deleted':True}
    return router

def build_transcript_records_router(memory):
    router=APIRouter(prefix='/api/transcript-records')
    @router.get('/{record_id}')
    def get(record_id:str,request:Request):
        with memory.connect() as db:
            db.execute('DELETE FROM transcript_records WHERE expires_at<?',(time.time(),))
            row=db.execute('SELECT user_id,payload,expires_at FROM transcript_records WHERE id=?',(record_id,)).fetchone()
        if not row or not row[0].startswith(request.state.principal_prefix):raise KeyError('Transcript not found')
        return {'messages':json.loads(row[1]),'expires_at':row[2]}
    return router
