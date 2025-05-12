from typing import Dict, List, Optional, Tuple
from models.schemas import KBDraft, KBArticle
from core.embedding_interface import get_embedding, cosine_similarity # For retriever part
import datetime

# In-memory storage (replace with a real DB for production)
db_drafts: Dict[str, KBDraft] = {}
db_published_kbs: Dict[str, KBArticle] = {}

# For RAG: Mimic a vector store with embeddings
# In a real system, use ChromaDB, FAISS, Pinecone, Weaviate etc.
vector_store_mimic: Dict[str, Tuple[KBArticle, List[float]]] = {} # kb_id -> (article_data, embedding)

def save_draft(draft: KBDraft):
    db_drafts[draft.draft_id] = draft

def get_draft(draft_id: str) -> Optional[KBDraft]:
    return db_drafts.get(draft_id)

def get_all_pending_drafts() -> List[KBDraft]:
    return [draft for draft in db_drafts.values() if draft.status == "pending_review"]

def update_draft_status(draft_id: str, status: str, feedback: Optional[str] = None):
    if draft_id in db_drafts:
        db_drafts[draft_id].status = status
        # In a real DB, you'd store feedback too
        print(f"Draft {draft_id} status updated to {status}. Feedback: {feedback or 'N/A'}")
        if status == "rejected": # Optionally remove or keep for audit
            pass # db_drafts.pop(draft_id, None)
        return True
    return False

def publish_kb_from_draft(draft_id: str, final_title: str, final_content: str, final_tags: List[str]) -> Optional[KBArticle]:
    draft = get_draft(draft_id)
    if not draft or draft.status != "pending_review":
        return None

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    published_kb = KBArticle(
        title=final_title,
        content_markdown=final_content,
        tags=final_tags,
        created_at=now_iso,
        last_updated_at=now_iso,
        source_draft_id=draft_id
    )
    db_published_kbs[published_kb.kb_id] = published_kb

    # "Embed" and store in our mimic vector store
    # In RAG, you might chunk larger documents. Here we embed the whole content.
    text_to_embed = f"Title: {published_kb.title}\nContent: {published_kb.content_markdown}"
    embedding = get_embedding(text_to_embed)
    vector_store_mimic[published_kb.kb_id] = (published_kb, embedding)

    # Remove from drafts (or mark as published)
    db_drafts.pop(draft_id, None)
    print(f"KB Article {published_kb.kb_id} published from draft {draft_id}.")
    return published_kb

def get_published_kb(kb_id: str) -> Optional[KBArticle]:
    return db_published_kbs.get(kb_id)

def search_vector_store(query_embedding: List[float], top_k: int) -> List[Tuple[KBArticle, float]]:
    if not vector_store_mimic:
        return []

    scored_articles = []
    for kb_id, (article_data, article_embedding) in vector_store_mimic.items():
        if not article_embedding or not query_embedding: # Handle cases where embedding might have failed
            similarity = 0.0
        elif len(article_embedding) != len(query_embedding):
            print(f"Warning: Embedding dimension mismatch for KB {kb_id}. Skipping.")
            similarity = 0.0
        else:
            similarity = cosine_similarity(query_embedding, article_embedding)
        scored_articles.append((article_data, similarity))

    # Sort by similarity score in descending order
    scored_articles.sort(key=lambda x: x[1], reverse=True)
    return scored_articles[:top_k]

# Initialize with a dummy KB for testing retriever
def init_dummy_data():
    if not db_published_kbs: # only if empty
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        dummy_kb = KBArticle(
            kb_id="dummy-kb-001",
            title="How to reset your password",
            content_markdown="## Problem Description\nUser forgot their password.\n\n## Resolution Steps\n1. Go to login page.\n2. Click 'Forgot Password'.\n3. Enter email.\n4. Follow instructions in email.",
            tags=["password", "account", "reset"],
            created_at=now_iso,
            last_updated_at=now_iso
        )
        db_published_kbs[dummy_kb.kb_id] = dummy_kb
        text_to_embed = f"Title: {dummy_kb.title}\nContent: {dummy_kb.content_markdown}"
        embedding = get_embedding(text_to_embed)
        vector_store_mimic[dummy_kb.kb_id] = (dummy_kb, embedding)
        print("Dummy KB initialized for testing.")

init_dummy_data()