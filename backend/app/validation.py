"""
Response validation and correction using LangChain with Google Gemini.
Falls back gracefully if LangChain or the provider is unavailable.
"""
from __future__ import annotations

from typing import Tuple, Optional, Dict, Any
import re

from .config import (
    ENABLE_LC_VALIDATION,
    VALIDATION_MAX_CHARS,
    API_KEY,
    ENABLE_FACT_CHECK_VALIDATION,
)


def _is_plain_text(s: str) -> bool:
    """Check for obvious Markdown/formatting we want to avoid."""
    # Disallow common markdown tokens at line starts or inline
    md_patterns = [
        r"\*\*.+\*\*",  # bold
        r"\*.+\*",        # italic
        r"^\s*[-*+]\s+",  # bullet list at line start
        r"^\s*#{1,6}\s+", # headings
        r"`{1,3}.+`{1,3}",  # code spans/blocks
    ]
    for p in md_patterns:
        if re.search(p, s, flags=re.MULTILINE):
            return False
    return True


def _detect_language_simple(text: str) -> str:
    arabic_pattern = r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
    return "Arabic" if re.search(arabic_pattern, text) else "English"


def _needs_fix(response_text: str, expected_language: str) -> Tuple[bool, str]:
    """Return (needs_fix, reason)."""
    if VALIDATION_MAX_CHARS > 0 and len(response_text) > VALIDATION_MAX_CHARS:
        print(f"[validator] Check: length {len(response_text)} > {VALIDATION_MAX_CHARS} -> needs fix")
        return True, "too_long"
    if not _is_plain_text(response_text):
        print("[validator] Check: formatting -> markdown detected -> needs fix")
        return True, "formatting"
    detected = _detect_language_simple(response_text)
    print(f"[validator] Check: language detected={detected}, expected={expected_language}")
    if expected_language != "English" and detected != expected_language:
        print("[validator] Check: language mismatch -> needs fix")
        return True, "language"
    return False, ""


def _safe_parse_json(s: str) -> Optional[Dict[str, Any]]:
    import json
    # strip code fences if the model wrapped JSON
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`\n ")
        # remove leading json hint if present
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    try:
        return json.loads(s)
    except Exception:
        return None


def _run_fact_check(question: str, answer: str, context: str) -> Optional[Dict[str, Any]]:
    """Run a LangChain fact-check against context, returning parsed JSON or None."""
    if not ENABLE_FACT_CHECK_VALIDATION:
        print("[fact-check] Disabled via ENABLE_FACT_CHECK_VALIDATION=false; skipping")
        return None
    if not API_KEY:
        print("[fact-check] Skipped: GOOGLE_API_KEY not configured")
        return None
    try:
        print("[fact-check] Running fact-check via LangChain + Gemini...")
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate

        system = (
            "You are a meticulous fact-checker AI. Your task is to evaluate a generated answer based STRICTLY on the provided context.\n"
            "Your output must be a JSON object with the keys 'is_fully_valid' and 'hallucinated_statements'."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            (
                "human",
                "Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:\n{answer}\n\nNow return ONLY a JSON object with keys 'is_fully_valid' (boolean) and 'hallucinated_statements' (array of strings).",
            ),
        ])

        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY, temperature=0.0)
        chain = prompt | llm
        out = chain.invoke({"context": context, "question": question, "answer": answer})
        content = out.content if hasattr(out, "content") else str(out)
        parsed = _safe_parse_json(content)
        if parsed is None:
            print(f"[fact-check] Warning: unable to parse JSON. Raw output: {repr(content[:400])}...")
            return None
        print(f"[fact-check] Result: {parsed}")
        return parsed
    except Exception as e:
        print(f"[fact-check] Error: {e}")
        return None


def validate_and_fix_response(user_question: str, response_text: str, expected_language: str, *, context_text: Optional[str] = None) -> str:
    """
    Validate LLM output and attempt to fix it using LangChain + Gemini.
    If LangChain or the provider is unavailable, apply lightweight cleanups.
    """
    if not ENABLE_LC_VALIDATION:
        print("[validator] Disabled via ENABLE_LC_VALIDATION=false; skipping")
        return response_text

    print("[validator] Running validation...")
    needs_fix, reason = _needs_fix(response_text, expected_language)
    if needs_fix:
        print(f"[validator] Needs fix due to: {reason}")
    if not needs_fix:
        print("[validator] Passed all checks; returning as-is")
        return response_text

    # Try LangChain-based rewrite first
    try:
        if not API_KEY:
            raise RuntimeError("Gemini API key not configured")

        print("[validator] Attempting LangChain rewrite with Gemini...")

        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate

        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY, temperature=0.1)

        system = (
            "You are a strict response formatter. Rewrite the assistant's answer to:\n"
            "- Use ONLY plain text (no Markdown, no asterisks, no headings, no bullets).\n"
            f"- Respond entirely in {expected_language}.\n"
            "- Keep the meaning but simplify formatting.\n"
            + (f"- Ensure length <= {VALIDATION_MAX_CHARS} characters.\n" if VALIDATION_MAX_CHARS > 0 else "")
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", "User question: {question}\nAssistant answer: {answer}\nRewrite now."),
        ])

        chain = prompt | llm
        out = chain.invoke({"question": user_question, "answer": response_text})
        fixed = out.content if hasattr(out, "content") else str(out)

        # Final local guard
        fixed = fixed.strip()
        if VALIDATION_MAX_CHARS > 0 and len(fixed) > VALIDATION_MAX_CHARS:
            fixed = fixed[:VALIDATION_MAX_CHARS]
            print("[validator] Post-fix: truncated to max chars")
        # Remove any lingering Markdown flair
        fixed = re.sub(r"\*\*([^*]+)\*\*", r"\1", fixed)
        fixed = re.sub(r"\*([^*]+)\*", r"\1", fixed)
        fixed = re.sub(r"^\s*[-*+]\s+", "", fixed, flags=re.MULTILINE)
        fixed = re.sub(r"^\s*#{1,6}\s+", "", fixed, flags=re.MULTILINE)
        print("[validator] LangChain rewrite complete; returning fixed text")
        # Optional fact-check after rewrite if context provided
        if context_text:
            _ = _run_fact_check(user_question, fixed, context_text)
        return fixed
    except Exception as _:
        # Fallback: quick local cleanup
        print("[validator] LangChain rewrite unavailable; using local cleanup")
        fixed = response_text
        # Trim length
        if VALIDATION_MAX_CHARS > 0 and len(fixed) > VALIDATION_MAX_CHARS:
            fixed = fixed[:VALIDATION_MAX_CHARS]
            print("[validator] Local cleanup: truncated to max chars")
        # Strip common markdown
        fixed = re.sub(r"\*\*([^*]+)\*\*", r"\1", fixed)
        fixed = re.sub(r"\*([^*]+)\*", r"\1", fixed)
        fixed = re.sub(r"^\s*[-*+]\s+", "", fixed, flags=re.MULTILINE)
        fixed = re.sub(r"^\s*#{1,6}\s+", "", fixed, flags=re.MULTILINE)
        print("[validator] Local cleanup complete; returning fixed text")
        fixed = fixed.strip()
        # Optional fact-check even if we did local cleanup (best effort)
        if context_text:
            _ = _run_fact_check(user_question, fixed, context_text)
        return fixed
