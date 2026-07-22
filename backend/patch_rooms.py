import json
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, polygonize
from rtree import index

with open('outputs/geometry_graph.json', 'r') as f:
    d = json.load(f)

nodes = d['nodes']
edges = d['edges']

# Find all dangling nodes
danglings = [n for n in nodes if n['degree'] == 1]
print(f"Dangling nodes: {len(danglings)}")

lines = []
for e in edges:
    n1 = nodes[e['from']]
    n2 = nodes[e['to']]
    lines.append(LineString([(n1['x'], n1['y']), (n2['x'], n2['y'])]))

print(f"Original lines: {len(lines)}")
# Try to close gaps
virtual_lines = []
rt = index.Index()
for i, n in enumerate(danglings):
    rt.insert(i, (n['x'], n['y'], n['x'], n['y']))

for i, n in enumerate(danglings):
    # Find neighbors within 200 units
    neighbors = list(rt.intersection((n['x']-200, n['y']-200, n['x']+200, n['y']+200)))
    for j in neighbors:
        if i < j:
            n2 = danglings[j]
            dist = ((n['x']-n2['x'])**2 + (n['y']-n2['y'])**2)**0.5
            if 10 < dist <= 200:
                virtual_lines.append(LineString([(n['x'], n['y']), (n2['x'], n2['y'])]))

print(f"Virtual lines: {len(virtual_lines)}")

all_lines = lines + virtual_lines
noded = unary_union(all_lines)
if noded.geom_type == 'MultiLineString':
    final_lines = list(noded.geoms)
elif noded.geom_type == 'LineString':
    final_lines = [noded]

polys = list(polygonize(final_lines))
print(f"Polygons found: {len(polys)}")

areas = [p.area for p in polys]
areas.sort()
print("Top 20 areas:", areas[-20:])
