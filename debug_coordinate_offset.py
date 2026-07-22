#!/usr/bin/env python3

import ezdxf
import json

# Configuration
DXF_PATH = r'C:/KaRar/data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf'
WALLS_PATH = r'C:/KaRar/outputs/walls.json'

# Load walls
with open(WALLS_PATH, 'r', encoding='utf-8') as f:
    walls = json.load(f)

print(f"Loaded {len(walls)} walls")

# Load DXF
doc = ezdxf.readfile(DXF_PATH)
msp = doc.modelspace()

# Get door entities
door_layers = ['kapı', 'kapi', 'kapi___pencere', 'kapi ve pencereler', 'kapı ve pencereler', 'KAPI VE PENCERELER']
door_entities = []

for entity in msp:
    if entity.dxf.layer in door_layers:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            width = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            door_entities.append((entity.dxf.layer, entity.dxftype(), width, start, end, entity))

print(f"Found {len(door_entities)} door entities")

# Calculate coordinate offsets
print("\n=== COORDINATE OFFSET ANALYSIS ===")

# Get average wall coordinates
wall_xs = []
wall_ys = []
for wall in walls:
    wall_xs.extend([wall['start'][0], wall['end'][0]])
    wall_ys.extend([wall['start'][1], wall['end'][1]])

wall_x_avg = sum(wall_xs) / len(wall_xs)
wall_y_avg = sum(wall_ys) / len(wall_ys)

print(f"Average wall coordinates: ({wall_x_avg:.2f}, {wall_y_avg:.2f})")

# Get average door coordinates
door_xs = []
door_ys = []
for i, (layer, etype, width, start, end, entity) in enumerate(door_entities[:20]):  # First 20
    door_xs.extend([start[0], end[0]])
    door_ys.extend([start[1], end[1]])

door_x_avg = sum(door_xs) / len(door_xs)
door_y_avg = sum(door_ys) / len(door_ys)

print(f"Average door coordinates (first 20): ({door_x_avg:.2f}, {door_y_avg:.2f})")

# Calculate offset
offset_x = wall_x_avg - door_x_avg
offset_y = wall_y_avg - door_y_avg

print(f"\nCalculated offset: dx={offset_x:.2f}, dy={offset_y:.2f}")

# Test if applying this offset makes coordinates match
print("\n=== TESTING OFFSET CORRECTION ===")

# Apply offset to door coordinates
door_xs_offset = [x + offset_x for x in door_xs]
door_ys_offset = [y + offset_y for y in door_ys]

# Check overlap
wall_xs_offset = [x + offset_x for x in wall_xs]
wall_ys_offset = [y + offset_y for y in wall_ys]

x_overlap = not (max(wall_xs_offset) < min(door_xs_offset) or max(door_xs_offset) < min(wall_xs_offset))
y_overlap = not (max(wall_ys_offset) < min(door_ys_offset) or max(door_ys_offset) < min(wall_ys_offset))

print(f"After offset correction:")
print(f"  Wall X range: {min(wall_xs_offset):.2f} to {max(wall_xs_offset):.2f}")
print(f"  Door X range: {min(door_xs_offset):.2f} to {max(door_xs_offset):.2f}")
print(f"  Wall Y range: {min(wall_ys_offset):.2f} to {max(wall_ys_offset):.2f}")
print(f"  Door Y range: {min(door_ys_offset):.2f} to {max(door_ys_offset):.2f}")
print(f"  X overlap: {x_overlap}")
print(f"  Y overlap: {y_overlap}")

if x_overlap and y_overlap:
    print("✓ Offset correction makes coordinates compatible!")
else:
    print("✗ Offset correction still doesn't make coordinates compatible")

# Also check if walls have layer information
print(f"\n=== WALL LAYER ANALYSIS ===")
wall_layers = set()
for wall in walls:
    wall_layers.add(wall.get('layer', 'NO_LAYER'))

print(f"Wall layers found: {wall_layers}")

# Check if walls.json has the same structure as expected
print(f"\n=== WALLS.JSON STRUCTURE ===")
if walls:
    print(f"First wall keys: {list(walls[0].keys())}")
    print(f"First wall sample: {walls[0]}")