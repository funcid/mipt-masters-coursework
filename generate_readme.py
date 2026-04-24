import os
import urllib.parse
import configparser

EXCLUDE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "node_modules"}
EXCLUDE_FILES = {"README.md"}
INCLUDE_EXTS = {".md", ".ipynb", ".java", ".kt", ".py"}

def load_submodules() -> dict[str, str]:
    """Загружает информацию о submodule'ах из .gitmodules"""
    submodules = {}
    if os.path.exists(".gitmodules"):
        try:
            config = configparser.ConfigParser()
            # ConfigParser требует, чтобы секции были в квадратных скобках
            # .gitmodules использует формат [submodule "path"], что configparser понимает
            config.read(".gitmodules", encoding="utf-8")
            for section in config.sections():
                if "path" in config[section] and "url" in config[section]:
                    path = config[section]["path"].strip()
                    url = config[section]["url"].strip()
                    submodules[path] = url
        except Exception:
            # Если configparser не справился, парсим вручную
            with open(".gitmodules", "r", encoding="utf-8") as f:
                current_path = None
                current_url = None
                for line in f:
                    line = line.strip()
                    if line.startswith("[submodule"):
                        # Сохраняем предыдущий submodule, если есть
                        if current_path and current_url:
                            submodules[current_path] = current_url
                        current_path = None
                        current_url = None
                    elif line.startswith("path ="):
                        current_path = line.split("=", 1)[1].strip()
                    elif line.startswith("url ="):
                        current_url = line.split("=", 1)[1].strip()
                # Сохраняем последний submodule
                if current_path and current_url:
                    submodules[current_path] = current_url
    return submodules

def is_submodule(dir_path: str) -> bool:
    """Проверяет, является ли директория submodule'ом"""
    git_file = os.path.join(dir_path, ".git")
    return os.path.isfile(git_file)

submodules = load_submodules()

def tree(dir_path: str, level: int = 0) -> list[str]:
    entries = [e for e in os.listdir(dir_path) if not e.startswith(".")]
    entries = [e for e in entries if e not in EXCLUDE_DIRS]
    entries = sorted(entries, key=lambda x: (os.path.isdir(os.path.join(dir_path, x)), x.lower()))

    lines = []
    for entry in entries:
        path = os.path.join(dir_path, entry)
        rel_path = os.path.relpath(path, ".").replace("\\", "/")

        if os.path.isdir(path):
            # Проверяем, является ли это submodule'ом
            is_sub = is_submodule(path) or rel_path in submodules
            sub_url = submodules.get(rel_path, None)
            
            if is_sub:
                # Для submodule'ов показываем только название и ссылку, без рекурсии
                indent = "  " * level
                link = f"[{entry}]({urllib.parse.quote(rel_path)})"
                if sub_url:
                    lines.append(f"{indent}- {link} 🔗 [submodule]({sub_url})")
                else:
                    lines.append(f"{indent}- {link} 🔗 [submodule]")
            else:
                # Для обычных папок делаем рекурсивный обход
                children = tree(path, level + 1)
                if children:  # Показываем только если есть содержимое
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
