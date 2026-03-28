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


def get_relevant_tables(query, top_k=3):
    logger.debug(f"Finding relevant tables for query: {query[:50] + '...' if len(query) > 50 else query}")
    
    # Enhanced logic for region queries - prioritize customers over sellers
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in ['region', 'state', 'geographic', 'location', 'area']):
        # For customer-focused region queries, always include customers table
        if any(keyword in query_lower for keyword in ['customer', 'sales by', 'revenue by', 'overall']):
            # Force customers table for customer region analysis
            customer_tables = ['customers', 'order_items', 'orders']
            logger.debug(f"Customer region query detected, prioritizing: {customer_tables}")
            return customer_tables[:top_k]
        elif any(keyword in query_lower for keyword in ['seller', 'merchant']):
            # Seller-focused region queries
            seller_tables = ['sellers', 'order_items']
            logger.debug(f"Seller region query detected, prioritizing: {seller_tables}")
            return seller_tables[:top_k]
    
    # Default semantic matching for other queries
    query_embedding = model.encode([query])
    scores = cosine_similarity(query_embedding, table_embeddings)[0]

    top_indices = np.argsort(scores)[-top_k:][::-1]
    relevant_tables = [table_names[i] for i in top_indices]
    
    logger.debug(f"Found relevant tables: {relevant_tables} with scores: {[scores[i] for i in top_indices]}")
    return relevant_tables
