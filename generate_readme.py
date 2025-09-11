import os

def make_anchor(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-")

lines = ["# Project Structure\n"]

anchors = []

for root, dirs, files in os.walk(".", topdown=True):
    if root.startswith("./.git") or "__pycache__" in root:
        continue
    level = root.count(os.sep)
    indent = "  " * (level - 1)
    folder_name = os.path.basename(root) if root != "." else "📂 Root"
    anchor = make_anchor(root)
    lines.append(f"{indent}- [{folder_name}](#{anchor})")
    anchors.append((anchor, root))

for anchor, path in anchors:
    lines.append(f"\n## {path}\n")
    lines.append("*(здесь можно добавить описание)*\n")

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
