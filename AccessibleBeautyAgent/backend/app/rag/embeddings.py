import hashlib
import re
import math
from typing import Protocol

def tokenize(text):
    text = text.lower()
    words = re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]', text)
    # Chinese bigrams improve matching without another tokenizer dependency.
    words += [text[i:i+2] for i in range(len(text)-1) if all('\u4e00' <= c <= '\u9fff' for c in text[i:i+2])]
    return words

class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

class MockEmbeddingProvider:
    """Deterministic hashed bag-of-words proxy, not a semantic model."""
    def embed(self, texts):
        vectors = []
        for text in texts:
            vector = [0.] * 256
            for token in tokenize(text):
                digest = hashlib.sha256(token.encode()).digest()
                index = int.from_bytes(digest[:4], 'little') % 256
                vector[index] += 1 if digest[4] & 1 else -1
            norm = math.sqrt(sum(x*x for x in vector)) or 1
            vectors.append([x / norm for x in vector])
        return vectors

class RemoteEmbeddingProvider:
    def __init__(self, settings):
        from app.services.qwen import QwenClient
        self.client = QwenClient(settings)
        self.model = settings.embedding_model
    def embed(self, texts):
        output = []
        for i in range(0,len(texts),10):
            data = self.client.request('/embeddings', {'model':self.model,'input':texts[i:i+10]})
            output.extend(x['embedding'] for x in sorted(data['data'],key=lambda x:x['index']))
        return output
