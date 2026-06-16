"""Diff-scoped code context via tree-sitter.

For each changed file we parse the file content at the PR head and, for the
changed lines, extract the enclosing function/class, the file's imports, and the
conventionally-named matching test file. The result is a compact blob per file
that gets fed to the specialist agents — no vector DB (out of scope for v1).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.state import Hunk

# Map file extension -> tree-sitter language name.
_LANG_BY_EXT = {".py": "python"}


@lru_cache(maxsize=None)
def _parser(lang: str):
    """Build (and cache) a tree-sitter Parser for a language."""
    from tree_sitter import Language, Parser

    if lang == "python":
        import tree_sitter_python as ts_python

        return Parser(Language(ts_python.language()))
    raise ValueError(f"Unsupported tree-sitter language: {lang}")

# Per-language node types we treat as "enclosing scope" and "import".
_SCOPE_TYPES = {
    "python": {"function_definition": "function", "class_definition": "class"},
}
_IMPORT_TYPES = {
    "python": {"import_statement", "import_from_statement"},
}


def _ext(path: str) -> str:
    dot = path.rfind(".")
    return path[dot:] if dot != -1 else ""


def _node_name(node) -> str | None:
    name = node.child_by_field_name("name")
    return name.text.decode("utf-8", "replace") if name else None


def _enclosing_scopes(root, line: int, lang: str) -> list[dict[str, Any]]:
    """Walk down to the deepest scope nodes spanning a 1-based line number."""
    row = line - 1
    scope_types = _SCOPE_TYPES[lang]
    chain: list[dict[str, Any]] = []
    node = root
    descended = True
    while descended:
        descended = False
        for child in node.children:
            if child.start_point[0] <= row <= child.end_point[0]:
                if child.type in scope_types:
                    chain.append({
                        "kind": scope_types[child.type],
                        "name": _node_name(child),
                        "start_line": child.start_point[0] + 1,
                        "end_line": child.end_point[0] + 1,
                    })
                node = child
                descended = True
                break
    return chain


def _imports(root, source: bytes, lang: str) -> list[str]:
    import_types = _IMPORT_TYPES[lang]
    out: list[str] = []
    for child in root.children:
        if child.type in import_types:
            out.append(source[child.start_byte:child.end_byte].decode("utf-8", "replace"))
    return out


def matching_test_path(path: str) -> str | None:
    """Conventional test path for a source file, or None for non-source files."""
    if not path.endswith(".py") or "/test" in path or path.startswith("test"):
        return None
    parts = path.rsplit("/", 1)
    fname = parts[-1]
    return f"tests/test_{fname}"


def build_file_context(
    path: str, source: str | None, changed_lines: list[int]
) -> dict[str, Any]:
    """Build a compact context blob for one changed file."""
    blob: dict[str, Any] = {
        "path": path,
        "language": None,
        "imports": [],
        "enclosing": [],
        "matching_test": matching_test_path(path),
    }

    lang = _LANG_BY_EXT.get(_ext(path))
    if lang is None or source is None:
        return blob  # unsupported language or content unavailable — degrade gracefully

    blob["language"] = lang
    src_bytes = source.encode("utf-8")
    tree = _parser(lang).parse(src_bytes)
    root = tree.root_node

    blob["imports"] = _imports(root, src_bytes, lang)

    seen: set[tuple[str | None, int]] = set()
    for line in changed_lines:
        for scope in _enclosing_scopes(root, line, lang):
            key = (scope["name"], scope["start_line"])
            if key not in seen:
                seen.add(key)
                blob["enclosing"].append(scope)
    return blob


def changed_lines_for(path: str, hunks: dict[str, list[Hunk]]) -> list[int]:
    """All added (new-side) line numbers for a path across its hunks."""
    lines: list[int] = []
    for h in hunks.get(path, []):
        lines.extend(h["added_lines"])
    return sorted(set(lines))
