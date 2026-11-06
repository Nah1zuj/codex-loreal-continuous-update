"""Owner-scoped access to legacy automatic look summaries."""
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
    def view(self,user_id):
        with self.memory.connect() as db:
            db.execute('DELETE FROM look_recollections WHERE updated_at<?',(time.time()-30*86400,))
            rows=db.execute('SELECT payload FROM look_recollections WHERE user_id=? ORDER BY updated_at DESC LIMIT 12',(user_id,)).fetchall()
        entries=[{**json.loads(row[0]),'origin':'legacy_automatic'} for row in rows]
        return {'enabled':self.enabled(user_id),'latest':None,'entries':entries,'retention_days':30}
    def setting(self,user_id,enabled):
        with self.memory.connect() as db:db.execute('INSERT INTO recollection_settings VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET enabled=excluded.enabled',(user_id,int(enabled)))
        return self.view(user_id)
    def clear(self,user_id):
        with self.memory.connect() as db:db.execute('DELETE FROM look_recollections WHERE user_id=?',(user_id,))
        return self.view(user_id)
