
import os
import re
import uuid
from functools import lru_cache

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models


COLLECTION = os.getenv("QDRANT_COLLECTION", "datanexus_documents")
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


@lru_cache(maxsize=1)
def get_qdrant() -> QdrantClient:
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://qdrant:6333")
    )


@lru_cache(maxsize=1)
def get_embedder() -> TextEmbedding:
    return TextEmbedding(model_name=EMBEDDING_MODEL)


def ensure_collection() -> None:
    client = get_qdrant()

    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )


def split_text(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def ingest_document(title: str, text: str) -> int:
    chunks = split_text(text)

    if not chunks:
        raise ValueError("Document text cannot be empty.")

    ensure_collection()

    vectors = list(get_embedder().embed(chunks))
    points = []

    for chunk, vector in zip(chunks, vectors):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={
                    "title": title,
                    "text": chunk,
                    "source": title,
                },
            )
        )

    get_qdrant().upsert(
        collection_name=COLLECTION,
        points=points,
        wait=True,
    )

    return len(points)



def retrieve_documents(question: str, top_k: int = 4) -> list[dict]:
    ensure_collection()

    query_vector = list(get_embedder().embed([question]))[0].tolist()

    response = get_qdrant().query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    results = []
    for hit in response.points:
        payload = hit.payload or {}
        results.append({
            "title": payload.get("title", "Unknown"),
            "text": payload.get("text", ""),
            "score": hit.score,
        })

    return results
