#!/usr/bin/env python3

import ezdxf
import json
import math

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

# Test wall matching for first few door entities
print("\n=== TESTING WALL MATCHING ===")

# Define point_to_line_segment_distance function
def point_to_line_segment_distance(point, line_start, line_end):
    """Calculate the shortest distance from a point to a line segment."""
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Vector from line start to end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        # Line segment is a point
        return math.dist(point, line_start)
    
    # Parameter t for projection of point onto line
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))  # Clamp to line segment
    
    # Projection point
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    
    return math.dist(point, [proj_x, proj_y])

# Test first 5 door entities
for i, (layer, etype, width, start, end, entity) in enumerate(door_entities[:5]):
    print(f"\n--- Door Entity {i+1} ---")
    print(f"Layer: {layer}")
    print(f"Type: {etype}")
    print(f"Width: {width:.2f} DXF units")
    
    # Calculate door center
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    print(f"Door center: {center}")
    
    # Find nearest wall
    min_dist = float('inf')
    best_wall = None
    
    for wall in walls:
        if wall.get('layer') != 'wall':
            continue
            
        wall_start = wall['start']
        wall_end = wall['end']
        dist = point_to_line_segment_distance(center, wall_start, wall_end)
        
        if dist < min_dist:
            min_dist = dist
            best_wall = wall
    
    print(f"Nearest wall ID: {best_wall['id'] if best_wall else 'None'}")
    print(f"Distance to nearest wall: {min_dist:.2f} DXF units")
    
    # Convert to mm
    dxf_scale = 32.0  # mm per DXF unit
    dist_mm = min_dist * dxf_scale
    print(f"Distance in mm: {dist_mm:.2f} mm")
    
    # Check if it matches with current threshold
    wall_match_threshold = 1000  # mm
    if min_dist <= (wall_match_threshold / dxf_scale):
        print(f"[MATCH] Would match with threshold {wall_match_threshold} mm")
    else:
        print(f"[NO MATCH] Would NOT match with threshold {wall_match_threshold} mm")

# Check coordinate system compatibility
print("\n=== COORDINATE SYSTEM COMPATIBILITY ===")

# Get some wall coordinates from walls.json
wall_coords = []
for wall in walls[:10]:  # First 10 walls
    wall_coords.append(wall['start'])
    wall_coords.append(wall['end'])

# Get some door coordinates from DXF
door_coords = []
for i, (layer, etype, width, start, end, entity) in enumerate(door_entities[:10]):
    door_coords.append(start)
    door_coords.append(end)

print(f"Wall coordinates range:")
wall_xs = [c[0] for c in wall_coords]
wall_ys = [c[1] for c in wall_coords]
print(f"  X: {min(wall_xs):.2f} to {max(wall_xs):.2f}")
print(f"  Y: {min(wall_ys):.2f} to {max(wall_ys):.2f}")

print(f"\nDoor coordinates range:")
door_xs = [c[0] for c in door_coords]
door_ys = [c[1] for c in door_coords]
print(f"  X: {min(door_xs):.2f} to {max(door_xs):.2f}")
print(f"  Y: {min(door_ys):.2f} to {max(door_ys):.2f}")

# Check if they overlap
x_overlap = not (max(wall_xs) < min(door_xs) or max(door_xs) < min(wall_xs))
y_overlap = not (max(wall_ys) < min(door_ys) or max(door_ys) < min(wall_ys))
print(f"\nCoordinate overlap:")
print(f"  X overlap: {x_overlap}")
print(f"  Y overlap: {y_overlap}")

if x_overlap and y_overlap:
    print("[MATCH] Coordinates appear to be in the same system")
else:
    print("[NO MATCH] Coordinates may be in different systems")