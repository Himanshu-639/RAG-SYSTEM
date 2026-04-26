from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
import ollama
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

load_dotenv()

app = FastAPI(title="RAG-SYSTEM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change this in production!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dataset = []

with open("cat-facts.txt", "r", encoding="utf-8") as file:
    dataset = file.readlines()
    print(f"Loaded cat-facts.txt with {len(dataset)}")

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'

VECTOR_DB = []

def add_chunk_to_database(chunk):
    embedding = ollama.embed(model = EMBEDDING_MODEL, input= chunk)['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))

for i, chunk in enumerate(dataset):
    add_chunk_to_database(chunk)
    print(f"Added chunk {i+1}/{len(dataset)} to database.")

def retrieve(query, top_n=3):
    query_embedding = ollama.embed(EMBEDDING_MODEL, input= query)['embeddings'][0]
    similarities = []
    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity([query_embedding], [embedding])[0][0]
        similarities.append((chunk, similarity))
    similarities.sort(key=lambda x:x[1], reverse=True)
    return similarities[:top_n]

from pydantic import BaseModel
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
async def get_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.post("/chat")
async def chat(request: QueryRequest):
    retrieved_knowledge = retrieve(request.query)
    
    url = "http://localhost:11434/api/generate"
    
    context_text = '\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])
    system_prompt = f"You are a helpful chatbot.\nUse only the following pieces of context to answer the question. Don't make up any new information:\n{context_text}"

    payload = {
        "model": "gemma4:e2b",
        "prompt": request.query,
        "system": system_prompt,
    }

    def stream_generator():
        try:
            response = requests.post(url, json=payload, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        yield data.get("response", "")
            else:
                yield f"Error: Status Code {response.status_code}"
        except Exception as e:
            yield f"Error: {e}"

    return StreamingResponse(stream_generator(), media_type="text/plain")