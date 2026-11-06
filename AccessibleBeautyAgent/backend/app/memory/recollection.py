"""Small, owner-scoped look summaries. Never stores audio or full conversation."""
import json,time

class RecollectionStore:
    def __init__(self,memory):
        self.memory=memory
        with memory.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS look_recollections (session_id TEXT PRIMARY KEY,user_id TEXT NOT NULL,payload TEXT NOT NULL,updated_at REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS recollection_settings (user_id TEXT PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 1)')
    def enabled(self,user_id):
        with self.memory.connect() as db:
            row=db.execute('SELECT enabled FROM recollection_settings WHERE user_id=?',(user_id,)).fetchone()
        return row is None or bool(row[0])
    def remember(self,session):
        p=session.makeup_plan
        if not p or p.status!='completed' or not self.enabled(session.user_id):return None
        payload={'session_id':session.session_id,'name':p.name,'date':p.date,'occasion':p.occasion,'style':p.needs.style,'completed_steps':[s.title for s in p.steps if s.status=='completed'],'all_steps_completed':all(s.status=='completed' for s in p.steps),'record_kind':'look_summary'}
        with self.memory.connect() as db:
            db.execute('INSERT INTO look_recollections VALUES (?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at WHERE look_recollections.user_id=excluded.user_id',(session.session_id,session.user_id,json.dumps(payload,ensure_ascii=False),time.time()))
            db.execute('DELETE FROM look_recollections WHERE user_id=? AND session_id NOT IN (SELECT session_id FROM look_recollections WHERE user_id=? ORDER BY updated_at DESC LIMIT 12)',(session.user_id,session.user_id))
        return payload
    def view(self,user_id):
        with self.memory.connect() as db:
            db.execute('DELETE FROM look_recollections WHERE updated_at<?',(time.time()-30*86400,))
            rows=db.execute('SELECT payload FROM look_recollections WHERE user_id=? ORDER BY updated_at DESC LIMIT 12',(user_id,)).fetchall()
        entries=[json.loads(row[0]) for row in rows]
        return {'enabled':self.enabled(user_id),'latest':entries[0] if entries else None,'entries':entries,'retention_days':30}
    def setting(self,user_id,enabled):
        with self.memory.connect() as db:db.execute('INSERT INTO recollection_settings VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET enabled=excluded.enabled',(user_id,int(enabled)))
        return self.view(user_id)
    def clear(self,user_id):
        with self.memory.connect() as db:db.execute('DELETE FROM look_recollections WHERE user_id=?',(user_id,))
        return self.view(user_id)
