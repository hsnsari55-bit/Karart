import sys
from backend.dxf_parser import DXFParser

parser = DXFParser()
filepath = parser.path_manager.get_path('data', 'GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf')
encoding = parser._detect_encoding(filepath)
pairs = parser._parse_pairs(filepath, encoding=encoding)

types = []
in_kap = False
current_type = None

for c, v in pairs:
    if c == 0:
        current_type = v
    if c == 8 and ('kap' in v.lower() or 'kap' in v):
        types.append(current_type)

print(set(types))
