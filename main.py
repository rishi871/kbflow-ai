from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from typing import List
from models.schemas import (
    TicketDataInput, KBDraft, KBArticle,
    KBSearchQuery, KBSearchResponse
)
from agents.kb_creator_agent import create_kb_draft_from_ticket
from agents.kb_retriever_agent import search_knowledge_base
from db.in_memory_db import (
    get_all_pending_drafts, get_draft, update_draft_status,
    publish_kb_from_draft, get_published_kb
)
import datetime

app = FastAPI(title="AI-Powered KB Workflow API")

@app.post("/api/v1/kb/drafts/from_ticket", response_model=KBDraft, status_code=201)
async def create_draft_endpoint(ticket_data: TicketDataInput):
    """
    Creates a KB draft from resolved ticket data.
    """
    try:
        draft = create_kb_draft_from_ticket(ticket_data)
        return draft
    except Exception as e:
        print(f"Error creating draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")

@app.get("/api/v1/kb/drafts/pending", response_model=List[KBDraft])
async def list_pending_drafts_endpoint():
    """
    Lists all KB drafts pending review.
    """
    return get_all_pending_drafts()

@app.get("/api/v1/kb/drafts/{draft_id}", response_model=KBDraft)
async def get_draft_endpoint(draft_id: str):
    """
    Retrieves a specific KB draft by ID.
    """
    draft = get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

class ApproveRejectPayload(BaseModel):
    final_title: Optional[str] = None
    final_content_markdown: Optional[str] = None
    final_tags: Optional[List[str]] = None
    feedback: Optional[str] = None # For rejections

@app.put("/api/v1/kb/drafts/{draft_id}/approve", response_model=KBArticle)
async def approve_draft_endpoint(
    draft_id: str,
    payload: ApproveRejectPayload = Body(...)
):
    """
    Approves a KB draft, publishing it as an article.
    Requires final_title, final_content_markdown, and final_tags in payload.
    """
    if not all([payload.final_title, payload.final_content_markdown, payload.final_tags is not None]):
         raise HTTPException(status_code=400, detail="final_title, final_content_markdown, and final_tags are required for approval.")

    published_kb = publish_kb_from_draft(
        draft_id,
        payload.final_title,
        payload.final_content_markdown,
        payload.final_tags
    )
    if not published_kb:
        raise HTTPException(status_code=404, detail="Draft not found or already processed")
    return published_kb

@app.put("/api/v1/kb/drafts/{draft_id}/reject")
async def reject_draft_endpoint(draft_id: str, payload: ApproveRejectPayload = Body(...)):
    """
    Rejects a KB draft.
    """
    success = update_draft_status(draft_id, "rejected", payload.feedback)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"message": "Draft rejected successfully", "draft_id": draft_id}

@app.post("/api/v1/kb/search", response_model=KBSearchResponse)
async def search_kb_endpoint(search_payload: KBSearchQuery, synthesize_answer: bool = False):
    """
    Searches the knowledge base using natural language.
    Set synthesize_answer=true query param to get a RAG-style answer.
    """
    return search_knowledge_base(search_payload, synthesize_answer=synthesize_answer)

@app.get("/api/v1/kb/published/{kb_id}", response_model=KBArticle)
async def get_published_kb_endpoint(kb_id: str):
    """
    Retrieves a specific published KB article by ID.
    """
    kb = get_published_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Published KB not found")
    return kb


# --- Placeholder for KB Improviser Endpoints ---
# @app.post("/api/v1/kb/{kb_id}/suggestions")
# async def suggest_improvements_endpoint(kb_id: str, new_info: str = Body(..., embed=True)):
#     # Call kb_improviser_agent.suggest_kb_improvements(kb_id, new_info)
#     return {"message": "Improvement suggestion process initiated (placeholder)."}

if __name__ == "__main__":
    import uvicorn
    # Initialize dummy data if needed (already called in in_memory_db.py)
    # from db.in_memory_db import init_dummy_data
    # init_dummy_data()
    uvicorn.run(app, host="0.0.0.0", port=8000)