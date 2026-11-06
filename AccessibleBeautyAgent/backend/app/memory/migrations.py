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
