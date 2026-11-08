"""Port reviewed tracked source groups from a credential-free fixed snapshot."""
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'.baseline/fd6154a'
APP='AccessibleBeautyAgent/'
A=('backend/app/config.py','backend/app/__init__.py','backend/app/schemas/','backend/app/memory/','backend/app/knowledge/','backend/app/rag/','backend/app/products/','backend/app/looks/','backend/app/content/','backend/app/services/','backend/app/policies/','data/','prompts/','templates/','runtime.py','runtime.json','backend/requirements','scripts/validate_kb.py','.env.example','.gitignore')
B=('backend/app/','tests/','pytest.ini','scripts/extract_video_frames.py')
C=('voice/','hardware/')
D=('frontend/',)
E=('scripts/','install-portable','launch-portable','start-portable','README.md')

def group_for(rel):
    if rel.startswith(APP):
        local=rel[len(APP):]
        if local.startswith(A):return 'A'
        if local.startswith(B):return 'B'
        if local.startswith(C):return 'C'
        if local.startswith(D):return 'D'
        if local.startswith(E):return 'E'
    elif rel in ('.gitignore','启动Demo_Mac.command','启动Demo_Windows.bat','首次安装_Mac.command','首次安装_Windows.bat','00_先读我_运行说明.txt'):
        return 'E'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('group',choices=list('ABCDE'));args=parser.parse_args()
    manifest=ROOT/'migration/port-manifest.json'
    entries=json.loads(manifest.read_text()) if manifest.exists() else []
    for source in sorted(BASE.rglob('*')):
        if not source.is_file():continue
        rel=source.relative_to(BASE).as_posix()
        if group_for(rel)!=args.group:continue
        if source.name=='.env' or source.suffix in ('.sqlite','.db','.onnx') or '/data/users/' in rel:raise ValueError(rel)
        dest=ROOT/rel
        if dest.exists():raise FileExistsError(dest)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        entries.append({'path':rel,'group':args.group,'baseline_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    manifest.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    print(f"Group {args.group}: {sum(e['group']==args.group for e in entries)} files ported")
if __name__=='__main__':main()
