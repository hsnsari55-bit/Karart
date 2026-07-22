import json
from collections import defaultdict

INPUT = r"C:\KaRar\outputs\bim_clean.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

nodes = {}
graph = defaultdict(set)

def node_id(pt):

    key = (round(pt[0], 3), round(pt[1], 3))

    if key not in nodes:
        nodes[key] = len(nodes)

    return nodes[key]

for obj in objects:

    if obj["category"] != "WALL":
        continue

    if obj["entity"] == "LINE":

        a = node_id(obj["start"])
        b = node_id(obj["end"])

        graph[a].add(b)
        graph[b].add(a)

    elif obj["entity"] == "LWPOLYLINE":

        pts = obj["points"]

        for i in range(len(pts)-1):

            a = node_id(pts[i])
            b = node_id(pts[i+1])

            graph[a].add(b)
            graph[b].add(a)

degree = defaultdict(int)

for node in graph:
    degree[len(graph[node])] += 1

print("\n========== GRAPH ANALYZER ==========\n")

for d in sorted(degree):
    print(f"Degree {d} : {degree[d]}")

print("\nToplam Node :", len(nodes))
print("Toplam Edge :", sum(len(v) for v in graph.values())//2)