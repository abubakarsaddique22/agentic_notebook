"""
C.2 JSON Lines (.jsonl): AI datasets ka format
==============================================
Server ki zaroorat NAHI.
    python -m part_c_json.c2_jsonl

Theory: part_c_json/NOTES.md (C.2)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

dataset = [
    {"messages": [{"role": "user", "content": "COD hai?"},
                  {"role": "assistant", "content": "Ji haan, sirf COD."}]},
    {"messages": [{"role": "user", "content": "Delivery kab?"},
                  {"role": "assistant", "content": "Lahore mein 2 din."}]},
]

path = Path(__file__).parent / "train.jsonl"     # isi folder mein file banegi

# Likhna: har row ek line
with path.open("w", encoding="utf-8") as f:
    for row in dataset:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("File ka content:")
print(path.read_text(encoding="utf-8"))

# Parhna: line by line (bari file bhi memory mein poori load nahi hoti)
with path.open(encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        row = json.loads(line)
        print(i, "->", row["messages"][0]["content"])

print(f"\nFile yahan bani: {path}")
