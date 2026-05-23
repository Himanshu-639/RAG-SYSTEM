import chromadb
import ollama
import uuid
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

def add_to_knowledge_base(text_content: str, metadata: dict):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=60,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.split_text(text_content)

    #Handling ChromaDB max batch size of 5461        
    if chunks:
        batch_size = 5000
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i: i+batch_size]

            batch_metadatas = [metadata for _ in batch_chunks]
            collection.add(
                ids = [str(uuid.uuid4()) for _ in batch_chunks],
                documents=batch_chunks,
                metadatas=batch_metadatas
            )
    return len(chunks)

def query_knowledge_base(query: str, n_results: int = 7):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results['documents'][0], results['metadatas'][0] if results['documents'] else []