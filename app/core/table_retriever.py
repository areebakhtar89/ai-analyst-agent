from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.core.schema_metadata import SCHEMA_METADATA

model = SentenceTransformer("all-MiniLM-L6-v2")

# Precompute table embeddings
table_texts = []
table_names = []

for table in SCHEMA_METADATA:
    text = table["table"] + " " + table["description"]
    table_texts.append(text)
    table_names.append(table["table"])

table_embeddings = model.encode(table_texts)


def get_relevant_tables(query, top_k=2):
    query_embedding = model.encode([query])
    scores = cosine_similarity(query_embedding, table_embeddings)[0]

    top_indices = np.argsort(scores)[-top_k:][::-1]
    return [table_names[i] for i in top_indices]
