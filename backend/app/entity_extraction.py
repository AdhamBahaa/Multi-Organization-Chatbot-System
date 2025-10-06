"""
Lightweight entity extraction: regex and simple patterns.
Keeps dependencies minimal; you can swap with spaCy or an LLM later.
"""
import re
from typing import List, Tuple


def extract_entities(text: str) -> List[Tuple[str, str]]:
    """
    Return a list of (entity_type, entity_name).
    Very simple heuristics: Emails, URLs, Numbers, Dates-like, Uppercase Terms.
    """
    entities: List[Tuple[str, str]] = []
    if not text:
        return entities

    # Emails
    for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        entities.append(("Email", m))

    # URLs
    for m in re.findall(r"https?://[^\s]+", text):
        entities.append(("URL", m))

    # Numbers (up to 6 digits)
    for m in re.findall(r"\b\d{1,6}\b", text):
        entities.append(("Number", m))

    # Date-like (very rough)
    for m in re.findall(r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})\b", text):
        entities.append(("Date", m))

    # Capitalized words that look like proper nouns (rough)
    for m in re.findall(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)\b", text):
        entities.append(("ProperNoun", m))

    return entities


