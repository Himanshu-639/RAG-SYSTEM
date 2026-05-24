# RAG System Architecture

This document describes the flow of information from file ingestion to the final AI-generated response.

## 1. Document Ingestion Flow (File Input)

```mermaid
graph TD
    A[User Uploads File .txt/.pdf] --> B{FastAPI /upload}
    B --> C[File Content Extraction]
    C --> D[Metadata Preparation]
    D --> E[chunk_size: 500, overlap: 60]
    E --> F[Vectorization - Ollama Embeddings]
    F --> G[(ChromaDB)]
    
    subgraph "Metadata Included"
    D -.-> D1[Source Filename]
    D -.-> D2[Page Number]
    D -.-> D3[Document Type]
    end
```

### Process Details:
- **Extraction:** PDF parsing handles text blocks and native markdown tables for high-fidelity context.
- **Chunking:** `RecursiveCharacterTextSplitter` ensures logical breaks (paragraphs, then sentences).
- **Storage:** Chunks are stored with unique UUIDs and metadata for targeted filtering.

---

## 2. Retrieval & Generation Flow (Query Output)

```mermaid
graph LR
    User[User Query] --> API{FastAPI /chat}
    API --> KB[knowledge_base.py]
    KB --> VectorSearch[Semantic Search in ChromaDB]
    VectorSearch --> Context[Retrieved Context Chunks]
    Context --> Prompt[System Prompt Construction]
    Prompt --> LLM[Ollama: Gemma 2b]
    LLM --> Stream[Streaming Response]
    Stream --> UI[Markdown Rendering in Browser]
```

### Process Details:
- **Retrieval:** The system fetches the top `N` most relevant chunks based on vector similarity.
- **Augmentation:** The retrieved text is injected into a "System Prompt" to ground the LLM in specific facts.
- **Generation:** The response is streamed token-by-token to ensure low perceived latency.
- **Rendering:** `marked.js` converts the LLM's raw markdown output into rich HTML (bolding, lists, code blocks).

---

## 3. Tech Stack
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Marked.js
- **Backend:** FastAPI (Python 3.13)
- **Vector Database:** ChromaDB
- **Embedding Model:** BGE-Base-en-v1.5 (Local via Ollama)
- **LLM:** Gemma 2b (Local via Ollama)
- **PDF Intelligence:** PyMuPDF (fitz)
