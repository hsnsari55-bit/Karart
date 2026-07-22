import sys
from backend.dxf_parser import DXFParser

parser = DXFParser()
filepath = parser.path_manager.get_path('data', 'GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf')
encoding = parser._detect_encoding(filepath)
pairs = parser._parse_pairs(filepath, encoding=encoding)

doors = []
in_block = False
block_name = None
in_entities = False

for i in range(len(pairs)):
    c, v = pairs[i]
    if c == 0 and v == 'SECTION' and pairs[i+1][0] == 2 and pairs[i+1][1] == 'ENTITIES':
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
    elif c == 8 and ('kap' in v.lower() or 'kap' in v):
        doors.append(block_name)

print("Kapı layer blocks:", set(doors))
