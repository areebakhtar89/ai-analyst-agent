from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.core.schema_metadata import SCHEMA_METADATA
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")
logger.info("Loaded sentence transformer model for table retrieval")

# Precompute table embeddings
table_texts = []
table_names = []

for table in SCHEMA_METADATA:
    text = table["table"] + " " + table["description"]
    table_texts.append(text)
    table_names.append(table["table"])

table_embeddings = model.encode(table_texts)
logger.debug(f"Precomputed embeddings for {len(table_names)} tables")


def get_relevant_tables(query, top_k=2):
    logger.debug(f"Finding relevant tables for query: {query[:50] + '...' if len(query) > 50 else query}")
    
    query_embedding = model.encode([query])
    scores = cosine_similarity(query_embedding, table_embeddings)[0]

    top_indices = np.argsort(scores)[-top_k:][::-1]
    relevant_tables = [table_names[i] for i in top_indices]
    
    logger.debug(f"Found relevant tables: {relevant_tables} with scores: {[scores[i] for i in top_indices]}")
    return relevant_tables
