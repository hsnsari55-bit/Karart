with open("data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf", "r", encoding="latin-1") as f:
    content = f.read()

import re

# find all occurrences of BLOCK followed by a name
# We can search for block names containing certain keywords
import urllib.parse

# Let's search for keywords like PLAN, KAT, BLOK, 467, PARSEL, ADA in the block names we parsed
from collections import Counter

# Let's use the code from search_blocks_raw.py to extract all block names
blocks = []
pos = 0
while True:
    pos = content.find("BLOCK", pos)
    if pos == -1:
        break
    
    # Check if it's group code 0
    start = max(0, pos - 30)
    end = min(len(content), pos + 100)
    chunk = content[start:end]
    if "0\nBLOCK" in chunk or "0\r\nBLOCK" in chunk:
        name_pos = content.find("\n  2\n", pos)
        if name_pos == -1 or name_pos > pos + 500:
            name_pos = content.find("\r\n  2\r\n", pos)
        if name_pos != -1 and name_pos < pos + 500:
            name_chunk = content[name_pos:name_pos+100]
            lines = name_chunk.splitlines()
            if len(lines) >= 3:
                name = lines[2].strip()
                blocks.append((pos, name))
    pos += 5

print("Filtered block names:")
keywords = ["BLOK", "PLAN", "KAT", "PARSEL", "ADA", "MIMARI"]
for pos, name in blocks:
    name_upper = name.upper()
    if any(kw in name_upper for kw in keywords):
        print(f"  Pos {pos}: '{name}'")
