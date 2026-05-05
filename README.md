# Local RAG Assistant

A local, private Retrieval-Augmented Generation (RAG) assistant built with FastAPI, ChromaDB, and Ollama. This project allows users to upload text documents, storing their embeddings in a vector database, and then uses a local LLM to answer questions based entirely on the provided context.

## Current Features
- **Local LLM Inference:** Powered by Ollama (using models like Gemma, Llama 3, etc.), ensuring 100% data privacy.
- **Persistent Vector Storage:** Utilizes ChromaDB to store and retrieve document embeddings efficiently.
- **Document Ingestion:** A UI allowing users to upload custom .txt files directly into the knowledge base.
- **Real-Time Streaming:** The chat interface streams the LLM's response back to the user in real-time.

## Future Development Roadmap

### 1. Advanced RAG & Retrieval Optimization
- **Reranking (Cross-Encoder):** Mitigate the "fuzziness" of vector search by retrieving a larger pool of documents (e.g., top 20) from ChromaDB, and utilizing a Cross-Encoder to rank and extract the absolute best 5 chunks for the LLM prompt.
- **Hybrid Search:** Implement a combination of BM25 (keyword-based) search along with vector embeddings to hit the sweet spot between keyword exactness and semantic meaning.
- **RAGAS Evaluation:** Implement an evaluation pipeline using RAGAS to quantify systemic quality metrics like *Faithfulness* (reducing hallucinations) and *Answer Relevancy*.

### 2. Enhanced Document Processing
- **Semantic Chunking:** Move away from naive newline-based chunking. Implement semantic splitting (e.g., RecursiveCharacterTextSplitter) to preserve the contextual meaning of paragraphs and sentences without breaking ideas in half.
- **Multi-Format Parsing:** Integrate libraries like PyMuPDF and python-docx to support extracting text and importing data from PDFs, Word Documents, and CSVs.
- **Metadata Tagging & Filtering:** Store file names, page numbers, and custom categories as metadata in ChromaDB. This allows for precise, filtered searching (e.g., "Search only within the 'Machine Learning' category").

### 3. API & User Experience Improvements
- **Conversational Memory:** Store dialogue history to enable follow-up questions and genuine multi-turn conversations.
- **Database Management Interface:** Add API endpoints and UI controls to view what documents are currently in the database and give users the ability to purge outdated information.
- **Rich Chat UI:** Integrate Markdown parsing (like marked.js) in the frontend to properly format the LLM's text, lists, and code blocks. Add loading spinners to improve UX during file uploads and initial LLM generation.
- **Dynamic Configuration:** Provide frontend controls to easily switch the active Ollama model and tweak the System Prompt depending on the required persona or task.
