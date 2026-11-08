"""Explicit construction of domain services, independent of HTTP hosting."""
from dataclasses import dataclass
from app.config import Settings
from app.rag.knowledge import KnowledgeStore
from app.rag.retriever import HybridRetriever
from app.looks.service import LookService
from app.products.service import ProductService
from app.memory.store import MemoryStore
from app.memory.recollection import RecollectionStore
from app.memory.migrations import migrate
from app.vision.service import VisionService
from app.agent.state import SessionStore
from app.agent.harness import AgentHarness
from app.agent.conversation import ConversationService
from app.knowledge.admin_service import KnowledgeAdminService


@dataclass(frozen=True)
class ApplicationServices:
    settings: Settings
    agent: AgentHarness
    conversation: ConversationService
    knowledge_admin: KnowledgeAdminService


def build_services(settings: Settings) -> ApplicationServices:
    store = KnowledgeStore(settings.knowledge_dir)
    sessions = SessionStore()
    rag = HybridRetriever(store, settings)
    memory = MemoryStore(settings.memory_path)
    migrate(memory)
    sessions.memory = memory
    agent = AgentHarness(settings, sessions, store, rag, LookService(store, settings),
                         ProductService(store, settings), memory, VisionService(settings))
    agent.recollection = RecollectionStore(memory)
    return ApplicationServices(settings, agent, ConversationService(agent),
                               KnowledgeAdminService(agent, settings))
