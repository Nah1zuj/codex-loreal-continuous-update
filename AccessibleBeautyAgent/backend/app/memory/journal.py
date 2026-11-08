"""Confirmed journal writes and linked transcript lifecycle."""
from datetime import datetime, timezone
import hashlib
import json
import time
import uuid

from app.memory.migrations import RETENTION_SECONDS


class JournalStore:
    def __init__(self,memory):
        self.memory=memory
        with memory.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS journal (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,payload TEXT NOT NULL,timestamp TEXT NOT NULL)')

    @staticmethod
    def record(record_id,payload,stamp):
        return {'id':record_id,'version':1,**json.loads(payload),'timestamp':stamp}

    def view(self,user_id):
        with self.memory.connect() as db:
            rows=db.execute('SELECT id,payload,timestamp FROM journal WHERE user_id=? ORDER BY timestamp DESC,id',
                            (user_id,)).fetchall()
        return [self.record(*row) for row in rows]

    def save(self,user_id,payload,transcript=None,confirmation_id=None,*,include_transcript=False):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            return self.insert(db,user_id,payload,transcript,confirmation_id,include_transcript=include_transcript,dedupe_legacy=True)

    def insert(self,db,user_id,payload,transcript=None,confirmation_id=None,*,include_transcript=False,dedupe_legacy=False):
        payload={**payload,'version':1}
        reviewed={key:value for key,value in payload.items() if key!='completed_step_count'}
        digest=hashlib.sha256(json.dumps([reviewed,include_transcript],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if confirmation_id is None and dedupe_legacy:
            confirmation_id='legacy:'+hashlib.sha256((user_id+digest).encode()).hexdigest()
        if confirmation_id:
            receipt=db.execute('SELECT record_id,digest FROM journal_receipts WHERE user_id=? AND confirmation_id=?',
                               (user_id,confirmation_id)).fetchone()
            if receipt:
                if receipt[1]!=digest:
                    raise ValueError('日志已编辑或删除，请重新审阅。 / Review the changed journal entry.')
                row=db.execute('SELECT id,payload,timestamp FROM journal WHERE id=? AND user_id=?',
                               (receipt[0],user_id)).fetchone()
                if not row:
                    raise KeyError('Journal entry not found')
                return self.record(*row)
        record_id=str(uuid.uuid4())
        stamp=datetime.now(timezone.utc).isoformat()
        if include_transcript:
            if not transcript:
                raise ValueError('No transcript available')
            transcript_id=str(uuid.uuid4())
            now=time.time()
            db.execute('DELETE FROM transcript_records WHERE expires_at<=?',(now,))
            db.execute('INSERT INTO transcript_records VALUES (?,?,?,?,?)',
                       (transcript_id,user_id,json.dumps(transcript,ensure_ascii=False),now,now+RETENTION_SECONDS))
            payload['transcript_id']=transcript_id
        raw=json.dumps(payload,ensure_ascii=False)
        db.execute('INSERT INTO journal VALUES (?,?,?,?)',(record_id,user_id,raw,stamp))
        if confirmation_id:
            db.execute('INSERT INTO journal_receipts VALUES (?,?,?,?)',(user_id,confirmation_id,record_id,digest))
        return self.record(record_id,raw,stamp)

    def edit(self,user_id,record_id,expected_version,edits):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload,timestamp FROM journal WHERE id=? AND user_id=?',(record_id,user_id)).fetchone()
            if not row:
                raise KeyError('Journal entry not found')
            payload=json.loads(row[0])
            version=payload.get('version',1)
            if version!=expected_version:
                raise ValueError('日志版本已变更，请重新读取。 / Reload the latest journal version.')
            payload.update(edits,version=version+1)
            raw=json.dumps(payload,ensure_ascii=False)
            db.execute('UPDATE journal SET payload=? WHERE id=? AND user_id=?',(raw,record_id,user_id))
            db.execute('UPDATE journal_receipts SET digest=NULL WHERE record_id=? AND user_id=?',(record_id,user_id))
        return self.record(record_id,raw,row[1])

    def delete(self,user_id,record_id):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload FROM journal WHERE id=? AND user_id=?',(record_id,user_id)).fetchone()
            if not row:
                raise KeyError('Journal entry not found')
            transcript_id=json.loads(row[0]).get('transcript_id')
            if transcript_id:
                db.execute('DELETE FROM transcript_records WHERE id=? AND user_id=?',(transcript_id,user_id))
            db.execute('DELETE FROM journal WHERE id=? AND user_id=?',(record_id,user_id))
            db.execute('UPDATE journal_receipts SET digest=NULL WHERE record_id=? AND user_id=?',(record_id,user_id))
        return {'deleted':True}
