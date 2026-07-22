#!/usr/bin/env python3
"""
Sprint 1 Final Validation - Visual Overlay Generator
Generates an SVG overlay showing detected elements on the original DXF
"""

import json
import ezdxf
from pathlib import Path

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_bounds(walls, doors, windows, rooms):
    """Calculate bounding box for all elements"""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    # Check walls
    for wall in walls:
        for point in [wall['start'], wall['end']]:
            min_x = min(min_x, point[0])
            min_y = min(min_y, point[1])
            max_x = max(max_x, point[0])
            max_y = max(max_y, point[1])
    
    # Check doors
    for door in doors:
        if 'start' in door and 'end' in door:
            for point in [door['start'], door['end']]:
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])
    
    # Check windows
    for window in windows:
        if 'start' in window and 'end' in window:
            for point in [window['start'], window['end']]:
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])
    
    # Check rooms
    for room in rooms:
        for point in room['polygon']:
            min_x = min(min_x, point[0])
            min_y = min(min_y, point[1])
            max_x = max(max_x, point[0])
            max_y = max(max_y, point[1])
    
    return min_x, min_y, max_x, max_y

def generate_svg(dxf_path, walls, doors, windows, rooms, output_path):
    """Generate SVG with all layers"""
    
    # Get bounds
    min_x, min_y, max_x, max_y = get_bounds(walls, doors, windows, rooms)
    
    # Add padding
    padding = 100
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding
    
    width = max_x - min_x
    height = max_y - min_y
    
    # Start SVG
    svg_lines = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{min_x} {min_y} {width} {height}">',
        f'<g transform="scale(1,-1) translate(0,{-max_y-min_y})">',  # Flip Y-axis for CAD coordinates
    ]
    
    # Layer 1: Original DXF (light gray)
    svg_lines.append('<!-- Original DXF Lines -->')
    svg_lines.append('<g id="dxf-original" stroke="#CCCCCC" stroke-width="0.5" fill="none">')
    
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        for entity in msp:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                svg_lines.append(f'<line x1="{start.x}" y1="{start.y}" x2="{end.x}" y2="{end.y}"/>')
            elif entity.dxftype() == 'LWPOLYLINE':
                points = list(entity.get_points('xy'))
                if len(points) >= 2:
                    path_data = f'M {points[0][0]} {points[0][1]}'
                    for x, y in points[1:]:
                        path_data += f' L {x} {y}'
                    if entity.closed:
                        path_data += ' Z'
                    svg_lines.append(f'<path d="{path_data}"/>')
            elif entity.dxftype() == 'POLYLINE':
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                if len(points) >= 2:
                    path_data = f'M {points[0][0]} {points[0][1]}'
                    for x, y in points[1:]:
                        path_data += f' L {x} {y}'
                    if entity.is_closed:
                        path_data += ' Z'
                    svg_lines.append(f'<path d="{path_data}"/>')
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                svg_lines.append(f'<circle cx="{center.x}" cy="{center.y}" r="{radius}"/>')
            elif entity.dxftype() == 'ARC':
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                # Convert to radians and calculate points
                import math
                start_rad = math.radians(start_angle)
                end_rad = math.radians(end_angle)
                start_x = center.x + radius * math.cos(start_rad)
                start_y = center.y + radius * math.sin(start_rad)
                end_x = center.x + radius * math.cos(end_rad)
                end_y = center.y + radius * math.sin(end_rad)
                large_arc = 1 if (end_angle - start_angle) > 180 else 0
                svg_lines.append(f'<path d="M {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {end_x} {end_y}"/>')
    except Exception as e:
        print(f"Warning: Could not read DXF entities: {e}")
    
    svg_lines.append('</g>')
    
    # Layer 2: Room polygons (semi-transparent yellow)
    svg_lines.append('<!-- Room Polygons -->')
    svg_lines.append('<g id="rooms" fill="#FFFF00" fill-opacity="0.3" stroke="#FFD700" stroke-width="2">')
    
    for room in rooms:
        polygon = room['polygon']
        if len(polygon) >= 3:
            points_str = ' '.join([f"{x},{y}" for x, y in polygon])
            svg_lines.append(f'<polygon points="{points_str}"/>')
    
    svg_lines.append('</g>')
    
    # Layer 3: Walls (red)
    svg_lines.append('<!-- Walls -->')
    svg_lines.append('<g id="walls" stroke="#FF0000" stroke-width="3" fill="none">')
    
    for wall in walls:
        x1, y1 = wall['start']
        x2, y2 = wall['end']
        svg_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    
    svg_lines.append('</g>')
    
    # Layer 4: Doors (green)
    svg_lines.append('<!-- Doors -->')
    svg_lines.append('<g id="doors" stroke="#00FF00" stroke-width="3" fill="none">')
    
    for door in doors:
        if 'start' in door and 'end' in door:
            x1, y1 = door['start']
            x2, y2 = door['end']
            svg_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    
    svg_lines.append('</g>')
    
    # Layer 5: Windows (blue)
    svg_lines.append('<!-- Windows -->')
    svg_lines.append('<g id="windows" stroke="#0000FF" stroke-width="3" fill="none">')
    
    for window in windows:
        if 'start' in window and 'end' in window:
            x1, y1 = window['start']
            x2, y2 = window['end']
            svg_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    
    svg_lines.append('</g>')
    
    # Layer 6: Room labels
    svg_lines.append('<!-- Room Labels -->')
    svg_lines.append('<g id="room-labels" font-family="Arial" font-size="50" fill="#000000" text-anchor="middle">')
    
    for room in rooms:
        # Calculate centroid
        polygon = room['polygon']
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        
        room_id = room.get('id', 'Unknown')
        
        # Add white background for better readability
        svg_lines.append(f'<text x="{cx}" y="{cy}" transform="scale(1,-1) translate(0,{-2*cy})" '
                        f'stroke="#FFFFFF" stroke-width="3" paint-order="stroke">{room_id}</text>')
        svg_lines.append(f'<text x="{cx}" y="{cy}" transform="scale(1,-1) translate(0,{-2*cy})">{room_id}</text>')
    
    svg_lines.append('</g>')
    
    # Close SVG
    svg_lines.append('</g>')
    svg_lines.append('</svg>')
    
    # Write to file
    svg_content = '\n'.join(svg_lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"[OK] Validation overlay saved to: {output_path}")
    print(f"  - Original DXF: light gray")
    print(f"  - Walls: {len(walls)} (red)")
    print(f"  - Doors: {len(doors)} (green)")
    print(f"  - Windows: {len(windows)} (blue)")
    print(f"  - Rooms: {len(rooms)} (semi-transparent yellow with labels)")

def main():
    """Main execution"""
    
    # Paths
    dxf_path = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"
    walls_path = "outputs/walls.json"
    doors_path = "outputs/doors.json"
    windows_path = "outputs/windows.json"
    rooms_path = "outputs/rooms.json"
    output_path = "outputs/sprint1_final_validation.svg"
    
    # Load data
    print("Loading detection results...")
    walls = load_json(walls_path)
    doors = load_json(doors_path)
    windows = load_json(windows_path)
    rooms = load_json(rooms_path)
    
    print(f"Loaded: {len(walls)} walls, {len(doors)} doors, {len(windows)} windows, {len(rooms)} rooms")
    
    # Generate SVG
    print("\nGenerating validation overlay...")
    generate_svg(dxf_path, walls, doors, windows, rooms, output_path)
    
    print("\n[OK] Sprint 1 Final Validation Complete")

if __name__ == "__main__":
    main()
