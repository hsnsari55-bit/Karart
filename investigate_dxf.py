#!/usr/bin/env python3

import ezdxf
import json

# Load the DXF file
dxf_path = r'C:/KaRar/data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf'
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

print("=== DXF INVESTIGATION REPORT ===\n")

# 1. List every layer name in the DXF
print("1. LAYERS IN DXF:")
layers = {}
for entity in msp:
    layer_name = entity.dxf.layer
    if layer_name not in layers:
        layers[layer_name] = []
    layers[layer_name].append(entity)

for layer_name, entities in sorted(layers.items()):
    print(f"   Layer '{layer_name}': {len(entities)} entities")

print(f"\nTotal layers: {len(layers)}")
print()

# 2. Count LINE, LWPOLYLINE, POLYLINE and ARC entities per layer
print("2. GEOMETRY TYPE COUNTS PER LAYER:")
geometry_counts = {}
for layer_name, entities in layers.items():
    counts = {'LINE': 0, 'LWPOLYLINE': 0, 'POLYLINE': 0, 'ARC': 0}
    for entity in entities:
        entity_type = entity.dxftype()
        if entity_type in counts:
            counts[entity_type] += 1
    geometry_counts[layer_name] = counts

for layer_name, counts in sorted(geometry_counts.items()):
    print(f"   Layer '{layer_name}':")
    for geom_type, count in counts.items():
        if count > 0:
            print(f"     {geom_type}: {count}")

print()

# 3. Find layers that may contain doors
print("3. POTENTIAL DOOR LAYERS:")
door_layer_candidates = []
for layer_name, entities in layers.items():
    # Check if layer name contains door-related keywords
    door_keywords = ['kapı', 'kapi', 'door', 'pencere', 'window', 'frame']
    layer_lower = layer_name.lower()
    
    has_door_geometry = False
    for entity in entities:
        if entity.dxftype() in ['LINE', 'LWPOLYLINE', 'ARC']:
            has_door_geometry = True
            break
    
    if any(keyword in layer_lower for keyword in door_keywords) or has_door_geometry:
        door_layer_candidates.append((layer_name, len(entities), has_door_geometry))
        print(f"   Candidate: '{layer_name}' ({len(entities)} entities, has door geometry: {has_door_geometry})")

print()

# 4. Explain why the current detector returns zero doors
print("4. ANALYSIS OF CURRENT DETECTOR ISSUES:")
print("   Current DOOR_LAYERS in detector:")
for layer in ['kapı', 'kapi', 'kapi___pencere', 'kapi ve pencereler', 'kapı ve pencereler', 'KAPI VE PENCERELER']:
    print(f"     - '{layer}'")

print("\n   Issues found:")
# Check if any of the door layer candidates match the detector's DOOR_LAYERS
found_match = False
for layer_name, _, _ in door_layer_candidates:
    for detector_layer in ['kapı', 'kapi', 'kapi___pencere', 'kapi ve pencereler', 'kapı ve pencereler', 'KAPI VE PENCERELER']:
        if layer_name.lower() == detector_layer.lower():
            found_match = True
            print(f"   ✓ Found matching layer: '{layer_name}'")
            break

if not found_match:
    print("   ✗ None of the door layer candidates match the detector's DOOR_LAYERS")
    print("   This is the primary reason for zero door detection!")

# Check geometry types
print("\n   Geometry type analysis:")
for layer_name, counts in geometry_counts.items():
    total_door_geom = counts['LINE'] + counts['LWPOLYLINE'] + counts['ARC']
    if total_door_geom > 0:
        print(f"   Layer '{layer_name}' has {total_door_geom} door geometries (LINE: {counts['LINE']}, LWPOLYLINE: {counts['LWPOLYLINE']}, ARC: {counts['ARC']})")

print()

# 5. Recommend the correct detection strategy
print("5. RECOMMENDED DETECTION STRATEGY:")
print("   Based on the investigation, the following changes are needed:")

# Find the actual door layer
actual_door_layer = None
for layer_name, _, has_door_geom in door_layer_candidates:
    if has_door_geom:
        actual_door_layer = layer_name
        break

if actual_door_layer:
    print(f"   1. Update DOOR_LAYERS to include: '{actual_door_layer}'")
    print(f"   2. The detector should also consider layers with door geometries even if layer name doesn't match keywords")
else:
    print("   1. No door geometries found in the DXF file")
    print("   2. May need to check if doors are stored in a different format or layer naming convention")

print("\n   Additional recommendations:")
print("   - Consider case-insensitive layer matching")
print("   - Add more door-related keywords to DOOR_LAYERS")
print("   - Log all entities for debugging")

print("\n=== END OF INVESTIGATION REPORT ===")