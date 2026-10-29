"""Anonymous browser isolation, not a production account login system."""
import hashlib,json,secrets,time
from http.cookies import SimpleCookie
from urllib.parse import parse_qs,urlencode
from starlette.responses import JSONResponse

class BrowserIdentityMiddleware:
    def __init__(self,app,agent,settings):
        self.app=app;self.agent=agent;self.settings=settings
        with agent.memory.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS browser_identities (token_hash TEXT PRIMARY KEY, principal TEXT NOT NULL, expires REAL NOT NULL)')
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or not scope['path'].startswith('/api'):return await self.app(scope,receive,send)
        headers={k.decode().lower():v.decode() for k,v in scope['headers']}
        async def error(status,message):await JSONResponse({'detail':message},status_code=status)(scope,receive,send)
        origin=headers.get('origin')
        if origin and origin not in {'http://localhost:5173','http://127.0.0.1:5173','http://localhost:5174','http://127.0.0.1:5174','http://localhost:5180','http://127.0.0.1:5180'} and origin!=scope.get('scheme','http')+'://'+headers.get('host',''):
            return await error(403,'Origin is not permitted')
        if scope['path'].startswith('/api/admin') and (not self.settings.developer_mode or (scope.get('client') or ('',))[0] not in {'127.0.0.1','::1','testclient'}):
            return await error(403,'Admin is restricted to local development; configure account authentication before production')
        cookie=SimpleCookie()
        try:cookie.load(headers.get('cookie',''))
        except Exception:return await error(400,'Invalid cookie')
        token=cookie['trace_identity'].value if 'trace_identity' in cookie else ''
        principal=None;now=time.time();new=False
        with self.agent.memory.connect() as db:
            db.execute('DELETE FROM browser_identities WHERE expires<?',(now,))
            row=db.execute('SELECT principal FROM browser_identities WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),now)).fetchone() if token else None
            if row:
                principal=row[0]
                db.execute('UPDATE browser_identities SET expires=? WHERE token_hash=?',(now+30*86400,hashlib.sha256(token.encode()).hexdigest()))
            else:
                if db.execute('SELECT COUNT(*) FROM browser_identities').fetchone()[0]>=2000:return await error(503,'Local identity capacity reached')
                token=secrets.token_urlsafe(32);principal=secrets.token_hex(8);new=True
                db.execute('INSERT INTO browser_identities VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),principal,now+30*86400))
        prefix='u_'+principal+'_';scope.setdefault('state',{})['principal_prefix']=prefix
        def owner(alias):
            if not isinstance(alias,str):return alias
            if alias.startswith('u_'):
                if not alias.startswith(prefix):raise PermissionError()
                return alias
            return prefix+hashlib.sha256(alias.encode()).hexdigest()[:24]
        def own_session(sid):
            session=self.agent.sessions.get(sid)
            if not session.user_id.startswith(prefix):raise PermissionError()
        path=scope['path']
        try:
            for base in ('/api/session/','/api/transcripts/','/api/full-look/','/api/vision/local/','/api/makeup/'):
                if (scope['method']=='GET' and path.startswith(base)) or (scope['method']=='DELETE' and path.startswith(('/api/vision/local/','/api/makeup/'))):
                    sid=path.rsplit('/',1)[1]
                    if sid not in {'plan','revise','confirm','memory-candidate'}:own_session(sid)
            if path.startswith('/api/profile/'):scope['path']='/api/profile/'+owner(path.rsplit('/',1)[1])
            query=parse_qs(scope.get('query_string',b'').decode())
            if 'user_id' in query:query['user_id']=[owner(query['user_id'][0])]
            elif path=='/api/journal':query['user_id']=[owner('demo')]
            scope['query_string']=urlencode(query,doseq=True).encode()
            raw=b''
            if scope['method'] in {'POST','PUT','PATCH','DELETE'}:
                while True:
                    event=await receive()
                    if event['type']=='http.disconnect':return
                    raw+=event.get('body',b'')
                    if len(raw)>26_000_000:return await error(413,'Request is too large')
                    if not event.get('more_body'):break
                if raw and 'application/json' in headers.get('content-type',''):
                    value=json.loads(raw)
                    if isinstance(value,dict):
                        if value.get('session_id'):own_session(value['session_id'])
                        if 'user_id' in value:value['user_id']=owner(value['user_id'])
                        elif path in {'/api/chat','/api/chat/stream','/api/journal','/api/feedback'}:value['user_id']=owner('demo')
                    raw=json.dumps(value,ensure_ascii=False).encode()
                    scope['headers']=[(k,v) for k,v in scope['headers'] if k.lower()!=b'content-length']+[(b'content-length',str(len(raw)).encode())]
        except (PermissionError,KeyError):return await error(404,'Private resource not found')
        except (ValueError,TypeError):return await error(400,'Invalid request')
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered and scope['method'] in {'POST','PUT','PATCH','DELETE'}:delivered=True;return {'type':'http.request','body':raw,'more_body':False}
            return await receive()
        async def response(event):
            if event['type']=='http.response.start':
                event['headers'].append((b'cache-control',b'no-store'))
                value='trace_identity='+token+'; HttpOnly; SameSite=Strict; Path=/api; Max-Age=2592000'+('' if self.settings.developer_mode else '; Secure')
                event['headers'].append((b'set-cookie',value.encode()))
            await send(event)
        return await self.app(scope,replay,response)
