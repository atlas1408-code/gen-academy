"""Compose a postable markdown comment from a structured Finding."""


def compose_comment(f: dict) -> str:
    """Build the markdown body posted to GitHub from structured fields."""
    sev = (f.get("severity") or "").upper()
    title = f.get("title") or (f.get("problem") or "")[:60]
    parts = [f"**[{sev}] {title}**" if title else f"**[{sev}]**"]
    if f.get("problem"):
        parts.append(f"**Problem:** {f['problem']}")
    if f.get("suggestion"):
        parts.append(f"**Suggestion:** {f['suggestion']}")
    return "\n\n".join(parts)
