import os
import urllib.parse

EXCLUDE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
EXCLUDE_FILES = {"README.md", "generate_readme.py"}

def tree(dir_path: str, prefix: str = "") -> list[str]:
    entries = [e for e in os.listdir(dir_path) if not e.startswith(".")]
    entries = [e for e in entries if e not in EXCLUDE_DIRS]
    entries = sorted(entries, key=lambda x: (os.path.isdir(os.path.join(dir_path, x)), x.lower()))

    lines = []
    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        rel_path = os.path.relpath(path, ".").replace("\\", "/")

        # фильтруем сам readme и скрипт
        if entry in EXCLUDE_FILES:
            continue

        link = f"[{entry}]({urllib.parse.quote(rel_path)})"
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{link}")

        if os.path.isdir(path):
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(tree(path, prefix + extension))
    return lines

lines = ["# Структура проекта", ""]
lines.extend(tree("."))

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
