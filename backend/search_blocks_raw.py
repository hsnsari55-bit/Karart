with open("data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf", "r", encoding="latin-1") as f:
    content = f.read()

import re
# Block definitions usually look like:
#   0
# BLOCK
#   5
# <handle>
# ...
#   2
# <block_name>

blocks = []
pos = 0
while True:
    pos = content.find("BLOCK", pos)
    if pos == -1:
        break
    
    # Check if it's group code 0
    # Let's extract around this pos
    start = max(0, pos - 30)
    end = min(len(content), pos + 100)
    chunk = content[start:end]
    if "0\nBLOCK" in chunk or "0\r\nBLOCK" in chunk:
        # Let's find group code 2 (name) after this pos
        # Name is usually group code 2, which is "  2\n<name>"
        name_pos = content.find("\n  2\n", pos)
        if name_pos == -1 or name_pos > pos + 500:
            name_pos = content.find("\r\n  2\r\n", pos)
        if name_pos != -1 and name_pos < pos + 500:
            # extract name
            name_start = name_pos + 5 if content[name_pos] == '\n' else name_pos + 7
            # wait, let's be more precise
            name_chunk = content[name_pos:name_pos+100]
            lines = name_chunk.splitlines()
            if len(lines) >= 3:
                name = lines[2].strip()
                blocks.append((pos, name))
    pos += 5

print(f"Total BLOCKS found in raw content: {len(blocks)}")
print("First 20 blocks:")
for p, n in blocks[:20]:
    print(f"  Pos {p}: '{n}'")
print("\nLast 20 blocks:")
for p, n in blocks[-20:]:
    print(f"  Pos {p}: '{n}'")
