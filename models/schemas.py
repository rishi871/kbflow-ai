from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid

class TicketDataInput(BaseModel):
    ticket_id: str = Field(..., description="External ticket ID")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    resolution_details: str = Field(..., description="How the ticket was resolved")
    conversation_log: Optional[str] = Field(None, description="Agent-customer conversation log")
    tags: Optional[List[str]] = Field(default_factory=list, description="Original ticket tags")

class KBDraft(BaseModel):
    draft_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_ticket_id: str
    generated_title: str
    generated_content_markdown: str # Full markdown content
    suggested_tags: List[str] = Field(default_factory=list)
    status: str = "pending_review" # pending_review, rejected
    created_at: str # ISO format string
    # Individual sections for easier access if needed (parsed from generated_content_markdown)
    problem_description: Optional[str] = None
    cause: Optional[str] = None
    resolution_steps: Optional[str] = None


class KBArticle(BaseModel):
    kb_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content_markdown: str
    tags: List[str] = Field(default_factory=list)
    created_at: str # ISO format string
    last_updated_at: str # ISO format string
    source_draft_id: Optional[str] = None
    # For RAG - the embedding is stored separately in a vector store typically
    # embedding: Optional[List[float]] = None # Not stored here directly in production

class KBSearchQuery(BaseModel):
    query: str
    top_k: int = 3

class KBSearchResultItem(BaseModel):
    kb_id: str
    title: str
    content_snippet: str # A snippet of the content or summary
    score: float
    full_content_markdown: Optional[str] = None # Optionally return full content

class KBSearchResponse(BaseModel):
    results: List[KBSearchResultItem]
    # Optional synthesized answer from RAG
    synthesized_answer: Optional[str] = None