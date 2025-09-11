import os

EXCLUDE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}

def tree(dir_path: str, prefix: str = "") -> str:
    entries = [e for e in os.listdir(dir_path) if not e.startswith(".")]
    entries = [e for e in entries if e not in EXCLUDE_DIRS]
    entries = sorted(entries, key=lambda x: (os.path.isdir(os.path.join(dir_path, x)), x))

    lines = []
    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry}")
        if os.path.isdir(path):
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(tree(path, prefix + extension))
    return lines

lines = ["# Project Structure", "```"]
lines.extend(tree("."))
lines.append("```")

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
