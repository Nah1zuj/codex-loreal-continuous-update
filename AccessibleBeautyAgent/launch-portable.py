"""One entry point for the portable release. Only owned children are terminated."""
from pathlib import Path
import atexit,json,os,shutil,signal,socket,subprocess,sys,time,urllib.request,webbrowser
ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:5180/'
RELEASE='TRACE-20261020-portable'
children=[];logs=[]
def read_json(url):
    with urllib.request.urlopen(url,timeout=2) as response:return json.load(response)
def occupied(port):
    with socket.socket() as sock:return sock.connect_ex(('127.0.0.1',port))==0
def cleanup():
    for child in children:
        if child.poll() is None:child.terminate()
    for child in children:
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()
    for log in logs:log.close()
def start():
    os.chdir(ROOT)
    if any(occupied(port) for port in (5180,8012,8013)):
        try:
            assert read_json(URL+'release.json')['release']==RELEASE
            assert read_json(URL+'api/health')['status']=='ok'
            assert read_json(URL+'local-voice/health')['ready']
        except Exception:raise RuntimeError('本版本端口被占用或服务不完整。请先关闭之前的本版本启动终端，再重试。没有停止其他程序。')
        print('本版本已运行：'+URL,flush=True);webbrowser.open(URL);return
    node=shutil.which('node')
    if not node:raise RuntimeError('未找到 Node.js 22.12+。')
    (ROOT/'work').mkdir(exist_ok=True)
    env=os.environ.copy();env['MPLCONFIGDIR']=str(ROOT/'work/matplotlib')
    commands=[('backend',[sys.executable,'-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8012','--timeout-graceful-shutdown','3']),('voice',[sys.executable,'-m','uvicorn','server:app','--app-dir','voice','--host','127.0.0.1','--port','8013','--timeout-graceful-shutdown','3']),('frontend',[node,'frontend/node_modules/vite/bin/vite.js','frontend','--config',str(ROOT/'frontend/vite.package.config.ts')])]
    for name,command in commands:
        log=(ROOT/'work'/('portable-'+name+'.log')).open('ab');logs.append(log)
        children.append(subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT))
    print('正在启动最新版，请稍候…',flush=True)
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        if any(child.poll() is not None for child in children):raise RuntimeError('有服务退出，请查看 AccessibleBeautyAgent/work/portable-*.log。')
        try:
            assert read_json(URL+'release.json')['release']==RELEASE
            assert read_json(URL+'api/health')['status']=='ok'
            assert read_json(URL+'local-voice/health')['ready']
            break
        except Exception:time.sleep(.5)
    else:raise RuntimeError('启动超时，请查看 AccessibleBeautyAgent/work/portable-*.log。')
    print('最新版已就绪：'+URL+'\n保留此窗口。Control+C 停止本次启动的服务。',flush=True)
    if '--no-browser' not in sys.argv:webbrowser.open(URL)
    while all(child.poll() is None for child in children):time.sleep(.5)
    raise RuntimeError('服务已停止，请查看日志。')
if __name__=='__main__':
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
    try:start()
    except KeyboardInterrupt:print('\nDemo已停止。')
    except Exception as error:print(str(error),file=sys.stderr);sys.exit(1)
