"""Phase 1 compatible view over canonical schemas; aliases, no duplicate models."""
from app.schemas.knowledge import BeautyLook as Look,BeautyRoutine as Routine,RoutineStep as Step,BeautyProduct as Product,ReferenceCase as Reference
from app.knowledge.repository import KnowledgeRepository

class KnowledgeStore:
    def __init__(self,directory):
        self.directory=directory
        self.repository=KnowledgeRepository(directory)
        data=self.repository.all()
        self.looks=data['LOOK'];self.routines=data['ROUTINE'];self.products=data['PRODUCT']
        self.references=data['REFERENCE_CASE'];self.guidance=data['ACCESSIBILITY_GUIDANCE'];self.sources=data['SOURCE']
        self.look_map={r['look_id']:r for r in self.looks}
        self.routine_map={r['routine_id']:r for r in self.routines}
    def documents(self):
        from app.rag.document_builder import build_documents
        return build_documents(self)
