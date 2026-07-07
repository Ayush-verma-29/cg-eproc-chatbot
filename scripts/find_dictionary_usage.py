# scripts/find_dictionary_usage.py
from pathlib import Path

def search():
    root = Path(".")
    for path in root.glob("backend/**/*.py"):
        try:
            content = path.read_text(encoding="utf-8")
            if "procurement_dictionary" in content or "procurement_dict" in content:
                print(f"Found reference in: {path}")
        except Exception as e:
            pass

if __name__ == "__main__":
    search()
