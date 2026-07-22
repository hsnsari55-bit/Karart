import sys
from backend.dxf_parser import DXFParser

parser = DXFParser()
filepath = parser.path_manager.get_path('data', 'GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf')
encoding = parser._detect_encoding(filepath)
pairs = parser._parse_pairs(filepath, encoding=encoding)

target_blocks = {'90 lÄ±k kapÄ± 2', '80 lÄ±k kapÄ± 2'}
# Let's find all INSERTs of these blocks
inserts_found = []

in_block = False
block_name = None
in_entities = False
current_insert = None

for i in range(len(pairs)):
    c, v = pairs[i]
    if c == 0 and v == 'SECTION':
        if i+1 < len(pairs) and pairs[i+1][0] == 2 and pairs[i+1][1] == 'ENTITIES':
            in_entities = True
    elif in_entities and c == 0 and v == 'ENDSEC':
        in_entities = False
    elif c == 0 and v == 'BLOCK':
        in_block = True
        j = i + 1
        while j < len(pairs) and pairs[j][0] != 0:
            if pairs[j][0] == 2:
                block_name = pairs[j][1]
                break
            j += 1
    elif c == 0 and v == 'ENDBLK':
        in_block = False
        block_name = None
    elif c == 0 and v == 'INSERT':
        j = i + 1
        inserted_block = None
        while j < len(pairs) and pairs[j][0] != 0:
            if pairs[j][0] == 2:
                inserted_block = pairs[j][1]
                break
            j += 1
        
        if inserted_block in target_blocks:
            context = "ENTITIES" if in_entities else f"BLOCK {block_name}"
            inserts_found.append((context, inserted_block))

print(f"Total door block inserts found: {len(inserts_found)}")
for context, inserted_block in inserts_found:
    print(f"Inserted in {context}: {inserted_block}")

