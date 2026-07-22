"""
Generate SVG visualization of drawing segmentation results.

Shows bounding boxes around each detected drawing region with labels.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def generate_svg_visualization(segmentation_file: str, output_file: str) -> None:
    """
    Generate SVG showing bounding boxes for each detected drawing.
    
    Args:
        segmentation_file: Path to drawing_segmentation.json
        output_file: Path to save the SVG
    """
    # Load segmentation data
    with open(segmentation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regions = data['regions']
    
    if not regions:
        print("No regions found in segmentation data")
        return
    
    # Calculate overall bounds
    all_min_x = min(r['bounds']['min_x'] for r in regions)
    all_max_x = max(r['bounds']['max_x'] for r in regions)
    all_min_y = min(r['bounds']['min_y'] for r in regions)
    all_max_y = max(r['bounds']['max_y'] for r in regions)
    
    # Add padding
    padding = 500
    all_min_x -= padding
    all_max_x += padding
    all_min_y -= padding
    all_max_y += padding
    
    # Calculate SVG dimensions
    drawing_width = all_max_x - all_min_x
    drawing_height = all_max_y - all_min_y
    
    # Scale to fit in reasonable SVG size (max 2000px)
    max_dimension = 2000
    scale = min(max_dimension / drawing_width, max_dimension / drawing_height)
    
    svg_width = drawing_width * scale
    svg_height = drawing_height * scale
    
    # Color scheme for different drawing types
    colors = {
        'Floor Plan': '#2E7D32',      # Green
        'Roof Plan': '#1565C0',       # Blue
        'Elevation': '#F57C00',       # Orange
        'Section': '#C62828',         # Red
        'Detail': '#6A1B9A'           # Purple
    }
    
    # Start SVG
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width:.0f}" height="{svg_height:.0f}" viewBox="0 0 {svg_width:.0f} {svg_height:.0f}">',
        '  <defs>',
        '    <style>',
        '      .bbox { fill: none; stroke-width: 3; opacity: 0.8; }',
        '      .label { font-family: Arial, sans-serif; font-size: 24px; font-weight: bold; }',
        '      .info { font-family: Arial, sans-serif; font-size: 16px; }',
        '      .title { font-family: Arial, sans-serif; font-size: 32px; font-weight: bold; fill: #333; }',
        '    </style>',
        '  </defs>',
        '',
        '  <!-- Background -->',
        '  <rect width="100%" height="100%" fill="#f5f5f5"/>',
        '',
        '  <!-- Title -->',
        f'  <text x="{svg_width/2:.0f}" y="40" class="title" text-anchor="middle">Drawing Segmentation - Connected Components</text>',
        f'  <text x="{svg_width/2:.0f}" y="70" class="info" text-anchor="middle" fill="#666">Detected {len(regions)} drawing region(s)</text>',
        ''
    ]
    
    # Transform function
    def transform_x(x: float) -> float:
        return (x - all_min_x) * scale
    
    def transform_y(y: float) -> float:
        # Flip Y axis for SVG (Y increases downward)
        return svg_height - (y - all_min_y) * scale
    
    # Draw each region
    for i, region in enumerate(regions, 1):
        bounds = region['bounds']
        drawing_type = region['type']
        floor_level = region.get('floor_level', None)
        color = colors.get(drawing_type, '#757575')
        
        # Transform coordinates
        x1 = transform_x(bounds['min_x'])
        y1 = transform_y(bounds['max_y'])  # Note: max_y maps to top in SVG
        x2 = transform_x(bounds['max_x'])
        y2 = transform_y(bounds['min_y'])  # Note: min_y maps to bottom in SVG
        
        width = x2 - x1
        height = y2 - y1
        
        # Draw bounding box
        svg_lines.append(f'  <!-- Region {i}: {drawing_type} -->')
        svg_lines.append(f'  <rect x="{x1:.2f}" y="{y1:.2f}" width="{width:.2f}" height="{height:.2f}" class="bbox" stroke="{color}"/>')
        
        # Add label
        label_x = x1 + width / 2
        label_y = y1 - 10
        
        # Include floor level in label if available
        label_text = f'{drawing_type} #{i}'
        if floor_level and floor_level != drawing_type:
            label_text = f'{drawing_type} #{i} ({floor_level})'
        
        svg_lines.append(f'  <text x="{label_x:.2f}" y="{label_y:.2f}" class="label" text-anchor="middle" fill="{color}">')
        svg_lines.append(f'    {label_text}')
        svg_lines.append(f'  </text>')
        
        # Add info text inside box
        info_x = x1 + 10
        info_y = y1 + 25
        
        # Show floor level if available
        if floor_level:
            svg_lines.append(f'  <text x="{info_x:.2f}" y="{info_y:.2f}" class="info" fill="{color}" font-weight="bold">')
            svg_lines.append(f'    {floor_level}')
            svg_lines.append(f'  </text>')
            info_y += 20
        
        svg_lines.append(f'  <text x="{info_x:.2f}" y="{info_y:.2f}" class="info" fill="{color}">')
        svg_lines.append(f'    {region["entity_count"]} entities')
        svg_lines.append(f'  </text>')
        
        info_y += 20
        svg_lines.append(f'  <text x="{info_x:.2f}" y="{info_y:.2f}" class="info" fill="{color}">')
        svg_lines.append(f'    {region["width"]:.0f} × {region["height"]:.0f}')
        svg_lines.append(f'  </text>')
        
        svg_lines.append('')
    
    # Add legend
    legend_x = 20
    legend_y = svg_height - 200
    
    svg_lines.append('  <!-- Legend -->')
    svg_lines.append(f'  <rect x="{legend_x}" y="{legend_y}" width="250" height="{len(colors) * 30 + 40}" fill="white" stroke="#333" stroke-width="2" opacity="0.9"/>')
    svg_lines.append(f'  <text x="{legend_x + 125}" y="{legend_y + 25}" class="label" text-anchor="middle" font-size="18">Drawing Types</text>')
    
    legend_y += 45
    for drawing_type, color in colors.items():
        svg_lines.append(f'  <rect x="{legend_x + 10}" y="{legend_y - 12}" width="20" height="20" fill="{color}"/>')
        svg_lines.append(f'  <text x="{legend_x + 40}" y="{legend_y + 3}" class="info">{drawing_type}</text>')
        legend_y += 30
    
    # Close SVG
    svg_lines.append('</svg>')
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))
    
    print(f"\nVisualization saved to: {output_file}")
    print(f"SVG dimensions: {svg_width:.0f} × {svg_height:.0f}")
    print(f"\nRegion breakdown:")
    
    # Count by type
    from collections import Counter
    type_counts = Counter(r['type'] for r in regions)
    for drawing_type, count in sorted(type_counts.items()):
        print(f"  {drawing_type}: {count}")


def main():
    """Main entry point"""
    # Default paths
    segmentation_file = "outputs/drawing_segmentation.json"
    output_file = "outputs/drawing_segmentation_validation.svg"
    
    # Check if files exist
    if not Path(segmentation_file).exists():
        print(f"Error: Segmentation file not found: {segmentation_file}")
        print("Please run the segmentation first:")
        print("  python backend/drawing_segmentation.py")
        sys.exit(1)
    
    # Generate visualization
    generate_svg_visualization(segmentation_file, output_file)
    print(f"\nOpen {output_file} in a web browser to view the results.")


if __name__ == "__main__":
    main()
