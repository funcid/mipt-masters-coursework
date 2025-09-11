import os
import urllib.parse

EXCLUDE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
EXCLUDE_FILES = {"README.md", "generate_readme.py"}

def tree(dir_path: str, level: int = 0) -> list[str]:
    entries = [e for e in os.listdir(dir_path) if not e.startswith(".")]
    entries = [e for e in entries if e not in EXCLUDE_DIRS]
    entries = sorted(entries, key=lambda x: (os.path.isdir(os.path.join(dir_path, x)), x.lower()))

    lines = []
    for entry in entries:
        path = os.path.join(dir_path, entry)
        rel_path = os.path.relpath(path, ".").replace("\\", "/")

        if entry in EXCLUDE_FILES:
            continue

        link = f"[{entry}]({urllib.parse.quote(rel_path)})"
        indent = "  " * level
        lines.append(f"{indent}- {link}")

        if os.path.isdir(path):
            lines.extend(tree(path, level + 1))
    return lines

lines = ["# Структура проекта", ""]
lines.extend(tree("."))

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
