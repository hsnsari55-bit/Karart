import json
from math import hypot

INPUT = r"C:\KaRar\outputs\bim_clean.json"

SNAP_DISTANCE = 20.0

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

nodes = []

for obj in objects:

    if obj["category"] != "WALL":
        continue

    if obj["entity"] == "LINE":

        nodes.append(obj["start"])
        nodes.append(obj["end"])

    elif obj["entity"] == "LWPOLYLINE":

        for p in obj["points"]:
            nodes.append(p)

# ======================================

unique = []

for p in nodes:

    found = False

    for u in unique:

        if hypot(p[0]-u[0], p[1]-u[1]) <= SNAP_DISTANCE:
            found = True
            break

    if not found:
        unique.append(p)

# ======================================

print("====================================")
print("        Node Snapper")
print("====================================")
print("İlk Node      :", len(nodes))
print("Snap Sonrası  :", len(unique))
print("Birleşen Node :", len(nodes)-len(unique))
print("Snap Mesafesi :", SNAP_DISTANCE)
print("====================================")