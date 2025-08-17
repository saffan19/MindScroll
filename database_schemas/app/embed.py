from sentence_transformers import SentenceTransformer
from functools import lru_cache

@lru_cache(maxsize=1)
def get_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    return SentenceTransformer(model_name)

def embed_text(text: str, model_name: str) -> list:
    model = get_model(model_name)
    vec = model.encode(text or "", normalize_embeddings=True)
    return vec.tolist()
