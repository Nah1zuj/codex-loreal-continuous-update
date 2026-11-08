"""Build local vector/metadata snapshot; app rebuilds from canonical files on startup."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.rag.knowledge import KnowledgeStore
from app.rag.retriever import HybridRetriever

def main():
    settings=Settings()
    index=HybridRetriever(KnowledgeStore(settings.knowledge_dir),settings)
    index.persist(settings.index_path)
    print(f'Indexed {len(index.documents)} parent/child documents -> {settings.index_path}')
    print('Startup rebuilds the in-memory index from canonical KB to avoid stale documents.')

if __name__=='__main__':main()
