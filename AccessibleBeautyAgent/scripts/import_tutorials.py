"""python scripts/import_tutorials.py authorized-segments.json [--commit]

Local bounded JSON text only; use the existing admin review/index workflow next.
"""
import sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.tutorial_ingestion import TutorialImporter

def main():
    parser=argparse.ArgumentParser();parser.add_argument('file',type=Path);parser.add_argument('--commit',action='store_true');args=parser.parse_args()
    if args.file.suffix.lower()!='.json':raise ValueError('Only JSON tutorial segment files are accepted')
    if args.file.stat().st_size>4_000_000:raise ValueError('Tutorial file too large')
    registry=json.loads((ROOT/'data/config/knowledge_sources.json').read_text(encoding='utf-8'))
    result=TutorialImporter(KnowledgeRepository(ROOT/'data/knowledge'),registry).import_segments(json.loads(args.file.read_text(encoding='utf-8')),args.commit)
    print(json.dumps({key:value for key,value in result.items() if key!='records'},ensure_ascii=False))
if __name__=='__main__':main()
