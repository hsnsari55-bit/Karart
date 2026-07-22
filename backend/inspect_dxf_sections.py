filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

with open(filepath, "r", encoding="latin-1") as f:
    content = f.read()

# Search for ENTITIES
pos = content.find("ENTITIES")
if pos != -1:
    print(f"Found ENTITIES at pos {pos}")
    # Print context
    print(content[pos-100:pos+1000])
else:
    print("ENTITIES section not found in the raw text!")

# Also search for ENDSEC of the BLOCKS section
blocks_pos = content.find("BLOCKS")
if blocks_pos != -1:
    print(f"\nFound BLOCKS section at pos {blocks_pos}")
    # Let's search for the next "SECTION" or if the file ends without it
    next_sec = content.find("SECTION", blocks_pos + 10)
    if next_sec != -1:
        print(f"Next SECTION after BLOCKS is at pos {next_sec}")
        print(content[next_sec-100:next_sec+500])
    else:
        print("No other SECTION found after BLOCKS!")
