"""Prompt service — assembles the final prompt from persona, RAG, and history.

System prompt contains ONLY tone/manner instructions.
All SCP knowledge comes from RAG at query time.

Message ordering (designed to keep persona voice anchored despite a large RAG
context block):

    [system]    persona.system_prompt
    [user]      few-shot example #1 user
    [assistant] few-shot example #1 assistant
    [user]      few-shot example #2 user
    [assistant] few-shot example #2 assistant
    [system]    # Retrieved SCP Documents: ...
    [user/asst] conversation history ...
    [user]      {current message}\\n\\n---\\n[캐릭터 지시] {closing_directive}

The closing directive piggy-backs on the recency bias — even after a 1-2k
token RAG block, the very last line the model sees is a persona reminder.
"""

from app.core.personas import Persona
from app.models.session import Message


def build_prompt(
    persona: Persona,
    rag_results: list[dict],
    conversation_history: list[Message],
    user_message: str,
) -> list[dict]:
    """Assemble the final prompt for vLLM chat/completions."""
    messages: list[dict] = []

    messages.append({"role": "system", "content": persona.system_prompt})

    for example_user, example_assistant in persona.few_shot_examples:
        messages.append({"role": "user", "content": example_user})
        messages.append({"role": "assistant", "content": example_assistant})

    if rag_results:
        context_blocks = []
        for r in rag_results:
            item = r.get("item_number", "Unknown")
            section = r.get("section_type", "unknown")
            text = r.get("text", "")
            context_blocks.append(f"[{item}] ({section})\n{text}")

        context_text = "\n\n---\n\n".join(context_blocks)
        messages.append({
            "role": "system",
            "content": f"# Retrieved SCP Documents:\n{context_text}",
        })

    for msg in conversation_history:
        messages.append({"role": msg.role, "content": msg.content})

    final_user_content = user_message
    if persona.closing_directive:
        final_user_content = (
            f"{user_message}\n\n---\n[캐릭터 지시] {persona.closing_directive}"
        )
    messages.append({"role": "user", "content": final_user_content})

    return messages


def extract_sources(rag_results: list[dict]) -> list[str]:
    """Extract unique source URLs from RAG results."""
    urls: set[str] = set()
    for r in rag_results:
        url = r.get("url")
        if url:
            urls.add(url)
    return sorted(urls)
