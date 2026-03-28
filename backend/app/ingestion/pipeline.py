'''

"""
Main ingestion pipeline.
Orchestrates: load → chunk → embed → store (Pinecone + Supabase).
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import structlog

from app.ingestion.loaders import load_document
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_and_store
from app.models.schemas import IngestResponse

load_dotenv()
logger = structlog.get_logger()


def ingest_document(source: str, category: str = "general") -> IngestResponse:
    """
    Full ingestion pipeline for a single document or URL.
    
    Args:
        source: File path or URL
        category: Optional category tag for filtering
    
    Returns:
        IngestResponse with stats
    """
    document_id = str(uuid.uuid4())
    filename = Path(source).name if not source.startswith("http") else source

    logger.info("ingestion_started", source=source, document_id=document_id)

    # Step 1: Load document
    text, source_type, metadata = load_document(source)
    metadata["category"] = category

    if not text.strip():
        raise ValueError(f"No text extracted from: {source}")

    # Step 2: Chunk text
    chunks = chunk_text(
        text=text,
        filename=filename,
        source_type=source_type,
        document_id=document_id,
        source_url=source if source_type == "url" else None,
        metadata=metadata,
    )

    if not chunks:
        raise ValueError(f"No chunks created from: {source}")

    # Step 3: Embed and store in Pinecone
    stored_count = embed_and_store(chunks)

    # Step 4: Log to Supabase
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )
        supabase.table("documents").insert({
            "id": document_id,
            "filename": filename,
            "source_type": source_type,
            "source_url": source if source_type == "url" else None,
            "chunk_count": stored_count,
            "ingested_at": datetime.now().isoformat(),
            "metadata": metadata,
        }).execute()

        logger.info("supabase_logged", document_id=document_id)

    except Exception as e:
        logger.error("supabase_log_failed", error=str(e))
        # Don't fail the whole pipeline if logging fails

    logger.info(
        "ingestion_complete",
        document_id=document_id,
        chunks=stored_count,
        source_type=source_type,
    )

    return IngestResponse(
        document_id=document_id,
        filename=filename,
        chunks_created=stored_count,
        status="success",
    )


if __name__ == "__main__":
    """Quick test — ingest a sample URL."""
    result = ingest_document(
        source="https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
        category="test"
    )
    print(f"\nIngestion Result:")
    print(f"  Document ID : {result.document_id}")
    print(f"  Filename    : {result.filename}")
    print(f"  Chunks      : {result.chunks_created}")
    print(f"  Status      : {result.status}")'''



import os
import uuid
import structlog
from app.ingestion.loaders import load_url, load_file
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_and_store

logger = structlog.get_logger()

def ingest_document(source_type: str, source_path: str, category: str = "general") -> dict:
    """ASLI LOGIC: Ingests and returns both ID and Chunk count"""
    doc_id = str(uuid.uuid4())
    # Safai: Category se extra space hatao
    clean_cat = category.strip()
    
    logger.info("ingestion_started", document_id=doc_id, source=source_path, category=clean_cat)

    try:
        # 1. Load data
        if source_type == "url":
            text = load_url(source_path)
        else:
            text = load_file(source_path)

        # 2. Chunking (Category pass karna zaroori hai)
        chunks = chunk_text(text, doc_id, source_path, source_type, clean_cat)
        
        # 3. Embedding and Storage
        count = embed_and_store(chunks)
        
        logger.info("ingestion_complete", chunks=count, document_id=doc_id)
        return {"document_id": doc_id, "chunks_count": count}
        
    except Exception as e:
        logger.error("ingestion_failed", error=str(e))
        raise e

def ingest_folder(folder_path: str, category: str = "general") -> dict:
    """Poore folder ko ingest karne ka power"""
    clean_path = folder_path.strip().strip('"').strip("'")
    if not os.path.exists(clean_path):
        return {"error": f"Path nahi mila: {clean_path}"}

    files = [f for f in os.listdir(clean_path) if f.endswith(('.pdf', '.docx', '.txt'))]
    results = []
    total_chunks = 0

    for filename in files:
        file_path = os.path.join(clean_path, filename)
        try:
            res = ingest_document("file", file_path, category)
            total_chunks += res["chunks_count"]
            results.append({"file": filename, "status": "success", "chunks": res["chunks_count"]})
        except Exception as e:
            results.append({"file": filename, "status": "failed", "error": str(e)})

    return {"total_files": len(files), "total_chunks_created": total_chunks, "details": results}