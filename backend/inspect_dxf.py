import os
import sys
import ezdxf
from ezdxf import recover
from collections import Counter

filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

try:
    doc, auditor = recover.readfile(filepath)
    print(f"Total database entities: {len(doc.entitydb)}")
    
    # Let's inspect all entities in the database that are geometry types
    geom_entities = []
    for ent in doc.entitydb.values():
        dxftype = ent.dxftype()
        if dxftype in ['LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'SPLINE', 'INSERT']:
            geom_entities.append(ent)
            
    print(f"\nFound {len(geom_entities)} total geometric entities in DB.")
    
    # Check their layers
    layers = Counter()
    for ent in geom_entities:
        layers[ent.dxf.layer if hasattr(ent.dxf, 'layer') else '0'] += 1
        
    print("\nGeometric entities by layer:")
    for layer, count in layers.most_common(20):
        print(f"  Layer '{layer}': {count} entities")
        
    # Check sample LINE entities
    line_samples = [ent for ent in geom_entities if ent.dxftype() == 'LINE']
    print(f"\nTotal LINE entities in DB: {len(line_samples)}")
    if line_samples:
        print("Sample lines:")
        for idx, ent in enumerate(line_samples[:5]):
            print(f"  Line {idx}: layer={ent.dxf.layer}, start={ent.dxf.start}, end={ent.dxf.end}")
            
except Exception as e:
    print(f"Error: {e}")
