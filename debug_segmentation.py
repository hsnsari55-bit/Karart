"""
Debug script to analyze segmentation results and layer information.
"""

import json
from collections import Counter

# Load segmentation data
with open('outputs/drawing_segmentation.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entities: {data['total_entities']}")
print(f"Total regions: {data['total_regions']}")
print(f"Proximity threshold: {data['proximity_threshold']}")
print()

# Analyze each region
for i, region in enumerate(data['regions'], 1):
    print(f"Region {i}: {region['type']}")
    print(f"  Entities: {region['entity_count']}")
    print(f"  Bounds: X[{region['bounds']['min_x']:.1f}, {region['bounds']['max_x']:.1f}]")
    print(f"  Bounds: Y[{region['bounds']['min_y']:.1f}, {region['bounds']['max_y']:.1f}]")
    print(f"  Size: {region['width']:.1f} × {region['height']:.1f}")
    print(f"  Aspect ratio: {region['width'] / region['height']:.2f}")
    print()

# Now let's check the actual DXF to see layer distribution
import ezdxf

dxf_path = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# Count entities by layer
layer_counts = Counter()
for entity in msp:
    if entity.dxftype() in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE"):
        layer_counts[entity.dxf.layer] += 1

print("Top 20 layers by entity count:")
for layer, count in layer_counts.most_common(20):
    print(f"  {layer}: {count}")
