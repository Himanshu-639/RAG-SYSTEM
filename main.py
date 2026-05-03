from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import requests
import json
from pydantic import BaseModel
from knowledge_base import add_to_knowledge_base, query_knowledge_base

app = FastAPI(title="RAG-SYSTEM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change this in production!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
async def get_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        return {"error": "Only .txt files are allowed"}
    
    content = await file.read()
    text = content.decode("utf-8")
    num_chunks = add_to_knowledge_base(text)
    
    return {"message": f"Successfully added {num_chunks} chunks from {file.filename} to the knowledge base"}

@app.post("/chat")
async def chat(request: QueryRequest):
    retrieved_knowledge = query_knowledge_base(request.query)
    
    url = "http://localhost:11434/api/generate"
    
    context_text = '\n'.join([f' - {chunk}' for chunk in retrieved_knowledge])
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