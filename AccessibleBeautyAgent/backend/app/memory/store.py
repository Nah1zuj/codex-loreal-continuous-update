import sqlite3
import json
import uuid
from datetime import datetime, timezone

class MemoryStore:
    def __init__(self, path):
        self.path = path
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
            episodes.append({'memory_id':mid,**c,'timestamp':timestamp})
        return {'user_id':user_id,'profile':profile,'episodes':episodes}

    def save(self, user_id, candidate, explicit_consent):
        if explicit_consent is not True:
            raise PermissionError('保存长期偏好需要明确同意。')
        from app.schemas.models import MemoryCandidate
        candidate = MemoryCandidate.model_validate(candidate).model_dump()
        mid = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('INSERT INTO memories VALUES (?,?,?,?)',(mid,user_id,json.dumps(candidate,ensure_ascii=False),timestamp))
        return {'memory_id':mid,'timestamp':timestamp,'saved':True}

    def delete(self, user_id, memory_id, explicit_consent):
        if explicit_consent is not True:
            raise PermissionError('删除记忆需要明确同意。')
        with self.connect() as db:
            cursor = db.execute('DELETE FROM memories WHERE id=? AND user_id=?',(memory_id,user_id))
            if cursor.rowcount == 0:
                raise KeyError('Memory not found')
        return {'deleted':True,'memory_id':memory_id}

    def update(self,user_id,memory_id,candidate,explicit_consent):
        if explicit_consent is not True:raise PermissionError('修改长期偏好需要明确同意。')
        from app.schemas.models import MemoryCandidate
        value=MemoryCandidate.model_validate(candidate).model_dump()
        timestamp=datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            cursor=db.execute('UPDATE memories SET candidate=?,timestamp=? WHERE id=? AND user_id=?',(json.dumps(value,ensure_ascii=False),timestamp,memory_id,user_id))
            if cursor.rowcount==0:raise KeyError('Memory not found')
        return {'memory_id':memory_id,'timestamp':timestamp,'updated':True}

    def healthy(self):
        with self.connect() as db:
            return db.execute('SELECT 1').fetchone()[0] == 1
