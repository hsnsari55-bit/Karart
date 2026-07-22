import ezdxf
from ezdxf import recover

filepath = "data/guzelce_repaired.dxf"
doc, auditor = recover.readfile(filepath)

print("Listing all non-empty blocks:")
non_empty_blocks = [b for b in doc.blocks if len(b) > 0]
non_empty_blocks.sort(key=lambda b: len(b), reverse=True)

for idx, b in enumerate(non_empty_blocks, 1):
    print(f"  [{idx:02d}] Block '{b.name}': {len(b)} entities")
    # Let's count entity types inside this block
    from collections import Counter
    types = Counter(ent.dxftype() for ent in b)
    print(f"       Types: {dict(types)}")
