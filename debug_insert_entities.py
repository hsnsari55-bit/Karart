import sys
from backend.dxf_parser import DXFParser

parser = DXFParser()
filepath = parser.path_manager.get_path('data', 'GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf')
encoding = parser._detect_encoding(filepath)
pairs = parser._parse_pairs(filepath, encoding=encoding)

inserts = []
in_entities = False
for i in range(len(pairs)):
    c, v = pairs[i]
    if c == 0 and v == 'SECTION' and pairs[i+1][0] == 2 and pairs[i+1][1] == 'ENTITIES':
        in_entities = True
    elif in_entities and c == 0 and v == 'ENDSEC':
        in_entities = False
    elif in_entities and c == 0 and v == 'INSERT':
        j = i + 1
        inserted_block = None
        while j < len(pairs) and pairs[j][0] != 0:
            if pairs[j][0] == 2:
                inserted_block = pairs[j][1]
                break
            j += 1
        inserts.append(inserted_block)

print("Inserts in ENTITIES:", set(inserts))
