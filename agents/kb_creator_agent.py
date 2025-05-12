from typing import Dict
from models.schemas import TicketDataInput, KBDraft
from core.llm_interface import get_llm_response, KB_CREATION_PROMPT_TEMPLATE
from db.in_memory_db import save_draft
import datetime
import re

def parse_llm_kb_response(markdown_text: str) -> Dict[str, str]:
    """
    Parses the LLM's Markdown response into structured sections.
    This is a simple parser; more robust parsing might be needed.
    """
    sections = {}
    current_section_name = None
    content_buffer = []

    # A more specific regex to capture only the desired sections
    # This regex looks for "## Section Name" and captures "Section Name"
    section_headers = [
        "Problem Description", "Environment", "Cause",
        "Resolution Steps", "Suggested Tags"
    ]
    # Create a regex pattern like (Problem Description|Environment|Cause|Resolution Steps|Suggested Tags)
    pattern_str = "|".join(re.escape(header) for header in section_headers)
    section_regex = re.compile(r"^##\s*(" + pattern_str + r")\s*$", re.MULTILINE)

    last_match_end = 0
    for match in section_regex.finditer(markdown_text):
        if current_section_name: # Save previous section content
            sections[current_section_name] = "".join(content_buffer).strip()

        # Content before this section header (if any, and not part of a previous section)
        # This part is tricky and might need refinement. For now, we focus on content *after* headers.

        current_section_name = match.group(1).strip()
        content_buffer = []
        last_match_end = match.end()

    # Add content after the last matched header
    if current_section_name:
        sections[current_section_name] = markdown_text[last_match_end:].strip()
    
    # If parsing fails to find sections, return the whole text as 'Content'
    if not sections and markdown_text:
        print("Warning: Could not parse LLM response into sections. Using full text.")
        sections["FullContent"] = markdown_text # Fallback

    return sections


def create_kb_draft_from_ticket(ticket_data: TicketDataInput) -> KBDraft:
    prompt = KB_CREATION_PROMPT_TEMPLATE.format(
        ticket_title=ticket_data.title,
        ticket_description=ticket_data.description,
        ticket_resolution=ticket_data.resolution_details,
        ticket_conversation=ticket_data.conversation_log or "N/A"
    )

    llm_generated_markdown = get_llm_response(prompt)

    # Try to parse common sections for easier access, but store full markdown
    # This parsing is basic and might need to be more robust.
    parsed_sections = parse_llm_kb_response(llm_generated_markdown)
    
    # Attempt to extract a title (e.g., first H1 if LLM doesn't make one, or use ticket title)
    # For simplicity, let's derive title from ticket if not easily parsable from LLM
    # Or even better, ask LLM to generate a title explicitly as part of the structure.
    # For now, we'll ask the user to confirm/edit title in supervisor UI.
    # Let's try to find a title in the generated content if present.
    title_match = re.search(r"^#\s*(.*)", llm_generated_markdown, re.MULTILINE)
    generated_title = title_match.group(1).strip() if title_match else ticket_data.title

    # Extract suggested tags
    suggested_tags_str = parsed_sections.get("Suggested Tags", "")
    suggested_tags = [tag.strip() for tag in suggested_tags_str.split(',') if tag.strip()] if suggested_tags_str else ticket_data.tags or []


    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    draft = KBDraft(
        source_ticket_id=ticket_data.ticket_id,
        generated_title=generated_title, # Will be refined by supervisor
        generated_content_markdown=llm_generated_markdown,
        suggested_tags=suggested_tags,
        problem_description=parsed_sections.get("Problem Description"),
        cause=parsed_sections.get("Cause"),
        resolution_steps=parsed_sections.get("Resolution Steps"),
        created_at=now_iso
    )
    save_draft(draft)
    return draft