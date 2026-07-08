#!/usr/bin/env python3
"""Sanitize generated repository content before the first push.

The upstream SQL demo data may contain cloud-provider credential-looking
example values. GitHub Push Protection blocks these even when they are sample
seed data, so replace them with explicit placeholders before committing the
new repository.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()

# Provider-specific access key identifiers that GitHub Push Protection detects.
DIRECT_REPLACEMENTS = [
    (re.compile(r"AKID[A-Za-z0-9]{13,}"), "TENCENT_CLOUD_SECRET_ID_PLACEHOLDER"),
    (re.compile(r"LTAI[A-Za-z0-9]{12,}"), "ALIBABA_CLOUD_ACCESS_KEY_ID_PLACEHOLDER"),
    (re.compile(r"AKLT[A-Za-z0-9]{12,}"), "VOLCENGINE_ACCESS_KEY_ID_PLACEHOLDER"),
]

# Secret values often sit in rows whose key/name/remark contains these words.
SECRET_CONTEXT_RE = re.compile(
    r"(?i)(secret[_-]?key|access[_-]?key[_-]?secret|secretid|secret_id|accessKeySecret|access-key-secret)"
)
QUOTED_VALUE_RE = re.compile(r"'([A-Za-z0-9/+_=.-]{24,})'")

# Avoid changing structural SQL identifiers; only sanitize long quoted values
# in lines that are clearly about cloud credentials.
PLACEHOLDER = "'CLOUD_SECRET_PLACEHOLDER'"


def sanitize_text(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in DIRECT_REPLACEMENTS:
        text, n = pattern.subn(replacement, text)
        count += n

    lines = []
    for line in text.splitlines(keepends=True):
        if SECRET_CONTEXT_RE.search(line):
            line, n = QUOTED_VALUE_RE.subn(PLACEHOLDER, line)
            count += n
        lines.append(line)
    return "".join(lines), count


def main() -> int:
    total = 0
    changed_files = 0
    for path in sorted(ROOT.rglob("*.sql")):
        if any(part in {".git", "node_modules", "target", "dist", "build"} for part in path.parts):
            continue
        original = path.read_text(encoding="utf-8", errors="ignore")
        sanitized, count = sanitize_text(original)
        if sanitized != original:
            path.write_text(sanitized, encoding="utf-8")
            total += count
            changed_files += 1
            print(f"Sanitized {count} credential-like values in {path.relative_to(ROOT)}")

    print(f"Credential-like SQL sanitization complete: files={changed_files}, replacements={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
