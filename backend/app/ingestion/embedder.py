'''import os
from typing import List
import structlog
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.models.schemas import DocumentChunk

logger = structlog.get_logger()

# Free local embedding model (No API Key needed)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PATH = "chroma_db"

def embed_and_store(chunks: List[DocumentChunk]) -> int:
    """
    Generate embeddings locally and store in ChromaDB.
    """
    if not chunks:
        logger.warning("no_chunks_to_embed")
        return 0

    try:
        # 1. Initialize local embeddings
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

        # 2. Prepare data for Chroma
        texts = [c.content for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "source_type": c.source_type,
                "source_url": c.source_url or "",
                "chunk_index": c.chunk_index,
                "content": c.content[:500] # for preview
            }
            for c in chunks
        ]
        ids = [c.chunk_id for c in chunks]

        # 3. Store in local ChromaDB folder
        vector_db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            ids=ids,
            persist_directory=CHROMA_PATH
        )
        
        logger.info("chroma_storage_success", count=len(chunks))
        return len(chunks)

    except Exception as e:
        logger.error("embedding_and_storage_failed", error=str(e))
        return 0
    '''

import os
from typing import List
import structlog
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.models.schemas import DocumentChunk

logger = structlog.get_logger()

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PATH = "chroma_db"

def embed_and_store(chunks: List[DocumentChunk]) -> int:
    if not chunks:
        return 0
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        texts = [c.content for c in chunks]
        
        # BOSS: Added 'category' here so it actually gets saved!
        metadatas = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "source_type": c.source_type,
                "category": c.metadata.get("category", "general"), # FIXED
                "chunk_index": c.chunk_index
            }
            for c in chunks
        ]
        ids = [c.chunk_id for c in chunks]

        vector_db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            ids=ids,
            persist_directory=CHROMA_PATH
        )
        return len(chunks)
    except Exception as e:
        logger.error("embedding_failed", error=str(e))
        return 0