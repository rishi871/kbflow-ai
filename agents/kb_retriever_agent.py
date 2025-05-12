from models.schemas import KBSearchQuery, KBSearchResultItem, KBSearchResponse
from core.embedding_interface import get_embedding
from core.llm_interface import get_llm_response # For RAG answer synthesis
from db.in_memory_db import search_vector_store

RAG_PROMPT_TEMPLATE = """
Based on the following knowledge base article excerpts, answer the user's question.
If the excerpts don't directly answer the question, say that you couldn't find a specific answer in the knowledge base.
Do not make up information. Cite the KB article titles if possible.

User Question: {query}

Knowledge Base Excerpts:
---
{context_str}
---

Answer:
"""

def search_knowledge_base(search_query: KBSearchQuery, synthesize_answer: bool = False) -> KBSearchResponse:
    query_embedding = get_embedding(search_query.query)
    
    # Perform semantic search
    # search_vector_store returns List[Tuple[KBArticle, float_score]]
    scored_articles_tuples = search_vector_store(query_embedding, search_query.top_k)

    results = []
    for article, score in scored_articles_tuples:
        # Create a snippet (e.g., first 200 chars of content)
        snippet = article.content_markdown[:200] + "..." if len(article.content_markdown) > 200 else article.content_markdown
        results.append(KBSearchResultItem(
            kb_id=article.kb_id,
            title=article.title,
            content_snippet=snippet,
            score=score,
            full_content_markdown=article.content_markdown # Send full content for Gradio to display
        ))

    synthesized_answer_text = None
    if synthesize_answer and results:
        # Prepare context for RAG
        context_parts = []
        for item in results: # Use top N results for context
            context_parts.append(f"Title: {item.title}\nContent: {item.content_snippet}\n---") # Use snippet or full content
        context_str = "\n".join(context_parts)
        
        rag_prompt = RAG_PROMPT_TEMPLATE.format(query=search_query.query, context_str=context_str)
        synthesized_answer_text = get_llm_response(rag_prompt, max_tokens=300)

    return KBSearchResponse(results=results, synthesized_answer=synthesized_answer_text)