from shapely.geometry import LineString
from shapely.ops import unary_union, polygonize

lines = [
    LineString([(0, 0), (10, 0)]),
    LineString([(10, 0), (10, 10)]),
    LineString([(10, 10), (0, 10)]),
    LineString([(0, 10), (0, 0)]),
    LineString([(5, -5), (5, 15)])
]

noded = unary_union(lines)
lines = list(noded.geoms)

polygons = list(polygonize(lines))
print(f"Polygons: {len(polygons)}")

for i, poly in enumerate(polygons):
    poly_edges = []
    for j, line in enumerate(lines):
        if poly.exterior.covers(line):
            poly_edges.append(j)
    print(f"Poly {i} edges:", poly_edges)
