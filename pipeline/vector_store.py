"""
ChromaDB vector store for mining documents.

Stores embeddings + metadata for semantic search.
Collection: mining_docs
"""

import json
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings
from loguru import logger

from .config import CHROMA_DIR, CHROMA_COLLECTION, EMBEDDING_DIM, MiningDocument


class VectorStore:
    """ChromaDB-backed vector store for mining documents."""

    def __init__(self, collection_name: str = CHROMA_COLLECTION):
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(
                f"Opened existing collection '{collection_name}': "
                f"{self.collection.count()} documents"
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Created new collection '{collection_name}'")

    def add_documents(
        self,
        docs: List[MiningDocument],
        embeddings: List[List[float]],
    ) -> int:
        """Add documents with embeddings to the vector store.

        Uses upsert semantics: if id exists, update metadata/embedding.
        Returns number of documents added.
        """
        if not docs:
            return 0

        ids = [doc.id for doc in docs]
        documents = [doc.content for doc in docs]
        metadatas = [
            {
                "source": doc.source,
                "category": doc.category,
                "title": doc.title,
                "url": doc.url,
                "language": doc.language,
                "published_at": doc.published_at or "",
                "minerals": json.dumps(
                    doc.metadata.get("minerals_mentioned", [])
                ),
                "policy_types": json.dumps(
                    doc.metadata.get("policy_types", [])
                ),
                "ingested_at": doc.ingested_at or "",
            }
            for doc in docs
        ]

        # ChromaDB upsert
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Vector store: upserted {len(docs)} documents")
        return len(docs)

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_doc: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search the vector store.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            where: Metadata filter (e.g., {"category": "policy"})
            where_doc: Document content filter

        Returns:
            List of {id, content, metadata, distance}
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_doc=where_doc,
            include=["documents", "metadatas", "distances"],
        )

        # Flatten results (ChromaDB returns lists of lists)
        docs = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                docs.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                )

        return docs

    def count(self) -> int:
        """Number of documents in the store."""
        return self.collection.count()

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get all documents from a specific source."""
        results = self.collection.get(
            where={"source": source},
            include=["documents", "metadatas"],
        )
        return [
            {
                "id": results["ids"][i],
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
            }
            for i in range(len(results["ids"]))
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        total = self.count()
        if total == 0:
            return {"total": 0, "by_source": {}, "by_category": {}}

        all_data = self.collection.get(include=["metadatas"])

        by_source = {}
        by_category = {}
        for meta in all_data["metadatas"]:
            src = meta.get("source", "unknown")
            cat = meta.get("category", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total": total,
            "by_source": by_source,
            "by_category": by_category,
        }
