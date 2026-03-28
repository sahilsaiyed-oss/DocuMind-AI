'''
import os
import time
from dotenv import load_dotenv
import structlog
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.models.schemas import QueryRequest, QueryResponse

load_dotenv()
logger = structlog.get_logger()

CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

def run_query(request: QueryRequest) -> QueryResponse:
    start_time = time.time()
    session_id = request.session_id or "default_session"

    try:
        # 1. Load Local Vector Store
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

        # 2. Retrieve
        docs = vector_db.similarity_search_with_score(request.query, k=request.top_k)
        context_text = "\n---\n".join([doc.page_content for doc, score in docs]) if docs else ""
        sources = [{"filename": d[0].metadata.get("filename"), "score": float(d[1])} for d in docs]

        # 3. Generate with STABLE model from .env
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
        )

        prompt = f"Context:\n{context_text}\n\nQuestion: {request.query}\nAnswer:"
        response = llm.invoke(prompt)
        
        latency_ms = int((time.time() - start_time) * 1000)
        return QueryResponse(
            answer=response.content,
            sources=sources,
            retrieval_score=float(docs[0][1]) if docs else 0.0,
            latency_ms=latency_ms,
            session_id=session_id
        )

    except Exception as e:
        logger.error("query_failed", error=str(e))
        return QueryResponse(answer=f"Error: {str(e)}", sources=[], retrieval_score=0, latency_ms=0, session_id=session_id)'''
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import structlog
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.models.schemas import QueryRequest, QueryResponse

load_dotenv()
logger = structlog.get_logger()

CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LOG_FILE = "query_history.json"

def save_to_history(query, answer, mode):
    log_entry = {"timestamp": datetime.now().isoformat(), "query": query, "answer": answer, "mode": mode}
    try:
        data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: data = json.load(f)
        data.append(log_entry)
        with open(LOG_FILE, "w") as f: json.dump(data, f, indent=2)
    except: pass

def run_query(request: QueryRequest) -> QueryResponse:
    start_time = time.time()
    session_id = request.session_id or "default_session"

    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

        search_kwargs = {"k": request.top_k}
        
        # BOSS: Multi-Category Filter Logic
        if request.filter_category:
            cat_list = [c.strip() for c in request.filter_category.split(",")]
            if len(cat_list) > 1:
                search_kwargs["filter"] = {"category": {"$in": cat_list}}
            else:
                search_kwargs["filter"] = {"category": cat_list[0]}

        docs = vector_db.similarity_search_with_score(request.query, **search_kwargs)

        if not docs:
            return QueryResponse(answer="I couldn't find anything in those categories, Boss.", sources=[], retrieval_score=0, latency_ms=0, session_id=session_id)

        context_text = "\n---\n".join([doc.page_content for doc, score in docs])
        sources = [{"filename": d[0].metadata.get("filename"), "score": float(d[1])} for d in docs]

        # TURBO MODE: Use 8b-instant for speed, temperature 0 for precision
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant",
            temperature=0
        )

        prompt = f"""
        Strict System: Use only the context below. 
        If asking about multiple topics, answer both clearly.
        Context: {context_text}
        Question: {request.query}
        Answer:
        """
        
        response = llm.invoke(prompt)
        answer = response.content

        save_to_history(request.query, answer, request.response_mode)

        return QueryResponse(
            answer=answer, sources=sources, retrieval_score=float(docs[0][1]),
            latency_ms=int((time.time() - start_time) * 1000), session_id=session_id
        )

    except Exception as e:
        return QueryResponse(answer=f"Error: {str(e)}", sources=[], retrieval_score=0, latency_ms=0, session_id=session_id)