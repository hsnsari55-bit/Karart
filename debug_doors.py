import sys
from backend.dxf_parser import DXFParser
import json

parser = DXFParser()
parser.parse("GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf")

doors = [ent for ent in parser.entities if 'kap' in ent.get('layer', '').lower()]
print(f"Total doors found: {len(doors)}")
for d in doors:
    print(d['type'], d.get('layer'), d.get('block_name'))
