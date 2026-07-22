import json
from math import hypot
from collections import defaultdict

INPUT = r"C:\KaRar\outputs\walls_normalized.json"
OUTPUT = r"C:\KaRar\outputs\geometry_graph.json"

TOL = 10.0

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

nodes = []
edges = []

def get_node(pt):
    x, y = pt

    for i, (nx, ny) in enumerate(nodes):
        if hypot(nx - x, ny - y) <= TOL:
            return i

    nodes.append((x, y))
    return len(nodes) - 1

for wall in walls:

    if wall["type"] != "LINE":
        continue

    n1 = get_node(tuple(wall["start"]))
    n2 = get_node(tuple(wall["end"]))

    edges.append({
        "wall_id": wall["id"],
        "from": n1,
        "to": n2,
        "angle": wall["angle"]
    })

degree = defaultdict(int)

for e in edges:
    degree[e["from"]] += 1
    degree[e["to"]] += 1

graph = {
    "nodes": [
        {
            "id": i,
            "x": round(x, 3),
            "y": round(y, 3),
            "degree": degree[i]
        }
        for i, (x, y) in enumerate(nodes)
    ],
    "edges": edges
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=4, ensure_ascii=False)

print("====================================")
print("        GEOMETRY GRAPH")
print("====================================")
print("Node :", len(nodes))
print("Edge :", len(edges))
print("Degree1 :", sum(1 for d in degree.values() if d == 1))
print("Degree2 :", sum(1 for d in degree.values() if d == 2))
print("Degree3+ :", sum(1 for d in degree.values() if d >= 3))
print("Kaydedildi :", OUTPUT)
print("====================================")