"""Owner-scoped summary preparation, confirmation, and explicit reuse."""
import hashlib
import json
import time

from app.memory.migrations import RETENTION_SECONDS, prune_progress
from app.schemas.makeup import MakeupPlan

VALID_STYLES = {'natural', 'warm', 'professional', 'evening', 'beginner'}


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class RecollectionStore:
    def __init__(self, memory):
        self.memory = memory
        with memory.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS look_recollections (session_id TEXT PRIMARY KEY,user_id TEXT NOT NULL,payload TEXT NOT NULL,updated_at REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS recollection_settings (user_id TEXT PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 1)')

    def subject(self, candidate_id, principal_prefix):
        kind, separator, sid = candidate_id.partition(':')
        if not separator or not sid or kind not in ('plan','legacy'):
            raise KeyError('Summary candidate not found')
        with self.memory.connect() as db:
            existing=db.execute('SELECT user_id FROM confirmed_summaries WHERE candidate_id=?',(candidate_id,)).fetchall()
            if kind=='plan':
                source=db.execute('SELECT user_id FROM makeup_sessions WHERE session_id=?',(sid,)).fetchall()
            else:
                source=db.execute('SELECT user_id FROM look_recollections WHERE session_id=?',(sid,)).fetchall()
        subject=next((row[0] for row in (*existing,*source) if row[0].startswith(principal_prefix)),None)
        if subject is None:
            raise KeyError('Summary candidate not found')
        return subject

    @staticmethod
    def _prune(db, now):
        db.execute('DELETE FROM look_recollections WHERE updated_at<=?', (now-RETENTION_SECONDS,))
        db.execute('DELETE FROM confirmed_summaries WHERE expires_at<=?', (now,))
        db.execute('DELETE FROM summary_dismissals WHERE expires_at<=?', (now,))

    @staticmethod
    def _dismiss(db, user_id, candidate_id, now):
        db.execute('INSERT OR REPLACE INTO summary_dismissals VALUES (?,?,?)',
                   (user_id,candidate_id,now+RETENTION_SECONDS))

    def view(self, user_id):
        with self.memory.connect() as db:
            now=time.time()
            self._prune(db,now)
            prune_progress(db,now)
            setting=db.execute('SELECT enabled FROM recollection_settings WHERE user_id=?',(user_id,)).fetchone()
            confirmed=db.execute(
                'SELECT candidate_id,version,payload,saved_at,reusable FROM confirmed_summaries '
                'WHERE user_id=? ORDER BY saved_at DESC,candidate_id', (user_id,),
            ).fetchall()
            old=db.execute('SELECT session_id,payload FROM look_recollections WHERE user_id=? ORDER BY updated_at DESC',
                           (user_id,)).fetchall()
        enabled=setting is None or bool(setting[0])
        entries=[self._saved(*row) for row in confirmed]
        confirmed_ids={row['id'] for row in entries}
        latest=next((entry for entry in entries if entry['reusable']),None) if enabled else None
        entries.extend({**json.loads(payload),'id':f'legacy:{sid}','origin':'legacy_automatic','reusable':False}
                       for sid,payload in old if f'legacy:{sid}' not in confirmed_ids)
        return {'enabled':enabled,'latest':latest,'entries':entries,'retention_days':30}

    @staticmethod
    def _saved(candidate_id, version, payload, saved_at, reusable):
        public=json.loads(payload)
        public.pop('_confirmed_edits_digest',None)
        return {**public,'id':candidate_id,'version':version,'saved_at':saved_at,'reusable':bool(reusable)}

    def _candidate(self, db, user_id, candidate_id, edits, now):
        kind, _, sid = candidate_id.partition(':')
        if db.execute('SELECT 1 FROM summary_dismissals WHERE user_id=? AND candidate_id=? AND expires_at>?',
                      (user_id,candidate_id,now)).fetchone():
            raise KeyError('Summary candidate dismissed')
        if kind=='plan':
            row=db.execute('SELECT payload FROM makeup_sessions WHERE user_id=? AND session_id=? AND updated_at>?',
                           (user_id,sid,now-RETENTION_SECONDS)).fetchone()
            if row is None:
                raise KeyError('Summary candidate not found')
            plan=MakeupPlan.model_validate_json(row[0])
            if plan.status!='completed':
                raise KeyError('Summary candidate not found')
            facts={'session_id':sid,'name':plan.name,'date':plan.date,'occasion':plan.occasion,
                   'style':plan.needs.style,'completed_steps':[step.title for step in plan.steps if step.status=='completed'],
                   'all_steps_completed':all(step.status=='completed' for step in plan.steps),'origin':'confirmed_course'}
            source_version=[plan.id,plan.revision]
        elif kind=='legacy':
            row=db.execute('SELECT payload,updated_at FROM look_recollections WHERE user_id=? AND session_id=? AND updated_at>?',
                           (user_id,sid,now-RETENTION_SECONDS)).fetchone()
            if row is None:
                raise KeyError('Summary candidate not found')
            original=json.loads(row[0])
            facts={key:original[key] for key in ('name','date','occasion','style','completed_steps','all_steps_completed')
                   if key in original}
            facts.update(session_id=sid,origin='legacy_reconfirmed')
            facts.setdefault('style','natural')
            facts.setdefault('completed_steps',[])
            facts.setdefault('all_steps_completed',False)
            source_version=row[1]
        else:
            raise KeyError('Summary candidate not found')
        facts['name']=str(facts.get('name','TRACE'))[:100]
        facts['note']=''
        facts.update(edits)
        version=hashlib.sha256(_encoded([user_id,candidate_id,source_version,facts]).encode()).hexdigest()
        return {'candidate_id':candidate_id,'version':version,'summary':facts}

    def prepare(self, user_id, candidate_id, edits=None):
        with self.memory.connect() as db:
            now=time.time()
            if db.execute('SELECT 1 FROM confirmed_summaries WHERE user_id=? AND candidate_id=? AND expires_at>?',
                          (user_id,candidate_id,now)).fetchone():
                raise KeyError('Summary already confirmed')
            return self._candidate(db,user_id,candidate_id,edits or {},now)

    def decide(self, user_id, candidate_id, version, edits, *, save):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            now=time.time()
            self._prune(db,now)
            existing=db.execute('SELECT candidate_id,version,payload,saved_at,reusable FROM confirmed_summaries '
                                'WHERE user_id=? AND candidate_id=?',(user_id,candidate_id)).fetchone()
            edits_digest=hashlib.sha256(_encoded(edits).encode()).hexdigest()
            if existing:
                if save and existing[1]==version:
                    saved=self._saved(*existing)
                    if json.loads(existing[2]).get('_confirmed_edits_digest')!=edits_digest:
                        raise ValueError('摘要内容已修改，请重新审阅。 / Review the changed summary.')
                    return {'saved':True,'duplicate':True,'record':saved}
                raise ValueError('该摘要已有确认版本。 / A confirmed version already exists.')
            candidate=self._candidate(db,user_id,candidate_id,edits,now)
            if candidate['version']!=version:
                raise ValueError('摘要内容已修改，请重新审阅。 / Review the changed summary.')
            if not save:
                self._dismiss(db,user_id,candidate_id,now)
                return {'saved':False,'rejected':True}
            raw=_encoded({**candidate['summary'],'_confirmed_edits_digest':edits_digest})
            db.execute('INSERT INTO confirmed_summaries VALUES (?,?,?,?,?,?,0)',
                       (user_id,candidate_id,version,raw,now,now+RETENTION_SECONDS))
            return {'saved':True,'duplicate':False,'record':self._saved(candidate_id,version,raw,now,False)}

    def setting(self, user_id, enabled):
        with self.memory.connect() as db:
            db.execute('INSERT INTO recollection_settings VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET enabled=excluded.enabled',
                       (user_id,int(enabled)))
        return self.view(user_id)

    def select(self, user_id, record_id):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM confirmed_summaries WHERE user_id=? AND candidate_id=? AND expires_at>?',
                              (user_id,record_id,time.time())).fetchone():
                raise KeyError('Confirmed summary not found')
            db.execute('UPDATE confirmed_summaries SET reusable=(candidate_id=?) WHERE user_id=?',(record_id,user_id))
            db.execute('INSERT OR REPLACE INTO recollection_settings VALUES (?,1)',(user_id,))
        return self.view(user_id)

    def reusable_style(self, user_id):
        item=self.view(user_id)['latest']
        return item['style'] if item and item.get('style') in VALID_STYLES else 'natural'

    def remove(self, user_id, record_id):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            result=db.execute('DELETE FROM confirmed_summaries WHERE user_id=? AND candidate_id=?',(user_id,record_id))
            removed=result.rowcount>0
            if record_id.startswith('legacy:'):
                result=db.execute('DELETE FROM look_recollections WHERE user_id=? AND session_id=?',
                                  (user_id,record_id.removeprefix('legacy:')))
                removed=removed or result.rowcount>0
            if not removed:
                raise KeyError('Summary not found')
            self._dismiss(db,user_id,record_id,time.time())
        return self.view(user_id)

    def clear(self, user_id):
        with self.memory.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for (candidate_id,) in db.execute('SELECT candidate_id FROM confirmed_summaries WHERE user_id=?',(user_id,)):
                self._dismiss(db,user_id,candidate_id,time.time())
            db.execute('DELETE FROM confirmed_summaries WHERE user_id=?',(user_id,))
            db.execute('DELETE FROM look_recollections WHERE user_id=?',(user_id,))
        return self.view(user_id)
