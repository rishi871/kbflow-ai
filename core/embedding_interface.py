from openai import OpenAI as OpenAIClient # Renamed to avoid conflict if we use 'OpenAI' class locally
from sentence_transformers import SentenceTransformer
from core.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL_DEFAULT_OPENAI,
    EMBEDDING_PROVIDER_DEFAULT, SENTENCE_TRANSFORMER_MODEL_DEFAULT,
    EMBEDDING_MODEL_ACTIVE # This will be set based on provider choice in config
)
import numpy as np

openai_embed_client = None
if OPENAI_API_KEY and EMBEDDING_PROVIDER_DEFAULT == "openai":
    openai_embed_client = OpenAIClient(api_key=OPENAI_API_KEY)
    print(f"OpenAI client initialized for embeddings with model: {EMBEDDING_MODEL_ACTIVE}")

st_model = None
if EMBEDDING_PROVIDER_DEFAULT == "sentence_transformers":
    try:
        st_model = SentenceTransformer(EMBEDDING_MODEL_ACTIVE) # EMBEDDING_MODEL_ACTIVE will be SENTENCE_TRANSFORMER_MODEL_DEFAULT
        print(f"SentenceTransformer model '{EMBEDDING_MODEL_ACTIVE}' loaded for embeddings.")
    except Exception as e:
        print(f"Warning: Could not load SentenceTransformer model '{EMBEDDING_MODEL_ACTIVE}': {e}")
        print("Embeddings will be mocked if SentenceTransformer model fails to load.")

def get_embedding(text: str, model: str = None) -> list[float]:
    active_embedding_model = model if model else EMBEDDING_MODEL_ACTIVE

    if not active_embedding_model:
        print("WARN: No active embedding model configured. Returning mock embedding.")
        return [0.0] * 384 # A common fallback dimension

    if EMBEDDING_PROVIDER_DEFAULT == "openai" and openai_embed_client:
        try:
            response = openai_embed_client.embeddings.create(input=[text], model=active_embedding_model)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error calling OpenAI embedding API (model: {active_embedding_model}): {e}")
            # Dimension for ada-002 is 1536. Other models might differ.
            return [0.0] * 1536 # Fallback for ada-002
    elif EMBEDDING_PROVIDER_DEFAULT == "sentence_transformers" and st_model:
        try:
            embedding = st_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Error using SentenceTransformer (model: {active_embedding_model}) for embedding: {e}")
            dim = getattr(st_model, 'get_sentence_embedding_dimension', lambda: 384)()
            return [0.0] * dim
    else:
        print(f"WARN: Embedding provider '{EMBEDDING_PROVIDER_DEFAULT}' or model '{active_embedding_model}' not available. Returning mock embedding.")
        dim = 1536 if active_embedding_model == EMBEDDING_MODEL_DEFAULT_OPENAI else 384
        # Simple hash-based mock, ensure it's float
        mock_emb = [float(ord(char) % 100) / 100.0 for char in text[:dim]]
        # Pad with zeros if text is shorter than dim
        mock_emb.extend([0.0] * (dim - len(mock_emb)))
        return mock_emb


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    np_vec1 = np.array(vec1, dtype=np.float32) # Ensure float type
    np_vec2 = np.array(vec2, dtype=np.float32)

    if np_vec1.shape != np_vec2.shape:
        print(f"Warning: Cosine similarity shape mismatch: {np_vec1.shape} vs {np_vec2.shape}. Returning 0.")
        return 0.0
    if np_vec1.ndim == 0 or np_vec2.ndim == 0 : # Handle scalar inputs if they somehow occur
        print(f"Warning: Cosine similarity received scalar input(s). Returning 0.")
        return 0.0
    if np_vec1.size == 0 or np_vec2.size == 0: # Handle empty vectors
        print(f"Warning: Cosine similarity received empty vector(s). Returning 0.")
        return 0.0


    dot_product = np.dot(np_vec1, np_vec2)
    norm_vec1 = np.linalg.norm(np_vec1)
    norm_vec2 = np.linalg.norm(np_vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)