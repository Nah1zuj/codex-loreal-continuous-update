export type Kind='LOOK'|'ROUTINE'|'REFERENCE_CASE'|'PRODUCT'|'ACCESSIBILITY_GUIDANCE'|'SOURCE'
export type RecordData=Record<string,unknown>
export type Vocabulary=Record<string,string[]>
export const idFields:Record<Kind,string>={LOOK:'look_id',ROUTINE:'routine_id',REFERENCE_CASE:'reference_id',PRODUCT:'product_id',ACCESSIBILITY_GUIDANCE:'guidance_id',SOURCE:'source_id'}
export const labels:Record<Kind,string>={LOOK:'妆容 Looks',ROUTINE:'步骤 Routines',REFERENCE_CASE:'参考 References',PRODUCT:'产品 Products',ACCESSIBILITY_GUIDANCE:'无障碍指引',SOURCE:'来源 Sources'}
export interface Dashboard {counts:Record<Kind,number>;verified_references:number;unverified_references:number;rag_documents:number;remote_ai_enabled:boolean;reference_provider:string;records:Record<Kind,RecordData[]>;indexed_versions:Record<string,number>}
export interface SaveReply {record:RecordData;message:string}
export interface AnalysisReply extends SaveReply {protected:boolean;suggested_revision?:RecordData}
export interface SearchHit {document_id:string;document_type:string;title:string;content:string;source:string;score:number;semantic_score:number;lexical_score:number;metadata:RecordData}
export interface DebugResult {query:string;parsed_filters:Record<string,string>;policy:string;embedding_mode:string;results:SearchHit[];semantic_results:SearchHit[];lexical_results:SearchHit[];merged_results:SearchHit[];reranked_results:SearchHit[]}
