"""Additive SQLite migrations; legacy records retained, never reassigned."""
def migrate(memory):
    with memory.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        db.execute('CREATE TABLE IF NOT EXISTS transcript_records (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL,expires_at REAL NOT NULL)')
        db.execute('CREATE INDEX IF NOT EXISTS transcript_owner ON transcript_records(user_id,expires_at)')
        db.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)')
        db.execute('CREATE TABLE IF NOT EXISTS makeup_sessions (session_id TEXT PRIMARY KEY,user_id TEXT NOT NULL,locale TEXT NOT NULL,payload TEXT NOT NULL,updated_at REAL NOT NULL)')
        db.execute('CREATE INDEX IF NOT EXISTS makeup_owner ON makeup_sessions(user_id,updated_at)')
        db.execute('CREATE TABLE IF NOT EXISTS makeup_events (session_id TEXT NOT NULL,event_id TEXT NOT NULL,intent TEXT NOT NULL,PRIMARY KEY(session_id,event_id))')
        db.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (2)')
        if not db.execute('SELECT 1 FROM schema_migrations WHERE version=3').fetchone():
            db.execute(
                'CREATE TABLE IF NOT EXISTS makeup_event_receipts '
                '(session_id TEXT NOT NULL,event_id TEXT NOT NULL,details TEXT NOT NULL,PRIMARY KEY(session_id,event_id))'
            )
            db.execute(
                'CREATE TRIGGER IF NOT EXISTS remove_makeup_event_receipt AFTER DELETE ON makeup_events '
                'BEGIN DELETE FROM makeup_event_receipts WHERE session_id=OLD.session_id AND event_id=OLD.event_id; END'
            )
            db.execute('INSERT INTO schema_migrations(version) VALUES (3)')
        if not db.execute('SELECT 1 FROM schema_migrations WHERE version=4').fetchone():
            db.execute(
                'CREATE TABLE IF NOT EXISTS confirmed_summaries ('
                'user_id TEXT NOT NULL,candidate_id TEXT NOT NULL,version TEXT NOT NULL,payload TEXT NOT NULL,'
                'saved_at REAL NOT NULL,expires_at REAL NOT NULL,reusable INTEGER NOT NULL DEFAULT 0,'
                'PRIMARY KEY(user_id,candidate_id))'
            )
            db.execute(
                'CREATE TABLE IF NOT EXISTS summary_dismissals ('
                'user_id TEXT NOT NULL,candidate_id TEXT NOT NULL,expires_at REAL NOT NULL,'
                'PRIMARY KEY(user_id,candidate_id))'
            )
            db.execute(
                'CREATE TRIGGER IF NOT EXISTS remove_expired_progress_events AFTER DELETE ON makeup_sessions '
                'BEGIN DELETE FROM makeup_events WHERE session_id=OLD.session_id; END'
            )
            db.execute('INSERT INTO schema_migrations(version) VALUES (4)')
        if not db.execute('SELECT 1 FROM schema_migrations WHERE version=5').fetchone():
            db.execute(
                'CREATE TABLE IF NOT EXISTS journal_receipts ('
                'user_id TEXT NOT NULL,confirmation_id TEXT NOT NULL,record_id TEXT NOT NULL,digest TEXT,'
                'PRIMARY KEY(user_id,confirmation_id))'
            )
            db.execute('INSERT INTO schema_migrations(version) VALUES (5)')
        if not db.execute('SELECT 1 FROM schema_migrations WHERE version=6').fetchone():
            db.execute(
                'CREATE TABLE IF NOT EXISTS preference_receipts ('
                'user_id TEXT NOT NULL,candidate_id TEXT NOT NULL,version TEXT NOT NULL,scope TEXT NOT NULL,'
                'record_id TEXT NOT NULL,stamp TEXT NOT NULL,digest TEXT,PRIMARY KEY(user_id,candidate_id))'
            )
            db.execute('INSERT INTO schema_migrations(version) VALUES (6)')
        prune_progress(db)


RETENTION_SECONDS = 30 * 86400


def prune_progress(db, now=None):
    from time import time
    cutoff=(time() if now is None else now)-RETENTION_SECONDS
    db.execute('DELETE FROM makeup_sessions WHERE updated_at<=?',(cutoff,))
