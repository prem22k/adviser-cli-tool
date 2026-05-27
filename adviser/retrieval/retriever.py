"""Hybrid Chroma + BM25 retrieval for Adviser."""

from __future__ import annotations

import os
import logging

# Suppress HuggingFace hub unauthenticated warnings and raw tqdm weights-loading progress bars
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_VERBOSITY"] = "error"
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

for logger_name in ["transformers", "sentence_transformers", "chromadb", "huggingface_hub", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

import hashlib
import json
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from adviser.config import settings


class HybridRetriever:
    def __init__(self) -> None:
        self.client = None
        self.collection = None
        self.bm25: BM25Okapi | None = None
        self.documents: list[dict[str, Any]] = []
        self.stats: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        try:
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        except ImportError as exc:
            raise RuntimeError("ChromaDB and sentence-transformers must be installed to run retrieval.") from exc

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-en-v1.5",
            device="cpu",
            normalize_embeddings=True,
        )
        self.client = chromadb.PersistentClient(path=str(settings.DB_PATH))
        self.collection = self.client.get_or_create_collection(
            name="adviser",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        payload = self.collection.get(include=["documents", "metadatas"])

        ids = payload.get("ids", [])
        documents = payload.get("documents", [])
        metadatas = payload.get("metadatas", [])
        self.documents = [
            {"id": doc_id, "document": document, "metadata": metadata or {}}
            for doc_id, document, metadata in zip(ids, documents, metadatas)
            if document
        ]

        tokenized = [item["document"].lower().split() for item in self.documents]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None

        stats_path = settings.DB_PATH / "stats.json"
        if stats_path.exists():
            self.stats = json.loads(stats_path.read_text(encoding="utf-8"))
        else:
            self.stats = {
                "total_chunks": len(self.documents),
                "sources": sorted(
                    {
                        str(item["metadata"].get("source", "unknown"))
                        for item in self.documents
                    }
                ),
            }
        return self.stats

    def _vector_search(self, query: str, k: int) -> list[dict[str, Any]]:
        if self.collection is None:
            raise RuntimeError("Retriever not loaded.")
        if not self.documents:
            return []

        result = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict[str, Any]] = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for rank, (doc_id, document, metadata, distance) in enumerate(zip(ids, docs, metadatas, distances)):
            score = 1 - float(distance)
            hits.append(
                {
                    "id": doc_id or self._make_key(metadata, document),
                    "document": document,
                    "metadata": metadata or {},
                    "score": score,
                    "rank": rank,
                    "kind": "vector",
                }
            )
        return hits

    def _bm25_search(self, query: str, k: int) -> list[dict[str, Any]]:
        if self.bm25 is None:
            return []

        scores = self.bm25.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        hits: list[dict[str, Any]] = []
        for rank, (index, score) in enumerate(ranked[:k]):
            if score <= 0:
                continue
            item = self.documents[index]
            hits.append(
                {
                    "id": item["id"],
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "score": float(score),
                    "rank": rank,
                    "kind": "bm25",
                }
            )
        return hits

    def _reciprocal_rank_fusion(
        self, vector_hits: list[dict[str, Any]], bm25_hits: list[dict[str, Any]], k: int = 60
    ) -> list[dict[str, Any]]:
        fused: dict[str, dict[str, Any]] = {}
        for rank, hit in enumerate(vector_hits):
            key = str(hit["id"])
            entry = fused.setdefault(key, dict(hit))
            entry["rrf_score"] = entry.get("rrf_score", 0.0) + settings.VECTOR_WEIGHT / (k + rank + 1)
        for rank, hit in enumerate(bm25_hits):
            key = str(hit["id"])
            entry = fused.setdefault(key, dict(hit))
            entry["rrf_score"] = entry.get("rrf_score", 0.0) + settings.BM25_WEIGHT / (k + rank + 1)
        return sorted(fused.values(), key=lambda item: item.get("rrf_score", 0.0), reverse=True)

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        limit = top_k or settings.TOP_K_RETRIEVE
        vector_hits = self._vector_search(query, limit * 3)
        bm25_hits = self._bm25_search(query, limit * 3)
        return self._reciprocal_rank_fusion(vector_hits, bm25_hits)[:limit]

    @staticmethod
    def format_context(hits: list[dict[str, Any]], max_chars: int = 12000) -> str:
        blocks: list[str] = []
        used = 0
        for hit in hits:
            source = Path(str(hit["metadata"].get("source", "unknown"))).name
            chunk_idx = hit["metadata"].get("chunk_idx", "?")
            block = f"[Chunk {chunk_idx} | {source}]\n{hit['document'].strip()}"
            if used + len(block) > max_chars:
                break
            blocks.append(block)
            used += len(block) + 2
        return "\n\n".join(blocks)

    @staticmethod
    def _make_key(metadata: dict[str, Any] | None, document: str) -> str:
        metadata = metadata or {}
        source = metadata.get("source", "unknown")
        chunk_idx = metadata.get("chunk_idx", "?")
        digest = hashlib.md5(document.encode("utf-8")).hexdigest()[:12]
        return f"{source}:{chunk_idx}:{digest}"
