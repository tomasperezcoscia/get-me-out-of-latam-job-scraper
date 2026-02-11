"""Embedding generation using bge-base-en-v1.5 + pgvector storage."""

import structlog
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Job

logger = structlog.get_logger(__name__)

MODEL_NAME = "BAAI/bge-base-en-v1.5"
BATCH_SIZE = 32

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        logger.info("embeddings.loading_model", model=MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("embeddings.model_loaded", model=MODEL_NAME)
    return _model


def embed_text(text_input: str) -> list[float]:
    """Embed a single text string into a 768-dim vector."""
    model = get_model()
    # bge-base-en-v1.5 recommends prefixing queries with "Represent this sentence: "
    embedding = model.encode(text_input, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts into 768-dim vectors."""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=BATCH_SIZE)
    return embeddings.tolist()


def embed_new_jobs(db: Session, limit: int = 200) -> int:
    """Generate embeddings for jobs that don't have them yet.

    Returns:
        Number of jobs embedded.
    """
    jobs = (
        db.query(Job)
        .filter(Job.embedding.is_(None))
        .order_by(Job.scraped_at.desc())
        .limit(limit)
        .all()
    )

    if not jobs:
        logger.info("embeddings.none_needed")
        return 0

    logger.info("embeddings.generating", count=len(jobs))

    # Build text representation for each job
    texts = []
    for job in jobs:
        text_repr = f"{job.title} at {job.company}. {job.description[:1000]}"
        if job.tags:
            text_repr += f" Skills: {', '.join(job.tags)}"
        texts.append(text_repr)

    # Batch embed
    vectors = embed_batch(texts)

    # Update DB
    for job, vector in zip(jobs, vectors):
        db.execute(
            text("UPDATE jobs SET embedding = :vec WHERE id = :id"),
            {"vec": str(vector), "id": str(job.id)},
        )

    db.commit()
    logger.info("embeddings.done", embedded=len(jobs))
    return len(jobs)
