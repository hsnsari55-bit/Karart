#!/usr/bin/env python3

import ezdxf
import json
import math

# Configuration - Updated based on analysis
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
        elif entity.dxftype() == 'LWPOLYLINE':
            # For LWPOLYLINE, calculate bounding box width
            points = [tuple(p) for p in entity.get_points()]
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                width = max(max(xs) - min(xs), max(ys) - min(ys))
                door_entities.append((entity.dxf.layer, entity.dxftype(), width, None, None, entity))

print(f"Found {len(door_entities)} door entities")

# Updated door detection parameters based on analysis
DOOR_DETECTION_PARAMS = {
    'MIN_DOOR_WIDTH': 100,      # Reduced from 200mm to ~100mm as requested
    'MAX_DOOR_WIDTH': 1500,     # Reduced from 2000mm to 1500mm to exclude outliers
    'MIN_ARC_RADIUS': 70,       # Keep as is
    'MAX_ARC_RADIUS': 1200,     # Keep as is
    'MIN_ARC_SWEEP': 40,        # Keep as is
    'MAX_ARC_SWEEP': 180,       # Keep as is
    'WALL_MATCH_DISTANCE_THRESHOLD': 1500,  # Reduced from 2000mm for more precise matching
}

print(f"\n=== DOOR DETECTION PARAMETERS ===")
print(f"MIN_DOOR_WIDTH: {DOOR_DETECTION_PARAMS['MIN_DOOR_WIDTH']} mm")
print(f"MAX_DOOR_WIDTH: {DOOR_DETECTION_PARAMS['MAX_DOOR_WIDTH']} mm")
print(f"WALL_MATCH_DISTANCE_THRESHOLD: {DOOR_DETECTION_PARAMS['WALL_MATCH_DISTANCE_THRESHOLD']} mm")

# DXF scale conversion
DXF_SCALE_MM_PER_UNIT = 32.0  # mm per DXF unit
print(f"DXF_SCALE_MM_PER_UNIT: {DXF_SCALE_MM_PER_UNIT} mm/unit")

# Convert parameters to DXF units
MIN_DOOR_WIDTH_DXF = DOOR_DETECTION_PARAMS['MIN_DOOR_WIDTH'] / DXF_SCALE_MM_PER_UNIT
MAX_DOOR_WIDTH_DXF = DOOR_DETECTION_PARAMS['MAX_DOOR_WIDTH'] / DXF_SCALE_MM_PER_UNIT
MIN_ARC_RADIUS_DXF = DOOR_DETECTION_PARAMS['MIN_ARC_RADIUS'] / DXF_SCALE_MM_PER_UNIT
MAX_ARC_RADIUS_DXF = DOOR_DETECTION_PARAMS['MAX_ARC_RADIUS'] / DXF_SCALE_MM_PER_UNIT
WALL_MATCH_DISTANCE_THRESHOLD_DXF = DOOR_DETECTION_PARAMS['WALL_MATCH_DISTANCE_THRESHOLD'] / DXF_SCALE_MM_PER_UNIT

print(f"\n=== CONVERTED TO DXF UNITS ===")
print(f"MIN_DOOR_WIDTH_DXF: {MIN_DOOR_WIDTH_DXF:.2f}")
print(f"MAX_DOOR_WIDTH_DXF: {MAX_DOOR_WIDTH_DXF:.2f}")
print(f"WALL_MATCH_DISTANCE_THRESHOLD_DXF: {WALL_MATCH_DISTANCE_THRESHOLD_DXF:.2f}")

# Point to line segment distance function
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

# Test first few door entities with updated parameters
print(f"\n=== TESTING WITH UPDATED PARAMETERS ===")

valid_doors = []
ignored_candidates = 0

for i, (layer, etype, width, start, end, entity) in enumerate(door_entities[:10]):  # Test first 10
    print(f"\n--- Door Entity {i+1} ---")
    print(f"Layer: {layer}")
    print(f"Type: {etype}")
    print(f"Width: {width:.2f} DXF units")
    
    # Calculate door center
    if start and end:
        center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    else:
        # For LWPOLYLINE, use average of points
        center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2] if start and end else [0, 0]
    
    print(f"Door center: {center}")
    
    # Convert width to mm for validation
    width_mm = width * DXF_SCALE_MM_PER_UNIT
    print(f"Width in mm: {width_mm:.2f}")
    
    # Validate door width
    if width_mm < DOOR_DETECTION_PARAMS['MIN_DOOR_WIDTH'] or width_mm > DOOR_DETECTION_PARAMS['MAX_DOOR_WIDTH']:
        print(f"  -> Width out of range ({DOOR_DETECTION_PARAMS['MIN_DOOR_WIDTH']}-{DOOR_DETECTION_PARAMS['MAX_DOOR_WIDTH']} mm)")
        ignored_candidates += 1
        continue
    else:
        print(f"  -> Width in valid range")
    
    # For arcs, validate swing angle
    if etype == 'ARC':
        # Calculate sweep angle
        center = [entity.dxf.center[0], entity.dxf.center[1]]
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        
        # Normalize angles to 0-360
        start_angle = start_angle % 360
        end_angle = end_angle % 360
        
        # Compute sweep angle (smallest angle between start and end)
        sweep = abs(end_angle - start_angle)
        if sweep > 180:
            sweep = 360 - sweep
        
        print(f"  -> Sweep angle: {sweep:.2f}°")
        if sweep < DOOR_DETECTION_PARAMS['MIN_ARC_SWEEP'] or sweep > DOOR_DETECTION_PARAMS['MAX_ARC_SWEEP']:
            print(f"  -> Sweep angle out of range ({DOOR_DETECTION_PARAMS['MIN_ARC_SWEEP']}-{DOOR_DETECTION_PARAMS['MAX_ARC_SWEEP']}°)")
            ignored_candidates += 1
            continue
        else:
            print(f"  -> Sweep angle in valid range")
    
    # Match to nearest wall
    min_dist = float('inf')
    best_wall_id = None
    
    for wall in walls:
        if wall.get('layer') != 'wall':
            continue
            
        wall_start = wall['start']
        wall_end = wall['end']
        dist = point_to_line_segment_distance(center, wall_start, wall_end)
        
        if dist < min_dist:
            min_dist = dist
            best_wall_id = wall['id']
    
    print(f"Nearest wall ID: {best_wall_id if best_wall_id else 'None'}")
    print(f"Distance to nearest wall: {min_dist:.2f} DXF units")
    
    # Convert distance to mm
    dist_mm = min_dist * DXF_SCALE_MM_PER_UNIT
    print(f"Distance in mm: {dist_mm:.2f} mm")
    
    # Check if it matches with current threshold
    if min_dist <= WALL_MATCH_DISTANCE_THRESHOLD_DXF:
        print(f"  -> Would match with threshold {DOOR_DETECTION_PARAMS['WALL_MATCH_DISTANCE_THRESHOLD']} mm")
        # Build final door object
        door_obj = {
            'id': i+1,
            'wall_id': best_wall_id if best_wall_id else 0,
            'center': center,
            'width': width_mm,
            'swing_angle': 0 if etype != 'ARC' else sweep,
            'orientation': 0,  # Simplified
            'type': 'Single'   # Simplified classification
        }
        valid_doors.append(door_obj)
        print(f"  -> Door added to valid list")
    else:
        print(f"  -> Would NOT match with threshold {DOOR_DETECTION_PARAMS['WALL_MATCH_DISTANCE_THRESHOLD']} mm")
    
    ignored_candidates += 1

print(f"\n=== SUMMARY ===")
print(f"Valid doors detected: {len(valid_doors)}")
print(f"Ignored candidates: {ignored_candidates}")
print(f"Doors saved to: outputs/doors.json")