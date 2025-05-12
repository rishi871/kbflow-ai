from openai import OpenAI
from core.config import (
    LLM_PROVIDER_DEFAULT,
    OPENAI_API_KEY, LLM_MODEL_DEFAULT_OPENAI,
    OPENROUTER_API_KEY, LLM_MODEL_DEFAULT_OPENROUTER, OPENROUTER_API_BASE,
    OPENROUTER_SITE_URL, OPENROUTER_APP_NAME,
    LLM_API_KEY_ACTIVE, LLM_API_BASE_ACTIVE, LLM_MODEL_ACTIVE
)

client = None

if LLM_API_KEY_ACTIVE:
    if LLM_PROVIDER_DEFAULT == "openrouter":
        client = OpenAI(
            base_url=OPENROUTER_API_BASE,
            api_key=LLM_API_KEY_ACTIVE,
            default_headers={ # Recommended by OpenRouter
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_APP_NAME,
            }
        )
        print(f"Using OpenRouter with model: {LLM_MODEL_ACTIVE}")
    elif LLM_PROVIDER_DEFAULT == "openai":
        client = OpenAI(api_key=LLM_API_KEY_ACTIVE)
        print(f"Using OpenAI with model: {LLM_MODEL_ACTIVE}")
    # Add other providers here if needed in the future
else:
    print("Warning: No LLM API key configured for the selected provider.")
    print("LLM functionality will be mocked or unavailable.")


def get_llm_response(prompt: str, model: str = None, max_tokens: int = 1500, temperature: float = 0.3) -> str:
    if not client:
        print("WARN: LLM client not initialized. Returning mock LLM response.")
        return f"Mock LLM Response for prompt: {prompt[:100]}..."

    active_model = model if model else LLM_MODEL_ACTIVE
    if not active_model:
        return "Error: No active LLM model configured."

    try:
        print(f"Sending request to LLM provider: {LLM_PROVIDER_DEFAULT}, model: {active_model}")
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling LLM ({LLM_PROVIDER_DEFAULT} with model {active_model}): {e}")
        return f"Error: Could not get response from LLM. Provider: {LLM_PROVIDER_DEFAULT}, Model: {active_model}"

# KB_CREATION_PROMPT_TEMPLATE remains the same
KB_CREATION_PROMPT_TEMPLATE = """
You are an expert technical writer creating a knowledge base article from a resolved support ticket.
Use the following ticket information to generate a draft KB article.

Ticket Information:
---
Title: {ticket_title}
Description: {ticket_description}
Resolution Details: {ticket_resolution}
Conversation Log (optional): {ticket_conversation}
---

Output the KB article in Markdown with AT LEAST the following sections (use more if appropriate):
## Problem Description
[Detailed problem faced by the user]

## Cause (if identifiable)
[Root cause of the issue]

## Resolution Steps
[Clear, step-by-step instructions to resolve the issue]

## Suggested Tags
[Up to 5 relevant keywords, comma-separated, e.g., Tag1, Tag2, Tag3]

Ensure the language is clear, professional, and easy to understand.
Do not include any preamble before the first "## Problem Description" section.
If resolution details are sparse, try to infer logical steps or state that detailed steps are needed.
"""

# RAG_PROMPT_TEMPLATE (from kb_retriever_agent.py, could also live here)
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