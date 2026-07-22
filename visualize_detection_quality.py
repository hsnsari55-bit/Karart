#!/usr/bin/env python3
"""
Visual validation of wall, door, and window detection quality.
Generates an SVG overlay showing:
- Original DXF entities in gray
- Detected walls in red
- Detected doors in green
- Detected windows in blue
"""

import ezdxf
import json
from pathlib import Path


def load_json(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_bounds(entities):
    """Calculate bounding box for all entities."""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for entity in entities:
        if 'start' in entity and 'end' in entity:
            points = [entity['start'], entity['end']]
        elif 'points' in entity:
            points = entity['points']
        else:
            continue
            
        for point in points:
            x, y = point[0], point[1]
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
    
    return min_x, min_y, max_x, max_y


def transform_coords(x, y, min_x, min_y, scale):
    """Transform DXF coordinates to SVG coordinates."""
    # Flip Y axis for SVG (Y increases downward in SVG)
    svg_x = (x - min_x) * scale
    svg_y = (y - min_y) * scale
    return svg_x, svg_y


def create_svg_overlay(dxf_path, walls_path, doors_path, windows_path, output_path):
    """Create SVG overlay visualization."""
    
    print("Loading DXF file...")
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    print("Loading detection results...")
    walls = load_json(walls_path)
    doors = load_json(doors_path)
    windows = load_json(windows_path)
    
    print(f"Loaded {len(walls)} walls, {len(doors)} doors, {len(windows)} windows")
    
    # Collect all DXF lines and polylines
    dxf_entities = []
    for entity in msp:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            dxf_entities.append({
                'type': 'LINE',
                'start': [start.x, start.y],
                'end': [end.x, end.y]
            })
        elif entity.dxftype() == 'LWPOLYLINE':
            points = list(entity.get_points('xy'))
            if len(points) >= 2:
                for i in range(len(points) - 1):
                    dxf_entities.append({
                        'type': 'LINE',
                        'start': [points[i][0], points[i][1]],
                        'end': [points[i+1][0], points[i+1][1]]
                    })
                # Close polyline if needed
                if entity.closed:
                    dxf_entities.append({
                        'type': 'LINE',
                        'start': [points[-1][0], points[-1][1]],
                        'end': [points[0][0], points[0][1]]
                    })
    
    print(f"Collected {len(dxf_entities)} DXF entities")
    
    # Calculate bounds from all entities
    all_entities = dxf_entities + walls + doors + windows
    min_x, min_y, max_x, max_y = get_bounds(all_entities)
    
    width = max_x - min_x
    height = max_y - min_y
    
    # Calculate scale to fit in reasonable SVG size (max 4000px)
    max_dimension = 4000
    scale = min(max_dimension / width, max_dimension / height)
    
    svg_width = width * scale
    svg_height = height * scale
    
    print(f"Bounds: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})")
    print(f"Dimensions: {width:.2f} x {height:.2f}")
    print(f"Scale: {scale:.4f}")
    print(f"SVG size: {svg_width:.0f} x {svg_height:.0f}")
    
    # Start building SVG
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width:.0f}" height="{svg_height:.0f}" viewBox="0 0 {svg_width:.0f} {svg_height:.0f}">')
    svg_lines.append('  <title>Wall Detection Quality Validation</title>')
    svg_lines.append('  <desc>Gray: Original DXF | Red: Detected Walls | Green: Detected Doors | Blue: Detected Windows</desc>')
    
    # Add white background
    svg_lines.append(f'  <rect width="{svg_width:.0f}" height="{svg_height:.0f}" fill="white"/>')
    
    # Draw original DXF entities in gray (thin lines)
    svg_lines.append('  <!-- Original DXF Entities (Gray) -->')
    svg_lines.append('  <g id="dxf-entities" stroke="lightgray" stroke-width="0.5" opacity="0.5">')
    for entity in dxf_entities:
        x1, y1 = transform_coords(entity['start'][0], entity['start'][1], min_x, min_y, scale)
        x2, y2 = transform_coords(entity['end'][0], entity['end'][1], min_x, min_y, scale)
        svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    svg_lines.append('  </g>')
    
    # Draw detected walls in red
    svg_lines.append('  <!-- Detected Walls (Red) -->')
    svg_lines.append('  <g id="walls" stroke="red" stroke-width="2" opacity="0.7">')
    for wall in walls:
        x1, y1 = transform_coords(wall['start'][0], wall['start'][1], min_x, min_y, scale)
        x2, y2 = transform_coords(wall['end'][0], wall['end'][1], min_x, min_y, scale)
        svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    svg_lines.append('  </g>')
    
    # Draw detected doors in green
    svg_lines.append('  <!-- Detected Doors (Green) -->')
    svg_lines.append('  <g id="doors" stroke="green" stroke-width="1.5" opacity="0.8">')
    for door in doors:
        if 'start' in door and 'end' in door:
            x1, y1 = transform_coords(door['start'][0], door['start'][1], min_x, min_y, scale)
            x2, y2 = transform_coords(door['end'][0], door['end'][1], min_x, min_y, scale)
            svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
        elif 'points' in door:
            # Handle polylines
            points = door['points']
            for i in range(len(points) - 1):
                x1, y1 = transform_coords(points[i][0], points[i][1], min_x, min_y, scale)
                x2, y2 = transform_coords(points[i+1][0], points[i+1][1], min_x, min_y, scale)
                svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    svg_lines.append('  </g>')
    
    # Draw detected windows in blue
    svg_lines.append('  <!-- Detected Windows (Blue) -->')
    svg_lines.append('  <g id="windows" stroke="blue" stroke-width="1.5" opacity="0.8">')
    for window in windows:
        if 'start' in window and 'end' in window:
            x1, y1 = transform_coords(window['start'][0], window['start'][1], min_x, min_y, scale)
            x2, y2 = transform_coords(window['end'][0], window['end'][1], min_x, min_y, scale)
            svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
        elif 'points' in window:
            # Handle polylines
            points = window['points']
            for i in range(len(points) - 1):
                x1, y1 = transform_coords(points[i][0], points[i][1], min_x, min_y, scale)
                x2, y2 = transform_coords(points[i+1][0], points[i+1][1], min_x, min_y, scale)
                svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    svg_lines.append('  </g>')
    
    # Add legend
    svg_lines.append('  <!-- Legend -->')
    legend_x = 20
    legend_y = 20
    svg_lines.append(f'  <g id="legend">')
    svg_lines.append(f'    <rect x="{legend_x-10}" y="{legend_y-10}" width="200" height="110" fill="white" stroke="black" stroke-width="1" opacity="0.9"/>')
    svg_lines.append(f'    <text x="{legend_x}" y="{legend_y+10}" font-family="Arial" font-size="14" font-weight="bold">Legend</text>')
    svg_lines.append(f'    <line x1="{legend_x}" y1="{legend_y+25}" x2="{legend_x+30}" y2="{legend_y+25}" stroke="lightgray" stroke-width="2"/>')
    svg_lines.append(f'    <text x="{legend_x+40}" y="{legend_y+30}" font-family="Arial" font-size="12">Original DXF</text>')
    svg_lines.append(f'    <line x1="{legend_x}" y1="{legend_y+45}" x2="{legend_x+30}" y2="{legend_y+45}" stroke="red" stroke-width="2"/>')
    svg_lines.append(f'    <text x="{legend_x+40}" y="{legend_y+50}" font-family="Arial" font-size="12">Walls ({len(walls)})</text>')
    svg_lines.append(f'    <line x1="{legend_x}" y1="{legend_y+65}" x2="{legend_x+30}" y2="{legend_y+65}" stroke="green" stroke-width="2"/>')
    svg_lines.append(f'    <text x="{legend_x+40}" y="{legend_y+70}" font-family="Arial" font-size="12">Doors ({len(doors)})</text>')
    svg_lines.append(f'    <line x1="{legend_x}" y1="{legend_y+85}" x2="{legend_x+30}" y2="{legend_y+85}" stroke="blue" stroke-width="2"/>')
    svg_lines.append(f'    <text x="{legend_x+40}" y="{legend_y+90}" font-family="Arial" font-size="12">Windows ({len(windows)})</text>')
    svg_lines.append(f'  </g>')
    
    svg_lines.append('</svg>')
    
    # Write SVG file
    svg_content = '\n'.join(svg_lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"\nSVG overlay saved to: {output_path}")
    print(f"File size: {len(svg_content) / 1024:.1f} KB")


def main():
    """Main execution."""
    # Paths
    dxf_path = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"
    walls_path = "outputs/walls.json"
    doors_path = "outputs/doors.json"
    windows_path = "outputs/windows.json"
    output_path = "outputs/detection_quality_overlay.svg"
    
    # Ensure output directory exists
    Path("outputs").mkdir(exist_ok=True)
    
    # Check if input files exist
    if not Path(dxf_path).exists():
        print(f"ERROR: DXF file not found: {dxf_path}")
        return
    
    if not Path(walls_path).exists():
        print(f"ERROR: Walls file not found: {walls_path}")
        return
    
    if not Path(doors_path).exists():
        print(f"ERROR: Doors file not found: {doors_path}")
        return
    
    if not Path(windows_path).exists():
        print(f"ERROR: Windows file not found: {windows_path}")
        return
    
    # Create visualization
    create_svg_overlay(dxf_path, walls_path, doors_path, windows_path, output_path)
    
    print("\n" + "="*60)
    print("VISUAL VALIDATION COMPLETE")
    print("="*60)
    print(f"Open the SVG file in a web browser to inspect:")
    print(f"  {output_path}")
    print("\nColor coding:")
    print("  - Gray (light):  Original DXF entities")
    print("  - Red:           Detected walls")
    print("  - Green:         Detected doors")
    print("  - Blue:          Detected windows")
    print("="*60)


if __name__ == "__main__":
    main()
