filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

with open(filepath, "r", encoding="latin-1") as f:
    content = f.read()

# Let's find some occurrences of "LINE" and see what is the closest SECTION above them.
import re

print("Searching for LINE occurrences:")
matches = [m.start() for m in re.finditer("LINE", content)]
print(f"Total occurrences of 'LINE': {len(matches)}")

# Let's take 3 sample positions and look backwards to find which SECTION they are in.
for idx, pos in enumerate(matches[:5]):
    # Find the nearest SECTION or ENDSEC or BLOCK before this pos
    sub_text = content[max(0, pos - 1000):pos + 200]
    print(f"\n--- Sample {idx} (pos {pos}) ---")
    # Let's print the last 200 chars and next 200 chars
    print(content[pos-300:pos+200])
