import gradio as gr
import requests # To call FastAPI backend
import json
import datetime

FASTAPI_BASE_URL = "http://127.0.0.1:8000/api/v1"

# --- Helper functions to interact with FastAPI ---
def get_pending_drafts_choices():
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/kb/drafts/pending")
        response.raise_for_status()
        drafts = response.json()
        # Return choices as (display_name, value) for Gradio dropdown
        return [(f"{d['generated_title'][:50]}... (ID: {d['draft_id'][:8]})", d['draft_id']) for d in drafts]
    except Exception as e:
        print(f"Error fetching drafts: {e}")
        return []

def load_draft_details(draft_id):
    if not draft_id:
        return "", "", "", "", "", "", "" # Clear fields
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/kb/drafts/{draft_id}")
        response.raise_for_status()
        draft = response.json()
        tags_str = ", ".join(draft.get('suggested_tags', []))
        return (
            draft.get('draft_id', ''),
            draft.get('generated_title', ''),
            draft.get('generated_content_markdown', ''),
            tags_str,
            draft.get('problem_description', 'N/A'),
            draft.get('cause', 'N/A'),
            draft.get('resolution_steps', 'N/A')
        )
    except Exception as e:
        print(f"Error loading draft {draft_id}: {e}")
        return draft_id, f"Error: {e}", "", "", "", "", ""

def approve_kb_draft(draft_id, final_title, final_content, final_tags_str, feedback="Approved via Gradio"):
    if not all([draft_id, final_title, final_content, final_tags_str is not None]):
        return "Error: Missing required fields for approval (ID, Title, Content, Tags)."
    try:
        tags_list = [tag.strip() for tag in final_tags_str.split(',') if tag.strip()]
        payload = {
            "final_title": final_title,
            "final_content_markdown": final_content,
            "final_tags": tags_list
        }
        response = requests.put(f"{FASTAPI_BASE_URL}/kb/drafts/{draft_id}/approve", json=payload)
        response.raise_for_status()
        return f"Draft {draft_id} approved successfully! Published KB: {response.json().get('kb_id')}"
    except Exception as e:
        return f"Error approving draft {draft_id}: {e}"

def reject_kb_draft(draft_id, feedback="Rejected via Gradio"):
    if not draft_id:
        return "Error: Draft ID is missing."
    if not feedback:
        feedback = "Rejected without specific feedback via Gradio."
    try:
        payload = {"feedback": feedback}
        response = requests.put(f"{FASTAPI_BASE_URL}/kb/drafts/{draft_id}/reject", json=payload)
        response.raise_for_status()
        return f"Draft {draft_id} rejected. Feedback: {feedback}"
    except Exception as e:
        return f"Error rejecting draft {draft_id}: {e}"

def search_kb(query, top_k=3, synthesize=False):
    if not query:
        return "Please enter a search query.", ""
    try:
        params = {"synthesize_answer": synthesize}
        payload = {"query": query, "top_k": int(top_k)}
        response = requests.post(f"{FASTAPI_BASE_URL}/kb/search", params=params, json=payload)
        response.raise_for_status()
        search_response_data = response.json()
        
        results_md = "### Search Results:\n"
        if not search_response_data["results"]:
            results_md += "No relevant KBs found."
        for item in search_response_data["results"]:
            results_md += f"\n---\n**Title:** {item['title']} (ID: {item['kb_id']}, Score: {item['score']:.2f})\n"
            results_md += f"**Snippet:**\n```\n{item['content_snippet']}\n```\n"
            # results_md += f"**Full Content:**\n```markdown\n{item['full_content_markdown']}\n```\n"


        synthesized_answer_md = ""
        if search_response_data.get("synthesized_answer"):
            synthesized_answer_md = f"### Synthesized Answer:\n{search_response_data['synthesized_answer']}"
        
        return results_md, synthesized_answer_md
    except Exception as e:
        return f"Error searching KB: {e}", ""

def create_example_draft():
    # This is for demo; in real life, it's triggered by the ticket system
    ticket_payload = {
        "ticket_id": f"DEMO-{datetime.datetime.now().strftime('%H%M%S')}",
        "title": "User cannot log in after password change",
        "description": "A user reported that they changed their password recently but now cannot log in. They see an 'Invalid credentials' error.",
        "resolution_details": "Advised user to clear browser cache and cookies. If that doesn't work, try resetting the password again carefully ensuring no typos. Confirmed user was able to log in after clearing cache.",
        "conversation_log": "User: I changed my password and now I can't log in!\nAgent: Okay, can you try clearing your browser cache and cookies first?\nUser: How do I do that?\nAgent: [Instructions for Chrome]\nUser: Okay, I did that... it worked! Thanks!",
        "tags": ["login", "password", "cache"]
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/kb/drafts/from_ticket", json=ticket_payload)
        response.raise_for_status()
        draft = response.json()
        return f"Example draft created: {draft['draft_id']}. Refresh pending drafts list."
    except Exception as e:
        return f"Error creating example draft: {e}"

# --- Gradio UI Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI-Powered KB Workflow - Supervisor UI")

    with gr.Tabs():
        with gr.TabItem("KB Draft Review"):
            with gr.Row():
                pending_drafts_dropdown = gr.Dropdown(label="Select Pending Draft", choices=get_pending_drafts_choices(), interactive=True)
                refresh_drafts_btn = gr.Button("Refresh Drafts List")
                create_example_draft_btn = gr.Button("Create Example Draft (Demo)")
            
            output_status_review = gr.Textbox(label="Action Status", interactive=False)
            
            draft_id_hidden = gr.Textbox(label="Draft ID (Hidden)", visible=False) # Keep track of current draft

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### AI Generated Sections (Reference)")
                    draft_problem_desc = gr.Markdown(label="Problem Description")
                    draft_cause = gr.Markdown(label="Cause")
                    draft_resolution_steps = gr.Markdown(label="Resolution Steps")
                with gr.Column(scale=2):
                    gr.Markdown("### Editable KB Article Content")
                    final_kb_title = gr.Textbox(label="Final KB Title", interactive=True)
                    final_kb_content = gr.TextArea(label="Final KB Content (Markdown)", lines=15, interactive=True)
                    final_kb_tags = gr.Textbox(label="Final Tags (comma-separated)", interactive=True)
            
            with gr.Row():
                approve_btn = gr.Button("Approve & Publish KB")
                reject_feedback_text = gr.Textbox(label="Rejection Feedback (Optional)", interactive=True)
                reject_btn = gr.Button("Reject Draft")

        with gr.TabItem("KB Search & Retrieve"):
            search_query_input = gr.Textbox(label="Describe your issue (Natural Language):")
            with gr.Row():
                search_top_k_slider = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="Top K Results")
                search_synthesize_checkbox = gr.Checkbox(label="Synthesize Answer (RAG)", value=False)
            search_kb_btn = gr.Button("Search Knowledge Base")
            
            gr.Markdown("---")
            search_results_display = gr.Markdown(label="Search Results")
            synthesized_answer_display = gr.Markdown(label="Synthesized Answer (from RAG)")

        # TODO: Add KB Improviser UI Tab later

    # --- Event Handlers ---
    refresh_drafts_btn.click(
        fn=get_pending_drafts_choices,
        outputs=pending_drafts_dropdown
    )
    create_example_draft_btn.click(
        fn=create_example_draft,
        outputs=output_status_review
    ).then(
        fn=get_pending_drafts_choices, # Refresh dropdown after creating
        outputs=pending_drafts_dropdown
    )

    pending_drafts_dropdown.change(
        fn=load_draft_details,
        inputs=pending_drafts_dropdown,
        outputs=[draft_id_hidden, final_kb_title, final_kb_content, final_kb_tags, draft_problem_desc, draft_cause, draft_resolution_steps]
    )

    approve_btn.click(
        fn=approve_kb_draft,
        inputs=[draft_id_hidden, final_kb_title, final_kb_content, final_kb_tags, reject_feedback_text], # feedback used as placeholder
        outputs=output_status_review
    ).then(
        fn=get_pending_drafts_choices, # Refresh dropdown after action
        outputs=pending_drafts_dropdown
    )

    reject_btn.click(
        fn=reject_kb_draft,
        inputs=[draft_id_hidden, reject_feedback_text],
        outputs=output_status_review
    ).then(
        fn=get_pending_drafts_choices, # Refresh dropdown after action
        outputs=pending_drafts_dropdown
    )
    
    search_kb_btn.click(
        fn=search_kb,
        inputs=[search_query_input, search_top_k_slider, search_synthesize_checkbox],
        outputs=[search_results_display, synthesized_answer_display]
    )

if __name__ == "__main__":
    demo.launch()