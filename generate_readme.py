import os

EXCLUDE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}

def make_anchor(path: str) -> str:
    return path.lower().replace(" ", "-").replace("_", "-").replace(".", "")

lines = ["# Project Files\n"]

anchors = []

for root, dirs, files in os.walk(".", topdown=True):
    # фильтруем лишние папки
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
    files = [f for f in files if not f.startswith(".")]

    for f in files:
        path = os.path.join(root, f).replace("\\", "/")
        if path.startswith("./"):
            path = path[2:]
        anchor = make_anchor(path)
        lines.append(f"- [{path}](#{anchor})")
        anchors.append((anchor, path))

# описания для каждого файла
lines.append("\n---\n")
for anchor, path in anchors:
    lines.append(f"## {path}\n")
    lines.append("*(описание файла)*\n")

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
