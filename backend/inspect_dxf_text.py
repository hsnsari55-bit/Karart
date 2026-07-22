filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

with open(filepath, "r", encoding="latin-1") as f:
    content = f.read()

print("Length of content character-wise:", len(content))

# Look for section markers
sections = []
pos = 0
while True:
    pos = content.find("SECTION", pos)
    if pos == -1:
        break
    # Find next line or lines
    start_idx = max(0, pos - 10)
    end_idx = min(len(content), pos + 100)
    sections.append((pos, content[start_idx:end_idx].replace('\n', '\\n')))
    pos += 7

print(f"\nFound {len(sections)} SECTION markers:")
for pos, sec in sections:
    print(f"  Pos {pos}: {sec}")

# Count occurrences of some key strings
keys = ['LINE', 'LWPOLYLINE', 'POLYLINE', 'INSERT', 'AcDbEntity', 'AcDbLine', 'AcDbPolyline']
print("\nOccurrences of key strings in raw content:")
for key in keys:
    print(f"  '{key}': {content.count(key)}")
