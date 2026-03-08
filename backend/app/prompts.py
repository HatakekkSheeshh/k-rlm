"""
app/prompts.py — Prompt template registry.

Mỗi template là một dict với:
  - id:          key định danh (dùng trong API và frontend)
  - label:       tên hiển thị trên UI
  - system:      system prompt cố định (có thể để None)
  - user_tpl:    template cho user message, dùng {text} làm placeholder
                 Nếu None → dùng thẳng input của người dùng
"""
from __future__ import annotations

from typing import TypedDict


class PromptTemplate(TypedDict):
    id: str
    label: str
    system: str | None
    user_tpl: str | None


TEMPLATES: list[PromptTemplate] = [
    {
        "id": "raw",
        "label": "Raw (No Template)",
        "system": None,
        "user_tpl": None,
    },

    # ── OCR Information Extraction ────────────────────────────────────────────
    {
        "id": "ocr_extraction",
        "label": "OCR — Price & Expiry Extraction",
        "system": (
            "You are an information extraction model. "
            "Always respond with valid JSON only. No explanation, no markdown."
        ),
        "user_tpl": (
            "From the OCR text below, extract:\n"
            "1. Product price\n"
            "2. Expiry date\n\n"
            "Rules:\n"
            "- Return JSON format only\n"
            "- price must be a number\n"
            "- expiry_date must be in format YYYY-MM-DD\n"
            "- If not found return null\n\n"
            "OCR TEXT:\n{text}"
        ),
    },

    # ── Summarisation ─────────────────────────────────────────────────────────
    {
        "id": "summarise",
        "label": "Summarise Text",
        "system": "You are a concise summarisation assistant. Summarise clearly in 3-5 bullet points.",
        "user_tpl": "Summarise the following text:\n\n{text}",
    },
]

# Lookup dict: id → template
TEMPLATE_MAP: dict[str, PromptTemplate] = {t["id"]: t for t in TEMPLATES}


def apply_template(template_id: str, user_text: str) -> tuple[str, str | None]:
    """
    Returns (formatted_prompt, system_prompt) after applying the chosen template.
    Falls back to 'raw' if the id is unknown.
    """
    tpl = TEMPLATE_MAP.get(template_id, TEMPLATE_MAP["raw"])

    user_prompt = (
        tpl["user_tpl"].format(text=user_text)
        if tpl["user_tpl"]
        else user_text
    )
    return user_prompt, tpl["system"]
