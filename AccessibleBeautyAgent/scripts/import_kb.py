import sys
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.knowledge.repository import KnowledgeRepository,atomic_json
from app.knowledge.importer import import_file

def main():
    p=argparse.ArgumentParser(description='Preview or commit CSV/XLSX as drafts; reviewed records are never overwritten.')
    p.add_argument('--file',type=Path,required=True)
    p.add_argument('--type',choices=['LOOK','ROUTINE','REFERENCE_CASE','PRODUCT','ACCESSIBILITY_GUIDANCE','SOURCE'])
    p.add_argument('--commit',action='store_true',help='Save accepted rows as canonical drafts')
    args=p.parse_args();s=Settings()
    report=import_file(args.file,KnowledgeRepository(s.knowledge_dir,s.history_dir),args.type,args.commit)
    output=s.reports_dir/(report['report_id']+'.json');atomic_json(output,report)
    atomic_json(ROOT/'data/import/staged'/(report['report_id']+'.json'),report['records'])
    print(f"Rows={report['total_rows']} accepted={report['accepted']} rejected={report['rejected']} warnings={report['warnings']} committed={report['committed']}")
    print('Report:',output)
    for e in report['errors']:print(f"ERROR {e['sheet']} row {e['row']} [{e['field']}]: {e['message']}")
    if report['rejected']:raise SystemExit(1)

if __name__=='__main__':main()
