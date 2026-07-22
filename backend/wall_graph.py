import json
from collections import defaultdict

# =====================================
# DOSYA
# =====================================

INPUT = r"C:\KaRar\outputs\bim_clean.json"

# =====================================
# OKU
# =====================================

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

walls = []

for obj in objects:

    if obj["category"] == "WALL":
        walls.append(obj)

# =====================================
# GRAPH
# =====================================

node_map = {}
reverse_nodes = {}
edges = []

def get_node(point):

    key = (
        round(point[0], 3),
        round(point[1], 3)
    )

    if key not in node_map:

        idx = len(node_map)

        node_map[key] = idx
        reverse_nodes[idx] = key

    return node_map[key]

for wall in walls:

    if wall["entity"] == "LINE":

        a = get_node(wall["start"])
        b = get_node(wall["end"])

        edges.append((a, b))

    elif wall["entity"] == "LWPOLYLINE":

        pts = wall["points"]

        for i in range(len(pts) - 1):

            a = get_node(pts[i])
            b = get_node(pts[i + 1])

            edges.append((a, b))

# =====================================
# BAĞLANTI
# =====================================

graph = defaultdict(set)

for a, b in edges:

    graph[a].add(b)
    graph[b].add(a)

connected = 0

for node in graph:

    if len(graph[node]) > 0:
        connected += 1

# =====================================
# RAPOR
# =====================================

print("====================================")
print("          Wall Graph")
print("====================================")

print("Wall Objects :", len(walls))
print("Nodes        :", len(node_map))
print("Edges        :", len(edges))
print("Connected    :", connected)

print("====================================")