#!/usr/bin/env python3

import ezdxf
import json

# Load the DXF file
dxf_path = r'C:/KaRar/data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf'
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

print("=== DXF SCALE ANALYSIS ===\n")

# Get all entities to understand the scale
all_entities = list(msp)
print(f"Total entities in DXF: {len(all_entities)}")

# Find entities with coordinates to understand scale
coordinates = []
for entity in all_entities:
    entity_type = entity.dxftype()
    if entity_type == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        coordinates.extend([start, end])
    elif entity_type == 'LWPOLYLINE':
        points = entity.get_points()
        coordinates.extend(points)
    elif entity_type == 'ARC':
        center = entity.dxf.center
        coordinates.append(center)

if coordinates:
    # Find min and max coordinates
    xs = [coord[0] for coord in coordinates]
    ys = [coord[1] for coord in coordinates]
    
    print(f"\nCoordinate ranges:")
    print(f"  X: {min(xs):.2f} to {max(xs):.2f} (range: {max(xs) - min(xs):.2f})")
    print(f"  Y: {min(ys):.2f} to {max(ys):.2f} (range: {max(ys) - min(ys):.2f})")
    
    # Calculate approximate scale
    # If we assume typical building dimensions, we can estimate the scale
    # For example, if a wall is 5 meters (5000mm) in real life
    # and appears as 50 units in DXF, then scale is 100:1 (100mm per unit)
    
    # Look at wall entities to estimate scale
    wall_entities = []
    for entity in all_entities:
        if entity.dxf.layer == 'Duvar':  # Wall layer
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                wall_entities.append((start, end))
    
    if wall_entities:
        print(f"\nWall entities found: {len(wall_entities)}")
        
        # Calculate average wall length
        lengths = []
        for start, end in wall_entities:
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            lengths.append(length)
        
        avg_length = sum(lengths) / len(lengths)
        print(f"Average wall length in DXF units: {avg_length:.2f}")
        
        # Estimate real-world wall length (typical room wall ~3000mm = 3m)
        estimated_real_length = 3000  # mm
        estimated_scale = estimated_real_length / avg_length
        print(f"Estimated scale: {estimated_scale:.2f} (mm per DXF unit)")
        
        # Convert door measurements to real-world scale
        print(f"\nDoor measurement scale conversion:")
        print(f"  Current MIN_DOOR_WIDTH: 200 DXF units")
        print(f"  Real-world equivalent: {200 * estimated_scale:.2f} mm")
        print(f"  Current MAX_DOOR_WIDTH: 1200 DXF units")
        print(f"  Real-world equivalent: {1200 * estimated_scale:.2f} mm")
        
        # Check what door widths we actually have
        door_layers = ['kapı', 'kapi', 'kapi___pencere', 'kapi ve pencereler', 'kapı ve pencereler', 'KAPI VE PENCERELER']
        door_entities = []
        
        for entity in all_entities:
            if entity.dxf.layer in door_layers:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    width = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
                    door_entities.append((entity.dxf.layer, entity.dxftype(), width))
                elif entity.dxftype() == 'ARC':
                    radius = entity.dxf.radius
                    door_entities.append((entity.dxf.layer, entity.dxftype(), radius))
        
        print(f"\nDoor entity measurements (DXF units):")
        for i, (layer, etype, value) in enumerate(door_entities[:10]):  # Show first 10
            print(f"  {i+1}. Layer '{layer}', {etype}: {value:.2f}")
        
        if len(door_entities) > 10:
            print(f"  ... and {len(door_entities) - 10} more")
        
        # Convert to real-world scale
        print(f"\nDoor entity measurements (real-world mm):")
        for i, (layer, etype, value) in enumerate(door_entities[:10]):
            real_value = value * estimated_scale
            print(f"  {i+1}. Layer '{layer}', {etype}: {real_value:.2f} mm")

print("\n=== END OF ANALYSIS ===")