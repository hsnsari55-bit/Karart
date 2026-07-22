import os
import ezdxf

filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"
repaired_path = "data/guzelce_repaired.dxf"

with open(filepath, "r", encoding="latin-1") as f:
    content = f.read()

# Let's clean trailing incomplete line if any
lines = content.splitlines()
# If the last line is incomplete (e.g., doesn't end with a newline or is a partial number), we can drop it to be safe
if len(lines[-1].strip()) < 2:
    lines = lines[:-1]

rebuilt_content = "\n".join(lines) + "\n"

# Add standard DXF terminations
# Since we are in the BLOCKS section, let's terminate the active block and then the SECTION
rebuilt_content += "  0\nENDBLK\n"
rebuilt_content += "  0\nENDSEC\n"

# Let's open an empty ENTITIES section to satisfy ezdxf requirements
rebuilt_content += "  0\nSECTION\n  2\nENTITIES\n  0\nENDSEC\n"
rebuilt_content += "  0\nEOF\n"

with open(repaired_path, "w", encoding="latin-1") as f:
    f.write(rebuilt_content)

print(f"Repaired DXF written to {repaired_path}")
print("Testing repaired file with ezdxf...")

try:
    doc = ezdxf.readfile(repaired_path)
    print("SUCCESS! Repaired file loaded successfully without errors!")
    print(f"Database entities count: {len(doc.entitydb)}")
    print(f"Modelspace entities: {len(doc.modelspace())}")
    
    # List blocks
    print(f"Total blocks in repaired file: {len(doc.blocks)}")
    non_empty_blocks = [b for b in doc.blocks if len(b) > 0]
    print(f"Non-empty blocks count: {len(non_empty_blocks)}")
    for b in non_empty_blocks[:10]:
        print(f"  - Block '{b.name}' has {len(b)} entities")
        
except Exception as e:
    print(f"Standard load failed: {e}. Trying recover mode on repaired file...")
    try:
        from ezdxf import recover
        doc, auditor = recover.readfile(repaired_path)
        print(f"Recover load successful. Auditor errors: {len(auditor.errors)}")
        print(f"Modelspace entities: {len(doc.modelspace())}")
        non_empty_blocks = [b for b in doc.blocks if len(b) > 0]
        print(f"Non-empty blocks count: {len(non_empty_blocks)}")
        for b in non_empty_blocks[:10]:
            print(f"  - Block '{b.name}' has {len(b)} entities")
    except Exception as e2:
        print(f"All load attempts failed: {e2}")
