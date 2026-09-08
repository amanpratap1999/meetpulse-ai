import json
import math
import hashlib
import re
from typing import List, Tuple
import numpy as np
from sqlalchemy.orm import Session
from src.models import ActionItem, Embedding, Meeting
from src.config import settings

VECTOR_DIM = 128

def generate_local_embedding(text: str, dim: int = VECTOR_DIM) -> List[float]:
    """
    Generates a deterministic normalized dense vector for text using token n-grams and hashing.
    Provides fast, zero-dependency semantic-like vector similarity for local environments.
    """
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = cleaned.split()
    
    vec = np.zeros(dim, dtype=np.float32)
    if not tokens:
        return vec.tolist()
    
    # Uni-grams and bi-grams
    features = list(tokens)
    for i in range(len(tokens) - 1):
        features.append(f"{tokens[i]}_{tokens[i+1]}")
        
    for feat in features:
        # Generate hash index and sign
        h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 1 else -1.0
        # Weight by length/frequency
        vec[idx] += sign * (1.0 + math.log(len(feat) + 1.0))
        
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
        
    return vec.tolist()

def get_embedding(text: str) -> List[float]:
    """
    Dispatches embedding generation based on settings.
    Defaults to local normalized vector.
    """
    return generate_local_embedding(text)

def search_action_items(db: Session, query: str, top_k: int = 10) -> List[Tuple[ActionItem, float]]:
    """
    Finds action items matching the query vector via cosine similarity.
    """
    query_vec = np.array(get_embedding(query), dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []
    
    embeddings = db.query(Embedding).all()
    if not embeddings:
        return []
    
    results = []
    for emb in embeddings:
        try:
            vec = np.array(json.loads(emb.vector_json), dtype=np.float32)
            denom = np.linalg.norm(vec) * query_norm
            sim = float(np.dot(vec, query_vec) / denom) if denom > 0 else 0.0
            results.append((emb.action_item, sim))
        except Exception:
            continue
            
    # Sort descending by similarity score
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
