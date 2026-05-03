import chromadb
import ollama
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name):
        self.model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = ollama.embed(model = self.model_name, input=input)['embeddings']
        return embeddings

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
custom_embeddings = CustomEmbeddingFunction(EMBEDDING_MODEL)

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name = "my-collection",
    embedding_function=custom_embeddings
)

with open("cat-facts.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
    print(f"Total {len(lines)} lines of text is read")
    print(lines)

collection.add(
    ids=[f"id_{i}" for i in range(0, len(lines))],
    documents = [line for line in lines]
)

result = collection.query(
    query_texts = ["which cat gave birth to maximum kittens ? "],
    n_results = 2
)

print(result)