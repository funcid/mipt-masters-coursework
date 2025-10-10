import os
import urllib.parse

EXCLUDE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
EXCLUDE_FILES = {"README.md"}
INCLUDE_EXTS = {".md", ".ipynb", ".java", ".kt", ".py"}

def tree(dir_path: str, level: int = 0) -> list[str]:
    entries = [e for e in os.listdir(dir_path) if not e.startswith(".")]
    entries = [e for e in entries if e not in EXCLUDE_DIRS]
    entries = sorted(entries, key=lambda x: (os.path.isdir(os.path.join(dir_path, x)), x.lower()))

    lines = []
    for entry in entries:
        path = os.path.join(dir_path, entry)
        rel_path = os.path.relpath(path, ".").replace("\\", "/")

        if os.path.isdir(path):
            # Сначала строим список детей
            children = tree(path, level + 1)
            if children:  # Папка пустая → пропускаем
                indent = "  " * level
                link = f"[{entry}]({urllib.parse.quote(rel_path)})"
                lines.append(f"{indent}- {link}")
                lines.extend(children)
        else:
            if entry in EXCLUDE_FILES:
                continue
            _, ext = os.path.splitext(entry)
            if ext.lower() in INCLUDE_EXTS:
                indent = "  " * level
                link = f"[{entry}]({urllib.parse.quote(rel_path)})"
                lines.append(f"{indent}- {link}")
    return lines

lines = ["# Структура проекта", ""]
lines.extend(tree("."))

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
