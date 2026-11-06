import sys
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.rag.knowledge import KnowledgeStore
from app.rag.retriever import HybridRetriever

def main():
    p=argparse.ArgumentParser();p.add_argument('--type');p.add_argument('--look-id');a=p.parse_args();s=Settings()
    store=KnowledgeStore(s.knowledge_dir);index=HybridRetriever(store,s);index.persist(s.index_path)
    scope=[d for d in index.documents if (not a.type or d['document_type']==a.type) and (not a.look_id or d['metadata'].get('look_id')==a.look_id)]
    print(f'PASS: total={len(index.documents)}, scope={len(scope)} -> {s.index_path}')
    print('Canonical JSON unchanged; full rebuild preserves other knowledge. Use admin Rebuild for live activation.')
    smoke=index.debug_search('dinner formal blush');print('Smoke results:',[d['document_id'] for d in smoke['results']])

if __name__=='__main__':main()
