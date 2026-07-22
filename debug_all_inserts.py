import sys
from backend.dxf_parser import DXFParser

parser = DXFParser()
filepath = parser.path_manager.get_path('data', 'GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf')
encoding = parser._detect_encoding(filepath)
pairs = parser._parse_pairs(filepath, encoding=encoding)

inserts = []
in_block = False
block_name = None

for i in range(len(pairs)):
    c, v = pairs[i]
    if c == 0 and v == 'BLOCK':
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
    elif c == 0 and v == 'INSERT' and in_block:
        j = i + 1
        inserted_block = None
        while j < len(pairs) and pairs[j][0] != 0:
            if pairs[j][0] == 2:
                inserted_block = pairs[j][1]
                break
            j += 1
        if 'kap' in inserted_block.lower() or 'kap' in inserted_block:
            inserts.append((block_name, inserted_block))

print("Blocks inserting kapı:", set(inserts))
