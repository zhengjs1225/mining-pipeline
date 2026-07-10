"""
Embedding generation using sentence-transformers with BGE-M3 model.

BGE-M3 (BAAI/bge-m3) supports:
- Multilingual (Chinese + English)
- Dense embeddings (1024-dim)
- 8192 token context window
- Good retrieval performance
"""

from typing import List

from loguru import logger

from .config import EMBEDDING_MODEL, EMBEDDING_DIM, MiningDocument


class Embedder:
    """Generate embeddings for mining documents."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(
            f"Embedding model loaded: dim={self.model.get_sentence_embedding_dimension()}"
        )

    def embed_documents(self, docs: List[MiningDocument]) -> List[List[float]]:
        """Generate embeddings for a batch of documents.

        Each document is encoded as: title + "\n" + content[:2000]
        This captures both the headline topic and key details.
        """
        if not docs:
            return []

        texts = [self._to_embedding_text(doc) for doc in docs]

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # Cosine similarity
            show_progress_bar=True,
            batch_size=32,
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    @staticmethod
    def _to_embedding_text(doc: MiningDocument) -> str:
        """Convert document to text suitable for embedding.

        Format: [SOURCE] [CATEGORY] title \n content (truncated)
        """
        # Include metadata prefix for better retrieval
        prefix = f"[{doc.source}] [{doc.category}]"
        if doc.language == "zh":
            source_names = {
                "rare_earth_cn": "中国稀土",
                "shfe": "上海期货交易所",
                "steel_union": "上海钢联",
                "mining_com": "Mining.com",
                "sp_global_mining": "S&P Global",
                "disr_au": "澳大利亚DISR",
                "lme": "LME",
            }
            prefix = f"[{source_names.get(doc.source, doc.source)}] [{doc.category}]"

        title = doc.title
        content = doc.content[:2000] if doc.content else ""

        return f"{prefix} {title}\n{content}"
