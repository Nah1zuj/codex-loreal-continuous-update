import hashlib
import hmac
import secrets
import sqlite3
import json
import uuid
from datetime import datetime, timezone

class MemoryStore:
    def __init__(self, path):
        self.path = path
        self.preview_key = secrets.token_bytes(32)
        path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, candidate TEXT NOT NULL, timestamp TEXT NOT NULL)')

    def connect(self):
        return sqlite3.connect(self.path)

    def profile(self, user_id):
        with self.connect() as db:
            rows = db.execute('SELECT id,candidate,timestamp FROM memories WHERE user_id=? ORDER BY timestamp,id', (user_id,)).fetchall()
        profile = {'preferred_finish':[],'preferred_saturation':None,'avoid':[],'material_preferences':[],'domain_preferences':{}}
        episodes = []
        for mid, raw, timestamp in rows:
            c = json.loads(raw)
            for field in ('preferred_finish','avoid','material_preferences'):
                profile[field] = sorted(set(profile[field] + c.get(field,[])))
            for key,values in c.get('domain_preferences',{}).items():profile['domain_preferences'][key]=values
            if c.get('preferred_saturation'):
                profile['preferred_saturation'] = c['preferred_saturation']
            episodes.append({'memory_id':mid,**c,'timestamp':timestamp,'version':timestamp})
        return {'user_id':user_id,'profile':profile,'episodes':episodes}

    @staticmethod
    def _candidate(value):
        from app.schemas.models import MemoryCandidate
        return MemoryCandidate.model_validate(value).model_dump(mode='json')

    @staticmethod
    def _digest(value):
        return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

    def _token(self,user_id,scope,candidate_id,digest):
        signed=json.dumps([user_id,scope,candidate_id,digest]).encode()
        return hmac.new(self.preview_key,signed,'sha256').hexdigest()

    def prepare(self,user_id,candidate,*,scope='create',memory_id=None,expected_version=None):
        if memory_id:
            with self.connect() as db:
                row=db.execute('SELECT timestamp FROM memories WHERE user_id=? AND id=?',(user_id,memory_id)).fetchone()
            if row is None:
                raise KeyError('Memory not found')
            if row[0]!=expected_version:
                raise ValueError('偏好版本已变更，请重新读取。 / Reload the latest preference.')
            scope=f'edit:{memory_id}:{expected_version}'
        normalized=self._candidate(candidate)
        candidate_id=str(uuid.uuid4())
        return {'candidate':normalized,'candidate_id':candidate_id,
                'candidate_version':self._token(user_id,scope,candidate_id,self._digest(normalized))}

    def _receipt(self,db,user_id,candidate_id,candidate_version,scope,digest=None):
        row=db.execute('SELECT version,scope,record_id,stamp,digest FROM preference_receipts '
                       'WHERE user_id=? AND candidate_id=?',(user_id,candidate_id)).fetchone()
        if row is None:
            return None
        if row[0]!=candidate_version or row[1]!=scope or row[4] is None or (digest is not None and row[4]!=digest):
            raise ValueError('偏好候选已更改或删除，请重新审阅。 / Review the updated preference.')
        return {'memory_id':row[2],'timestamp':row[3],'saved':True,'duplicate':True}

    def replay(self,user_id,candidate_id,candidate_version,scope):
        if not candidate_id or not candidate_version:
            return None
        with self.connect() as db:
            return self._receipt(db,user_id,candidate_id,candidate_version,scope)

    def save(self,user_id,candidate,explicit_consent,*,candidate_id=None,candidate_version=None,
             scope='create',memory_id=None,expected_version=None):
        if explicit_consent is not True:
            raise PermissionError('保存长期偏好需要明确同意。')
        value=self._candidate(candidate)
        digest=self._digest(value)
        if memory_id:
            scope=f'edit:{memory_id}:{expected_version}'
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT timestamp FROM memories WHERE id=? AND user_id=?',(memory_id,user_id)).fetchone() if memory_id else None
            if memory_id and row is None:
                raise KeyError('Memory not found')
            if not candidate_id or not candidate_version:
                raise ValueError('请先审阅这个版本的偏好候选。 / Review this preference version first.')
            if result:=self._receipt(db,user_id,candidate_id,candidate_version,scope,digest):
                return result
            expected=self._token(user_id,scope,candidate_id,digest)
            if not hmac.compare_digest(expected,candidate_version):
                raise ValueError('偏好候选已更改或过期，请重新审阅。 / Review the updated preference.')
            stamp=datetime.now(timezone.utc).isoformat()
            raw=json.dumps(value,ensure_ascii=False)
            if memory_id:
                if row[0]!=expected_version:
                    raise ValueError('偏好版本已变更，请重新读取。 / Reload the latest preference.')
                db.execute('UPDATE memories SET candidate=?,timestamp=? WHERE id=? AND user_id=?',(raw,stamp,memory_id,user_id))
                db.execute('UPDATE preference_receipts SET digest=NULL WHERE record_id=? AND user_id=?',(memory_id,user_id))
            else:
                memory_id=str(uuid.uuid4())
                db.execute('INSERT INTO memories VALUES (?,?,?,?)',(memory_id,user_id,raw,stamp))
            db.execute('INSERT INTO preference_receipts VALUES (?,?,?,?,?,?,?)',
                       (user_id,candidate_id,candidate_version,scope,memory_id,stamp,digest))
        return {'memory_id':memory_id,'timestamp':stamp,'saved':True,'duplicate':False}

    def delete(self, user_id, memory_id, explicit_consent):
        if explicit_consent is not True:
            raise PermissionError('删除记忆需要明确同意。')
        with self.connect() as db:
            cursor = db.execute('DELETE FROM memories WHERE id=? AND user_id=?',(memory_id,user_id))
            if cursor.rowcount == 0:
                raise KeyError('Memory not found')
            db.execute('UPDATE preference_receipts SET digest=NULL WHERE record_id=? AND user_id=?',(memory_id,user_id))
            # Earlier coaching journals embedded a snapshot of derived preferences.
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='journal'").fetchone():
                rows=db.execute('SELECT id,payload FROM journal WHERE user_id=?',(user_id,)).fetchall()
                for entry_id, raw in rows:
                    entry=json.loads(raw)
                    summary=entry.get('coaching_summary')
                    if not isinstance(summary,dict) or not summary.get('preferences'):
                        continue
                    previous=dict(summary)
                    summary['preferences']={}
                    try:
                        matches=json.loads(entry.get('reflection',''))==previous
                    except (TypeError,ValueError):
                        matches=False
                    if matches:
                        entry['reflection']=json.dumps(summary,ensure_ascii=False)
                    db.execute('UPDATE journal SET payload=? WHERE id=? AND user_id=?',
                               (json.dumps(entry,ensure_ascii=False),entry_id,user_id))
        return {'deleted':True,'memory_id':memory_id}

    def healthy(self):
        with self.connect() as db:
            return db.execute('SELECT 1').fetchone()[0] == 1
