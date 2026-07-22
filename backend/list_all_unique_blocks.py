with open("data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf", "r", encoding="latin-1") as f:
    content = f.read()

import re

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
                blocks.append(name)
    pos += 5

from collections import Counter
unique_blocks = Counter(blocks)
print(f"Unique blocks: {len(unique_blocks)}")
for n, c in unique_blocks.most_common():
    print(f"  '{n}': {c} occurrences")
