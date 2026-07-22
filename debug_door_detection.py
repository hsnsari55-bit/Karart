#!/usr/bin/env python3

import ezdxf
import json
import math

# Configuration
DXF_PATH = r'C:/KaRar/data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf'
WALLS_PATH = r'C:/KaRar/outputs/walls.json'
ROOMS_PATH = r'C:/KaRar/outputs/rooms.json'

# Door layers to consider
DOOR_LAYERS = [
    'kapı', 'kapi', 'kapi___pencere', 'kapi ve pencereler', 'kapı ve pencereler',
    'KAPI VE PENCERELER'
]

# Geometry types to consider
GEOMETRY_TYPES = ['LINE', 'LWPOLYLINE', 'ARC']

# Door detection parameters
MIN_DOOR_WIDTH = 200   # Minimum door width in mm
MAX_DOOR_WIDTH = 1200  # Maximum door width in mm
MIN_ARC_RADIUS = 200   # Minimum arc radius for door swing (mm)
MAX_ARC_RADIUS = 1200  # Maximum arc radius for door swing (mm)
MIN_ARC_SWEEP = 70     # Minimum sweep angle for door arc (degrees)
MAX_ARC_SWEEP = 110    # Maximum sweep angle for door arc (degrees)
WALL_MATCH_DISTANCE_THRESHOLD = 500  # Maximum distance to consider a wall match (mm)

def debug_layer_matching():
    """Debug layer matching between DXF and detector."""
    print("=== DEBUG: Layer Matching ===")
    
    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()
    
    # Get all layers from DXF
    dxf_layers = set()
    for entity in msp:
        dxf_layers.add(entity.dxf.layer)
    
    print(f"DXF layers found: {sorted(dxf_layers)}")
    print(f"\nDOOR_LAYERS in detector: {DOOR_LAYERS}")
    
    # Check for matches
    print("\nLayer matching analysis:")
    for detector_layer in DOOR_LAYERS:
        found = False
        for dxf_layer in dxf_layers:
            if detector_layer.lower() == dxf_layer.lower():
                print(f"  [MATCH] '{detector_layer}' == '{dxf_layer}'")
                found = True
                break
        if not found:
            print(f"  [NO MATCH] '{detector_layer}'")
    
    # Check for case-insensitive matches
    print("\nCase-insensitive matching:")
    for detector_layer in DOOR_LAYERS:
        for dxf_layer in dxf_layers:
            if detector_layer.lower() == dxf_layer.lower():
                print(f"  [MATCH] '{detector_layer}' == '{dxf_layer}'")

def debug_geometry_extraction():
    """Debug geometry extraction from DXF."""
    print("\n=== DEBUG: Geometry Extraction ===")
    
    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()
    
    # Count entities by layer and type
    layer_stats = {}
    for entity in msp:
        layer = entity.dxf.layer
        entity_type = entity.dxftype()
        
        if layer not in layer_stats:
            layer_stats[layer] = {'LINE': 0, 'LWPOLYLINE': 0, 'ARC': 0, 'OTHER': 0}
        
        if entity_type in layer_stats[layer]:
            layer_stats[layer][entity_type] += 1
        else:
            layer_stats[layer]['OTHER'] += 1
    
    print("Entities by layer and type:")
    for layer, counts in sorted(layer_stats.items()):
        if any(counts[geom] > 0 for geom in ['LINE', 'LWPOLYLINE', 'ARC']):
            print(f"  Layer '{layer}':")
            for geom_type, count in counts.items():
                if count > 0:
                    print(f"    {geom_type}: {count}")

def debug_walls_loading():
    """Debug walls loading from JSON."""
    print("\n=== DEBUG: Walls Loading ===")
    
    try:
        with open(WALLS_PATH, 'r', encoding='utf-8') as f:
            walls = json.load(f)
        
        print(f"Loaded {len(walls)} walls from {WALLS_PATH}")
        
        # Check wall structure
        if walls:
            print("\nFirst wall structure:")
            first_wall = walls[0]
            print(f"  Keys: {list(first_wall.keys())}")
            print(f"  Sample values:")
            for key, value in first_wall.items():
                if key in ['id', 'layer']:
                    print(f"    {key}: {value}")
                elif key in ['start', 'end']:
                    print(f"    {key}: {value}")
        
        # Count walls by layer
        wall_layers = {}
        for wall in walls:
            layer = wall.get('layer', 'unknown')
            wall_layers[layer] = wall_layers.get(layer, 0) + 1
        
        print(f"\nWalls by layer: {wall_layers}")
        
    except Exception as e:
        print(f"Error loading walls: {e}")

def debug_rooms_loading():
    """Debug rooms loading from JSON."""
    print("\n=== DEBUG: Rooms Loading ===")
    
    try:
        with open(ROOMS_PATH, 'r', encoding='utf-8') as f:
            rooms = json.load(f)
        
        print(f"Loaded {len(rooms)} rooms from {ROOMS_PATH}")
        
        # Check room structure
        if rooms:
            print("\nFirst room structure:")
            first_room = rooms[0]
            print(f"  Keys: {list(first_room.keys())}")
            print(f"  Sample values:")
            for key, value in first_room.items():
                if key in ['id', 'center']:
                    print(f"    {key}: {value}")
                elif key == 'boundary':
                    print(f"    {key}: {len(value)} points")
        
    except Exception as e:
        print(f"Error loading rooms: {e}")

def debug_door_processing():
    """Debug door entity processing."""
    print("\n=== DEBUG: Door Entity Processing ===")
    
    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()
    
    # Get door entities
    door_entities = []
    for entity in msp:
        if entity.dxf.layer not in DOOR_LAYERS:
            continue
        if entity.dxftype() not in GEOMETRY_TYPES:
            continue
        door_entities.append(entity)
    
    print(f"Found {len(door_entities)} raw door candidates")
    
    # Process first few entities to debug
    for i, entity in enumerate(door_entities[:5]):
        print(f"\nEntity {i+1}:")
        print(f"  Layer: {entity.dxf.layer}")
        print(f"  Type: {entity.dxftype()}")
        
        try:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                width = math.dist(start, end)
                print(f"  LINE: start={start}, end={end}, width={width:.2f}")
                print(f"  Width in range? {MIN_DOOR_WIDTH} <= {width:.2f} <= {MAX_DOOR_WIDTH}")
                
            elif entity.dxftype() == 'LWPOLYLINE':
                points = [tuple(p) for p in entity.get_points()]
                if points:
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    width = max(xs) - min(xs)
                    height = max(ys) - min(ys)
                    width = max(width, height)
                    print(f"  LWPOLYLINE: {len(points)} points, width={width:.2f}")
                    print(f"  Width in range? {MIN_DOOR_WIDTH} <= {width:.2f} <= {MAX_DOOR_WIDTH}")
                
            elif entity.dxftype() == 'ARC':
                center = [entity.dxf.center[0], entity.dxf.center[1]]
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle % 360
                end_angle = entity.dxf.end_angle % 360
                sweep = abs(end_angle - start_angle)
                if sweep > 180:
                    sweep = 360 - sweep
                print(f"  ARC: center={center}, radius={radius}, sweep={sweep:.2f}")
                print(f"  Radius in range? {MIN_ARC_RADIUS} <= {radius} <= {MAX_ARC_RADIUS}")
                print(f"  Sweep in range? {MIN_ARC_SWEEP} <= {sweep:.2f} <= {MAX_ARC_SWEEP}")
                
        except Exception as e:
            print(f"  Error processing entity: {e}")

def main():
    print("=== DOOR DETECTION DEBUG ===\n")
    
    debug_layer_matching()
    debug_geometry_extraction()
    debug_walls_loading()
    debug_rooms_loading()
    debug_door_processing()
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == '__main__':
    main()