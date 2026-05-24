from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import requests
import json
from pydantic import BaseModel
import fitz
import io
import uuid
from knowledge_base import add_to_knowledge_base, query_knowledge_base
import urllib.parse

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
    doc_id = str(uuid.uuid4())

    metadata = {
        "docId": doc_id,
        "filename": file.filename,
        "filetype": file.content_type
    }
    if file.filename.endswith(".txt"):
        content = await file.read()
        text = content.decode("utf-8")
        num_chunks = add_to_knowledge_base(text, metadata=metadata)
        return {"message": f"Successfully added {num_chunks} chunks from {file.filename} to the knowledge base"}

    elif file.filename.endswith(".pdf"):
        content = await file.read()
        
        doc = fitz.open(stream=content, filetype="pdf")
        
        full_text = ""
        has_tables = False
        
        for page_num, page in enumerate(doc):
            tables = page.find_tables()
            if tables.tables:
                has_tables = True
            
            # Extract regular text blocks
            blocks = page.get_text("blocks")
            page_elements = []
            
            for b in blocks:
                x0, y0, x1, y1, text, block_no, block_type = b
                if block_type != 0:  # Skip non-text blocks
                    continue
                block_rect = fitz.Rect(x0, y0, x1, y1)
                
                # Check if block belongs to any table
                is_table_text = False
                for table in tables:
                    if block_rect.intersects(table.bbox):
                        is_table_text = True
                        break
                        
                if not is_table_text:
                    page_elements.append((y0, text))
                    
            # Extract tables natively formatting to Markdown
            for table in tables:
                page_elements.append((table.bbox[1], "\n" + table.to_markdown() + "\n"))
                
            # Sort by vertical position (y0) to maintain top-to-bottom reading order
            page_elements.sort(key=lambda x: x[0])
            
            for _, content_str in page_elements:
                full_text += content_str
                
        print("has_tables", has_tables)
        num_chunks = add_to_knowledge_base(full_text, metadata=metadata)
        return {"message": f"Successfully added {num_chunks} chunks from {file.filename} to the knowledge base"}

    else:
        return {"error": "Only .txt and .pdf files are allowed"}
    
    

@app.post("/chat")
async def chat(request: QueryRequest):
    retrieved_docs, retrieved_metadata = query_knowledge_base(request.query)
    print(retrieved_docs)
    
    url = "http://localhost:11434/api/generate"
    
    context_text = '\n'.join([f' - {chunk}' for chunk in retrieved_docs])
    system_prompt = f"You are a helpful chatbot.\nUse only the following pieces of context to answer the question. Don't make up any new information:\n{context_text}"

    payload = {
        "model": "gemma4:e2b",
        "prompt": request.query,
        "system": system_prompt,
    }

    sources = []
    for doc, meta in zip(retrieved_docs, retrieved_metadata):
        sources.append({
            "filename": meta.get("filename", "Unknown"),
            "chunk_index": meta.get("chunk_index", "Unknown"),
            "content": doc
        })

    sources_json = urllib.parse.quote(json.dumps(sources))


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

    return StreamingResponse(
        stream_generator(), 
        media_type="text/plain",
        headers={"X-Sources": sources_json, "Access-Control-Expose-Headers": "X-Sources"}
    )