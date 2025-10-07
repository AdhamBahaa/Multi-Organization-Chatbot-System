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


def extract_relations(text: str) -> List[Tuple[str, str, str]]:
    """
    Very lightweight, rule-based extraction of typed relations from text.
    Returns a list of (subject, predicate, object) triples.

    Supported (best-effort):
    - KNOWS: "Alice knows Bob"
    - LIVES_IN / LOCATED_IN: "Bob lives in Cairo", "Company located in Cairo"
    - WORKS_AT: "Alice works at Acme"
    - PART_OF: "X is part of Y"
    - REPORTS_TO: "X reports to Y"
    - AGE: "Alice is 30 years old" (object is a number as string)

    This is deliberately simple and language-agnostic English heuristics.
    For production, replace with spaCy or an LLM-based extractor.
    """
    triples: List[Tuple[str, str, str]] = []
    if not text:
        return triples

    # Normalize whitespace
    t = re.sub(r"\s+", " ", text).strip()

    # Split on sentence terminators (very rough)
    sentences = re.split(r"[\.!?]\s+", t)

    proper_noun = r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    thing = r"([A-Z][a-zA-Z0-9_\-]{2,}(?:\s+[A-Z][a-zA-Z0-9_\-]{2,})*)"

    patterns = [
        # Alice knows Bob
        (re.compile(rf"\b{proper_noun}\s+knows\s+{proper_noun}\b"), "KNOWS", (1, 2)),
        # Bob lives in Cairo
        (re.compile(rf"\b{proper_noun}\s+lives\s+in\s+{proper_noun}\b"), "LIVES_IN", (1, 2)),
        # X is located in Y / located in
        (re.compile(rf"\b{thing}\s+located\s+in\s+{proper_noun}\b", re.IGNORECASE), "LOCATED_IN", (1, 2)),
        # Alice works at Acme
        (re.compile(rf"\b{proper_noun}\s+works\s+at\s+{thing}\b"), "WORKS_AT", (1, 2)),
        # X is part of Y
        (re.compile(rf"\b{thing}\s+is\s+part\s+of\s+{thing}\b", re.IGNORECASE), "PART_OF", (1, 2)),
        # X reports to Y
        (re.compile(rf"\b{proper_noun}\s+reports\s+to\s+{proper_noun}\b"), "REPORTS_TO", (1, 2)),
        # Alice is 30 years old
        (re.compile(rf"\b{proper_noun}\s+is\s+(\d{{1,3}})\s+years\s+old\b"), "AGE", (1, 2)),
    ]

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        for pat, rel, (si, oi) in patterns:
            m = pat.search(s)
            if not m:
                continue
            try:
                subj = m.group(si)
                obj = m.group(oi)
                triples.append((subj, rel, obj))
            except IndexError:
                continue

    return triples


