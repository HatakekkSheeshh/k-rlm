"""
Prompt template registry.
Each template: id, label, system, user_tpl (with {text} placeholder).
"""
from __future__ import annotations

from typing import TypedDict


class PromptTemplate(TypedDict):
    id: str
    label: str
    system: str | None
    user_tpl: str | None


TEMPLATES: list[PromptTemplate] = [
    {"id": "raw", "label": "Raw (No Template)", "system": None, "user_tpl": None},
    {
        "id": "ocr_extraction",
        "label": "OCR — Price & Expiry Extraction",
        "system": "You are an information extraction model. Always respond with valid JSON only. No explanation, no markdown.",
        "user_tpl": "From the OCR text below, extract:\n1. Product price\n2. Expiry date\n\nRules:\n- Return JSON format only\n- price must be a number\n- expiry_date must be in format YYYY-MM-DD\n- If not found return null\n\nOCR TEXT:\n{text}"
    },
    {
        "id": "summarise",
        "label": "Summarise Text",
        "system": "You are a concise summarisation assistant. Summarise clearly in 3-5 bullet points.",
        "user_tpl": "Summarise the following text:\n\n{text}",
    },
]

TEMPLATE_MAP: dict[str, PromptTemplate] = {t["id"]: t for t in TEMPLATES}


def apply_template(template_id: str, user_text: str) -> tuple[str, str | None]:
    """Apply template to user text. Falls back to raw if unknown."""
    tpl = TEMPLATE_MAP.get(template_id, TEMPLATE_MAP["raw"])
    user_prompt = tpl["user_tpl"].format(text=user_text) if tpl["user_tpl"] else user_text
    return user_prompt, tpl["system"]
