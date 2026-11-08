import sys
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.knowledge.repository import KnowledgeRepository

def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=ROOT/'data/knowledge');a=p.parse_args()
    report=KnowledgeRepository(a.directory).validate()
    print(report['status'])
    for level in ('errors','warnings'):
        for e in report[level]:print(f"{'ERROR' if level=='errors' else 'WARNING'} {e['type']} row {e['row']} [{e['field']}]: {e['message']}")
    print('Records:',{k:len(v) for k,v in report['records'].items()})
    if report['errors']:raise SystemExit(1)

if __name__=='__main__':main()
