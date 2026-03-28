'''

"""
FastAPI route definitions.
Exposes /ingest, /chat, /history, /metrics, and /health endpoints.
"""
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import shutil
import tempfile
import structlog

from app.ingestion.pipeline import ingest_document
from app.retrieval.rag_agent import run_query
from app.retrieval.memory import (
    create_session,
    get_history,
    delete_session,
    get_session_stats,
)
from app.metrics.tracker import get_metrics_summary
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
)

logger = structlog.get_logger()
router = APIRouter()


# ─── Health Check ────────────────────────────────────────────
@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Knowledge Base Agent",
        "version": "1.0.0",
    }


# ─── Ingest: File Upload ──────────────────────────────────────
@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
):
    """
    Upload and ingest a document file (PDF, DOCX, TXT).
    Chunks, embeds, and stores in Pinecone automatically.
    """
    allowed_types = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX, TXT",
        )

    # Save to temp file for processing
    suffix = allowed_types[file.content_type]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_document(source=tmp_path, category=category)
        # Use original filename in response
        result.filename = file.filename
        logger.info("file_ingested", filename=file.filename, chunks=result.chunks_created)
        return result
    except Exception as e:
        logger.error("file_ingest_failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


# ─── Ingest: URL ──────────────────────────────────────────────
@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: IngestRequest):
    """
    Ingest content from a public URL.
    Scrapes, chunks, embeds, and stores automatically.
    """
    try:
        result = ingest_document(
            source=request.url,
            category=request.category or "general",
        )
        logger.info("url_ingested", url=request.url, chunks=result.chunks_created)
        return result
    except Exception as e:
        logger.error("url_ingest_failed", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── Chat ─────────────────────────────────────────────────────
@router.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    """
    Submit a question to the RAG knowledge base.
    Returns a grounded answer with sources and metrics.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        response = run_query(request)
        return response
    except Exception as e:
        logger.error("chat_failed", query=request.query[:60], error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── Session: New ─────────────────────────────────────────────
@router.post("/session/new")
async def new_session():
    """Create a new conversation session."""
    session_id = create_session()
    return {"session_id": session_id}


# ─── Session: History ─────────────────────────────────────────
@router.get("/session/{session_id}/history")
async def session_history(session_id: str):
    """Retrieve conversation history for a session."""
    history = get_history(session_id)
    stats = get_session_stats(session_id)

    if stats is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return {
        "session_id": session_id,
        "turn_count": stats["turn_count"],
        "messages": history,
    }


# ─── Session: Delete ──────────────────────────────────────────
@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """Delete a session and clear its history."""
    deleted = delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


# ─── Metrics ──────────────────────────────────────────────────
@router.get("/metrics")
async def metrics():
    """Return system performance metrics."""
    stats = get_metrics_summary()
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")
    return stats



@router.post("/ingest/folder")
async def ingest_folder_api(folder_path: str, category: str = "general"):
    """Train AI on an entire folder of documents"""
    from app.ingestion.pipeline import ingest_folder
    result = ingest_folder(folder_path, category)
    return result
    '''
'''
import os
import shutil
import tempfile
import structlog
import json
import re  # New import for smart extraction
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import Optional, Union
from datetime import datetime

from app.ingestion.pipeline import ingest_document, ingest_folder
from app.retrieval.rag_agent import run_query
from app.models.schemas import QueryRequest, QueryResponse, IngestRequest, IngestResponse
from app.metrics.tracker import get_metrics_summary
from app.retrieval.memory import create_session

logger = structlog.get_logger()
router = APIRouter()

@router.post("/chat", response_model=QueryResponse)
async def chat(request: Request):
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8").strip()
        
        query_text = body_str
        extracted_category = None
        response_mode = "detailed"
        top_k = 3

        # ─── STEP 1: Check if input is JSON or RAW TEXT ───
        try:
            body_json = json.loads(body_str)
            if isinstance(body_json, dict):
                # If full JSON, use it as is
                query_data = QueryRequest(**body_json)
                return run_query(query_data)
            elif isinstance(body_json, str):
                query_text = body_json
        except json.JSONDecodeError:
            pass # Keep it as raw text

        # ─── STEP 2: BOSS FEATURE - Extract Category from Quotes ───
        # Example: What is the dose? "diabetes" -> category="diabetes"
        match = re.search(r'\"([^\"]+)\"', query_text)
        if match:
            extracted_category = match.group(1) # Get text inside quotes
            # Remove the quoted part from the query so AI doesn't get confused
            query_text = query_text.replace(f'"{extracted_category}"', "").strip()
            logger.info("smart_filter_detected", category=extracted_category, query=query_text)

        # ─── STEP 3: Create Query Object ───
        query_obj = QueryRequest(
            query=query_text,
            top_k=top_k,
            response_mode=response_mode,
            filter_category=extracted_category # Now it's smart!
        )

        if not query_obj.query.strip():
            raise HTTPException(status_code=400, detail="Query empty")

        response = run_query(query_obj)
        return response

    except Exception as e:
        logger.error("chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Boss, error: {str(e)}")

# ... baaki endpoints (ingest_folder, ingest_file) wahi purane rahenge ...
# (Unhe mat chedna, wo sahi chal rahe hain)

# ─── Ingest: Folder ──────────────────────────────────────────
@router.post("/ingest/folder")
async def ingest_folder_api(folder_path: str, category: str = "general"):
    try:
        result = ingest_folder(folder_path, category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Ingest: File Upload ──────────────────────────────────────
@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...), category: str = Form(default="general")):
    allowed_types = {"application/pdf": ".pdf", "text/plain": ".txt"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    suffix = allowed_types[file.content_type]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        doc_id = ingest_document(source_type="file", source_path=tmp_path, category=category)
        return IngestResponse(
            document_id=doc_id, filename=file.filename, chunks_created=0,
            status="success", ingested_at=datetime.now().isoformat()
        )
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)

# ─── URL Ingest ──────────────────────────────────────────────
@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: IngestRequest):
    doc_id = ingest_document(source_type="url", source_path=request.url, category=request.category)
    return IngestResponse(
        document_id=doc_id, filename=request.url, chunks_created=0,
        status="success", ingested_at=datetime.now().isoformat()
    )

# ─── Session & Metrics ──────────────────────────────────────
@router.get("/metrics")
async def metrics(): return get_metrics_summary()

@router.post("/session/new")
async def new_session(): return {"session_id": create_session()}'''

'''
import os
import shutil
import tempfile
import structlog
import json
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Body
from typing import Optional, Any, List
from datetime import datetime
from collections import Counter

# Important Imports for Database
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.ingestion.pipeline import ingest_document, ingest_folder
from app.retrieval.rag_agent import run_query
from app.models.schemas import QueryRequest, QueryResponse, IngestRequest, IngestResponse
from app.metrics.tracker import get_metrics_summary
from app.retrieval.memory import create_session

logger = structlog.get_logger()
router = APIRouter()

# Global Constants
CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ─── 1. CHAT ENDPOINT (BOSS MODE) ──────────────────────────
@router.post("/chat", response_model=QueryResponse)
async def chat(user_input: str = Body(..., media_type="text/plain", example='Explain the system "cab_sharing"')):
    """Accepts raw text or JSON. Use "category" in quotes to filter."""
    try:
        query_raw = user_input.strip()
        if not query_raw:
            raise HTTPException(status_code=400, detail="Sawal toh likho Boss!")

        # Catch all categories in quotes
        all_categories = re.findall(r'\"([^\"]+)(?:\"|$)', query_raw)
        
        query_text = query_raw
        for cat in all_categories:
            query_text = query_text.replace(f'"{cat}"', "").replace(f'"{cat}', "")
        
        query_text = query_text.replace('"', '').strip()
        filter_str = ",".join(all_categories) if all_categories else None

        query_obj = QueryRequest(
            query=query_text,
            top_k=5,
            response_mode="detailed",
            filter_category=filter_str
        )
        return run_query(query_obj)
    except Exception as e:
        logger.error("chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ─── 2. INGEST FOLDER ──────────────────────────────────────
@router.post("/ingest/folder")
async def ingest_folder_api(folder_path: str, category: str = "general"):
    """Ingest an entire folder of documents."""
    return ingest_folder(folder_path, category)

# ─── 3. INGEST FILE ────────────────────────────────────────
@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...), category: str = Form(default="general")):
    """Upload and ingest a single PDF/TXT file."""
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        res = ingest_document("file", tmp_path, category)
        return IngestResponse(
            document_id=res["document_id"], 
            filename=file.filename, 
            chunks_created=res["chunks_count"], 
            status="success", 
            ingested_at=datetime.now().isoformat()
        )
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)

# ─── 4. LIST DOCUMENTS ─────────────────────────────────────
@router.get("/documents/list")
async def list_ingested_documents():
    """Boss Feature: See what's inside the database."""
    if not os.path.exists(CHROMA_PATH):
        return {"message": "Database khali hai Boss!"}
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        data = vector_db.get()
        metadatas = data.get('metadatas', [])
        if not metadatas: return {"message": "No files found."}
        
        files_info = {}
        for m in metadatas:
            fname = m.get('filename', 'Unknown')
            cat = m.get('category', 'general')
            files_info[fname] = cat
            
        result = [{"file": f, "category": c} for f, c in files_info.items()]
        return {"total_unique_files": len(result), "documents": result}
    except Exception as e:
        return {"error": str(e)}

# ─── 5. ANALYTICS SUMMARY ──────────────────────────────────
@router.get("/analytics/summary")
async def get_analytics_summary():
    """Boss Feature: AI Performance Analytics."""
    HISTORY_FILE = "query_history.json"
    if not os.path.exists(HISTORY_FILE):
        return {"message": "Abhi tak koi chat nahi hui hai Boss!"}
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        
        categories_used = []
        for item in history:
            q = item.get("query", "").lower()
            if "cab" in q: categories_used.append("cab_sharing")
            elif "diabetes" in q or "metformin" in q: categories_used.append("diabetes")
            else: categories_used.append("general")

        return {
            "total_questions_handled": len(history),
            "popular_categories": dict(Counter(categories_used)),
            "system_health": "Running Like a Beast! 🦾",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"Analytics fail: {str(e)}"}

# ─── 6. HEALTH CHECK ───────────────────────────────────────
@router.get("/health")
async def health_check():
    return {"status": "healthy", "project": "IntelliDocs AI", "version": "1.5.0"}


# 1. Folder ki Details dekhne ke liye (Files + Chunks)
@router.get("/documents/category/{category_name}")
async def get_category_details(category_name: str):
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        
        # Database se data nikalo
        data = vector_db.get(where={"category": category_name})
        metadatas = data.get('metadatas', [])
        
        if not metadatas:
            return {"message": "Category not found"}

        file_stats = {}
        for m in metadatas:
            fname = m.get('filename', 'Unknown')
            file_stats[fname] = file_stats.get(fname, 0) + 1 # Chunks count kar raha hai

        result = [{"filename": f.split('\\')[-1], "chunks": c} for f, c in file_stats.items()]
        return {
            "category": category_name,
            "total_files": len(result),
            "files": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Folder ko Rename karne ke liye
@router.post("/documents/rename-category")
async def rename_category(old_name: str, new_name: str):
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        
        # Purane data ko pakdo
        data = vector_db.get(where={"category": old_name})
        ids = data.get('ids', [])
        
        if not ids:
            return {"error": "Old category not found"}

        # Metadata update karo
        for i in range(len(ids)):
            vector_db._collection.update(
                ids=[ids[i]],
                metadatas=[{**data['metadatas'][i], "category": new_name}]
            )
            
        return {"status": "success", "message": f"Renamed {old_name} to {new_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''


import os
import shutil
import tempfile
import structlog
import json
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Body
from typing import Optional, Any, List
from datetime import datetime
from collections import Counter

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.ingestion.pipeline import ingest_document, ingest_folder
from app.retrieval.rag_agent import run_query
from app.models.schemas import QueryRequest, QueryResponse, IngestRequest, IngestResponse

logger = structlog.get_logger()
router = APIRouter()

CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ─── 1. SMART CHAT ──────────────────────────────────────────
@router.post("/chat", response_model=QueryResponse)
async def chat(user_input: str = Body(..., media_type="text/plain")):
    try:
        query_raw = user_input.strip()
        all_categories = re.findall(r'\"([^\"]+)(?:\"|$)', query_raw)
        query_text = query_raw
        for cat in all_categories:
            query_text = query_text.replace(f'"{cat}"', "").replace(f'"{cat}', "")
        query_text = query_text.replace('"', '').strip()

        query_obj = QueryRequest(
            query=query_text,
            top_k=5,
            response_mode="detailed",
            filter_category=all_categories[0] if all_categories else None
        )
        return run_query(query_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 2. LIST ALL CATEGORIES & DOCUMENTS ──────────────────────
@router.get("/documents/list")
async def list_documents():
    if not os.path.exists(CHROMA_PATH): return {"documents": []}
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    data = vector_db.get()
    metadatas = data.get('metadatas', [])
    files_info = {}
    for m in metadatas:
        fname = m.get('filename', 'Unknown').split('\\')[-1].split('/')[-1]
        cat = m.get('category', 'general')
        if cat not in files_info: files_info[cat] = []
        if fname not in files_info[cat]: files_info[cat].append(fname)
    
    return {"categories": [{"name": k, "files": v, "count": len(v)} for k, v in files_info.items()]}

# ─── 3. RENAME CATEGORY ──────────────────────────────────────
@router.post("/documents/rename")
async def rename_category(old_name: str, new_name: str):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    data = vector_db.get(where={"category": old_name})
    ids = data.get('ids', [])
    if not ids: raise HTTPException(status_code=404, detail="Category not found")
    for i in range(len(ids)):
        new_meta = data['metadatas'][i]
        new_meta['category'] = new_name
        vector_db._collection.update(ids=[ids[i]], metadatas=[new_meta])
    return {"status": "success"}

# ─── 4. DELETE CATEGORY ──────────────────────────────────────
@router.delete("/documents/category/{name}")
async def delete_category(name: str):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    vector_db._collection.delete(where={"category": name})
    return {"status": "deleted"}

# ─── 5. INGEST FOLDER / FILE (STABLE) ────────────────────────
@router.post("/ingest/folder")
async def ingest_folder_api(folder_path: str, category: str = "general"):
    return ingest_folder(folder_path, category)

@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...), category: str = Form(default="general")):
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        from app.ingestion.pipeline import ingest_document
        res = ingest_document("file", tmp_path, category)
        from datetime import datetime
        return IngestResponse(document_id=res["document_id"], filename=file.filename, chunks_created=res["chunks_count"], status="success", ingested_at=datetime.now().isoformat())
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)

@router.get("/analytics/summary")
async def get_analytics():
    import json
    if not os.path.exists("query_history.json"): return {"total_questions_handled": 0}
    with open("query_history.json", "r") as f: history = json.load(f)
    return {"total_questions_handled": len(history)}

@router.get("/health")
async def health(): return {"status": "ok"}