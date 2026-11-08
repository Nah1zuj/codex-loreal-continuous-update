import math
from collections import Counter
from app.rag.embeddings import tokenize,MockEmbeddingProvider,RemoteEmbeddingProvider
from app.rag.reranker import MockReranker,RemoteRerankerAdapter
from app.knowledge.vocabulary import Vocabulary
from app.knowledge.policy import eligible, is_reviewed
from app.knowledge.repository import atomic_json

class HybridRetriever:
    def __init__(self,store,settings,embedding=None,reranker=None):
        self.settings=settings;self.documents=store.documents()
        self.embedding=embedding or (MockEmbeddingProvider() if settings.embedding_provider=='mock' else RemoteEmbeddingProvider(settings))
        self.reranker=reranker or (MockReranker() if settings.reranker_provider=='mock' else RemoteRerankerAdapter())
        self.vectors=self.embedding.embed([d['content'] for d in self.documents])
        self.counts=[Counter(tokenize(d['content'])) for d in self.documents]
        self.df=Counter(t for count in self.counts for t in count)
        self.avg_len=sum(sum(x.values()) for x in self.counts)/max(1,len(self.counts))
    def permitted(self,metadata):
        if metadata.get('subtype')=='makeup_lesson':
            return bool(metadata.get('source_rights_confirmed')) and (
                is_reviewed(metadata) or (self.settings.developer_mode and eligible(metadata,self.settings))
            )
        return eligible(metadata,self.settings)
    def search(self,query,filters=None,limit=5):return self._search(query,filters or {},limit)
    def debug_search(self,query,filters=None,limit=20):
        parsed=Vocabulary().parse_query(query);parsed.update(filters or {})
        return {**self._search(query,parsed,limit),'parsed_filters':parsed,'policy':'research/developer' if self.settings.developer_mode or self.settings.research_mode else 'human-reviewed (non-demo)'}
    def _search(self,query,filters,limit):
        allowed={'scene','look_id','makeup_area','document_type','verified','source_type','parent_id','demo_data','status','subtype','language'}
        if any(k not in allowed for k in filters):raise ValueError('Unsupported metadata filter')
        query_vector=self.embedding.embed([query])[0];tokens=set(tokenize(query));hits=[]
        for doc,vector,count in zip(self.documents,self.vectors,self.counts):
            metadata=doc['metadata']
            if not self.permitted(metadata):continue
            def matches(key,value):
                actual=metadata.get(key)
                return value in actual if isinstance(actual,list) else str(actual).lower()==str(value).lower()
            if not all(matches(k,v) for k,v in filters.items()):continue
            lexical=0.;length=sum(count.values())
            for token in tokens:
                freq=count.get(token,0);idf=math.log(1+(len(self.documents)-self.df[token]+.5)/(self.df[token]+.5))
                lexical+=idf*freq*2.2/(freq+1.2*(.25+.75*length/max(1,self.avg_len)))
            cosine=sum(a*b for a,b in zip(vector,query_vector))/((math.sqrt(sum(x*x for x in vector))*math.sqrt(sum(x*x for x in query_vector))) or 1)
            semantic=max(0,cosine);score=.55*lexical/(1+lexical)+.45*semantic
            if score>0:hits.append({**doc,'score':round(score,6),'semantic_score':round(semantic,6),'lexical_score':round(lexical,6)})
        merged=sorted(hits,key=lambda x:x['score'],reverse=True);ranked=self.reranker.rerank(query,merged)
        # A reranker may reorder candidates, but cannot introduce or alter knowledge.
        originals={row['document_id']:row for row in merged};seen=set();safe=[]
        for row in ranked:
            rid=row.get('document_id')
            if rid in originals and rid not in seen:
                safe.append(originals[rid]);seen.add(rid)
        ranked=safe
        return {'query':query,'results':ranked[:limit],'semantic_results':sorted(hits,key=lambda x:x['semantic_score'],reverse=True)[:limit],'lexical_results':sorted(hits,key=lambda x:x['lexical_score'],reverse=True)[:limit],'merged_results':merged[:limit],'reranked_results':ranked[:limit],'embedding_mode':type(self.embedding).__name__}
    def persist(self,path):atomic_json(path,{'format_version':2,'embedding_provider':type(self.embedding).__name__,'documents':self.documents,'vectors':self.vectors})
