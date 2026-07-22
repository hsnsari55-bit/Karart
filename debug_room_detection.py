import json
from shapely.geometry import LineString
from shapely.ops import polygonize

# Load walls
with open('outputs/walls_normalized.json', 'r', encoding='utf-8') as f:
    walls = json.load(f)

print(f"Total walls: {len(walls)}")

# Convert to LineStrings
lines = []
for wall in walls:
    if wall.get("type") == "LINE":
        start = tuple(wall["start"])
        end = tuple(wall["end"])
        lines.append(LineString([start, end]))

print(f"Total LineStrings: {len(lines)}")

# Try to polygonize
polygons = list(polygonize(lines))
print(f"Polygons detected: {len(polygons)}")

if polygons:
    print("\nFirst 5 polygons:")
    for i, poly in enumerate(polygons[:5]):
        print(f"  Polygon {i+1}: Area={poly.area:.2f}, Perimeter={poly.length:.2f}")
else:
    print("\nNo polygons detected - walls don't form closed loops")
    print("\nChecking wall connectivity...")
    
    # Check for gaps
    endpoints = {}
    for i, wall in enumerate(walls):
        if wall.get("type") == "LINE":
            start = tuple(wall["start"])
            end = tuple(wall["end"])
            
            endpoints[start] = endpoints.get(start, 0) + 1
            endpoints[end] = endpoints.get(end, 0) + 1
    
    # Count endpoints that appear only once (dead ends)
    dead_ends = [pt for pt, count in endpoints.items() if count == 1]
    print(f"Dead ends (unconnected endpoints): {len(dead_ends)}")
    
    # Show sample dead ends
    if dead_ends:
        print(f"\nSample dead ends (first 5):")
        for pt in dead_ends[:5]:
            print(f"  {pt}")
