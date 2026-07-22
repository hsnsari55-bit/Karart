filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

with open(filepath, "r", encoding="latin-1") as f:
    content = f.read()

# Find occurrences of "*Model_Space"
pos = 0
while True:
    pos = content.find("*Model_Space", pos)
    if pos == -1:
        break
    print(f"\nFound '*Model_Space' at pos {pos}")
    # Print the next 1000 characters
    print(content[pos-100:pos+1200])
    pos += 12
