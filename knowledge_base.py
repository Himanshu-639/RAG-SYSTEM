import chromadb
import ollama
import uuid
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name):
        self.model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = ollama.embed(model = self.model_name, input=input)['embeddings']
        return embeddings

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
custom_embeddings = CustomEmbeddingFunction(EMBEDDING_MODEL)

chroma_client = chromadb.PersistentClient(path='database/')
collection = chroma_client.get_or_create_collection(
    name = "my-collection",
    embedding_function=custom_embeddings
)

def add_to_knowledge_base(text_content: str):
    chunks = []
    for c in text_content.split('\n'):
        chunks.append(c.strip())
    if chunks:
        collection.add(
            ids = [str(uuid.uuid4()) for _ in chunks],
            documents=chunks
        )
    return len(chunks)

def query_knowledge_base(query: str, n_results: int = 3):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results['documents'][0] if results['documents'] else []