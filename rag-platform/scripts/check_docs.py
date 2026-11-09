"""Validate local Markdown targets and code fences without network requests."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPOSITORY = Path(__file__).resolve().parents[2]
EXCLUDED = {"node_modules", ".venv", ".git", ".next", ".mypy_cache", ".pytest_cache"}


def check_document(path: Path) -> list[str]:
    errors: list[str] = []
    fence = ""
    for number, line in enumerate(path.read_text().splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if not fence:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = ""
            continue
        if fence:
            continue
        for target in re.findall(r"\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", line):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(REPOSITORY) or not resolved.exists():
                errors.append(f"{path.relative_to(REPOSITORY)}:{number}: missing target {target}")
    if fence:
        errors.append(f"{path.relative_to(REPOSITORY)}: unclosed code fence")
    return errors


def main() -> int:
    documents = [
        path
        for path in REPOSITORY.rglob("*.md")
        if not EXCLUDED.intersection(path.relative_to(REPOSITORY).parts)
    ]
    errors = [error for path in documents for error in check_document(path)]
    for error in errors:
        print(error)
    print(f"Checked {len(documents)} Markdown documents; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
