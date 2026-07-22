import sys
from backend.dxf_parser import DXFParser
import json

parser = DXFParser()
parser.parse("GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf")

layers = set([ent.get('layer', '') for ent in parser.entities])
print(f"Layers in parser entities: {layers}")
