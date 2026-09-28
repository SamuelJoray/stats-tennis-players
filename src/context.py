"""Loads per-table domain-knowledge notes from context/*.md.

This is prompt augmentation: the schema alone tells the model column names
and types, but not what a code like "4f8b2f3b1f#" in the points table's
'1st' column means. Files here fill that gap. A missing or empty file for a
table is simply skipped -- schema + sample values is all the model gets.
"""

import os

CONTEXT_DIR = "context"


def build_context_text() -> str:
    if not os.path.isdir(CONTEXT_DIR):
        return ""

    sections = []
    for filename in sorted(os.listdir(CONTEXT_DIR)):
        if not filename.endswith(".md"):
            continue
        path = os.path.join(CONTEXT_DIR, filename)
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            sections.append(content)

    return "\n\n".join(sections)


if __name__ == "__main__":
    print(build_context_text())
