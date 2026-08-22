"""Document loader and vector store for ParcelPilot policy documents.

Loads markdown documents, chunks them with metadata (source type, status,
account_id, freshness), and indexes into ChromaDB with Gemini embeddings.
"""

import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR, GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, CHROMA_COLLECTION
from app.auth.models import UserContext, UserRole

# ---------------------------------------------------------------------------
# Document metadata registry
# ---------------------------------------------------------------------------
DOCUMENT_REGISTRY = {
    "01_Support_Policy_v3_CURRENT.md": {
        "title": "ParcelPilot Support Policy v3",
        "doc_type": "policy",
        "status": "CURRENT",
        "effective_date": "2026-05-01",
        "reliability_tier": 2,  # 1=highest (agreement), 2=current policy, 3=ops guide, 4=historical
        "account_id": None,  # General - all accounts
        "internal_only": False,
    },
    "02_Support_Policy_v2_DEPRECATED.md": {
        "title": "ParcelPilot Support Policy v2 (DEPRECATED)",
        "doc_type": "policy",
        "status": "DEPRECATED",
        "effective_date": "2025-01-01",
        "reliability_tier": 5,  # Deprecated - lowest
        "account_id": None,
        "internal_only": False,
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.md": {
        "title": "Cancellation & Service Credit SOP v4",
        "doc_type": "sop",
        "status": "CURRENT",
        "effective_date": "2026-06-15",
        "reliability_tier": 2,
        "account_id": None,
        "internal_only": False,
    },
    "04_Product_Operations_Guide_and_Known_Issues.md": {
        "title": "Product Operations Guide & Known Issues",
        "doc_type": "ops_guide",
        "status": "CURRENT",
        "effective_date": "2026-08-14",
        "reliability_tier": 3,
        "account_id": None,
        "internal_only": True,  # Known issues are internal
    },
    "05_Northstar_Logistics_Enterprise_Agreement.md": {
        "title": "Northstar Logistics Enterprise Agreement",
        "doc_type": "agreement",
        "status": "CURRENT",
        "effective_date": "2026-01-01",
        "reliability_tier": 1,  # Highest - signed agreement
        "account_id": "ACCT-001",
        "internal_only": False,
    },
    "06_LumenWorks_Service_Agreement.md": {
        "title": "LumenWorks Service Agreement",
        "doc_type": "agreement",
        "status": "CURRENT",
        "effective_date": "2026-03-01",
        "reliability_tier": 1,
        "account_id": "ACCT-002",
        "internal_only": False,
    },
}


# ---------------------------------------------------------------------------
# Vector store setup
# ---------------------------------------------------------------------------
_chroma_client: Optional[chromadb.Client] = None
_collection: Optional[chromadb.Collection] = None
_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Get or create Gemini embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBEDDING_MODEL,
            google_api_key=GEMINI_API_KEY,
        )
    return _embeddings


def get_chroma_collection() -> chromadb.Collection:
    """Get or create the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
        # Delete existing collection if any (for clean re-index)
        try:
            _chroma_client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass
        _collection = _chroma_client.create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def load_and_index_documents():
    """Load all documents, chunk them, and index into ChromaDB."""
    collection = get_chroma_collection()
    embeddings = get_embeddings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n- ", "\n● ", "\n\n", "\n", ". ", " "],
    )

    all_texts = []
    all_metadatas = []
    all_ids = []

    for filename, meta in DOCUMENT_REGISTRY.items():
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found, skipping.")
            continue

        content = filepath.read_text(encoding="utf-8")
        chunks = splitter.split_text(content)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}::chunk_{i}"
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_metadatas.append({
                "filename": filename,
                "title": meta["title"],
                "doc_type": meta["doc_type"],
                "status": meta["status"],
                "effective_date": meta["effective_date"],
                "reliability_tier": meta["reliability_tier"],
                "account_id": meta["account_id"] or "general",
                "internal_only": str(meta["internal_only"]),
                "chunk_index": i,
            })

    # Embed and add to collection
    if all_texts:
        embedded = embeddings.embed_documents(all_texts)
        collection.add(
            ids=all_ids,
            embeddings=embedded,
            documents=all_texts,
            metadatas=all_metadatas,
        )
        print(f"Indexed {len(all_texts)} chunks from {len(DOCUMENT_REGISTRY)} documents.")


def search_documents(
    query: str,
    user: UserContext,
    top_k: int = 5,
    doc_type: Optional[str] = None,
) -> list[dict]:
    """Search documents with access control.

    Access rules:
    - Customers can see: general policies/SOPs + their own agreement
    - Customers CANNOT see: other customers' agreements, internal-only docs
    - Internal staff can see everything
    """
    collection = get_chroma_collection()
    embeddings = get_embeddings()

    query_embedding = embeddings.embed_query(query)

    # Build where filter for access control
    where_clauses = []

    if user.role == UserRole.CUSTOMER:
        # Customers: only general docs + their own agreement, exclude internal-only
        where_clauses.append({"internal_only": "False"})
        where_clauses.append({
            "$or": [
                {"account_id": "general"},
                {"account_id": user.account_id or "none"},
            ]
        })

    if doc_type:
        where_clauses.append({"doc_type": doc_type})

    # Exclude DEPRECATED docs by default (internal can still access if needed)
    if user.role == UserRole.CUSTOMER:
        where_clauses.append({"status": "CURRENT"})

    # Combine where clauses
    where_filter = None
    if len(where_clauses) == 1:
        where_filter = where_clauses[0]
    elif len(where_clauses) > 1:
        where_filter = {"$and": where_clauses}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"],
    )

    # Format results with reliability info
    formatted = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        formatted.append({
            "content": results["documents"][0][i],
            "source": meta["title"],
            "filename": meta["filename"],
            "doc_type": meta["doc_type"],
            "status": meta["status"],
            "reliability_tier": meta["reliability_tier"],
            "account_id": meta["account_id"],
            "effective_date": meta["effective_date"],
            "relevance_score": round(1 - results["distances"][0][i], 4),
        })

    # Sort by reliability tier (lower = more authoritative), then relevance
    formatted.sort(key=lambda x: (x["reliability_tier"], -x["relevance_score"]))

    return formatted
