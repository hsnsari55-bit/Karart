import json
import os
import sys
from math import hypot

# Ensure project root is in sys.path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.path_manager import PathManager

# ======================================
# DOSYA
# ======================================

pm = PathManager()
BIM_FILE = pm.get_path("outputs", "bim_clean.json")

if not os.path.exists(BIM_FILE):
    BIM_FILE = pm.get_path("outputs", "bim.json")

if not os.path.exists(BIM_FILE):
    print(f"Hata: BIM dosyası bulunamadı: {BIM_FILE}")
    sys.exit(1)

# ======================================
# OKU
# ======================================

with open(BIM_FILE, "r", encoding="utf-8") as f:
    objects = json.load(f)

walls = []
doors = []
windows = []
columns = []
stairs = []

for obj in objects:

    if obj["category"] == "WALL":
        walls.append(obj)

    elif obj["category"] == "DOOR":
        doors.append(obj)

    elif obj["category"] == "WINDOW":
        windows.append(obj)

    elif obj["category"] == "COLUMN":
        columns.append(obj)

    elif obj["category"] == "STAIR":
        stairs.append(obj)

# ======================================
# WALL GRAPH
# ======================================

nodes = {}
edges = []

def add_node(pt):

    key = (round(pt[0], 3), round(pt[1], 3))

    if key not in nodes:
        nodes[key] = len(nodes)

    return nodes[key]

for wall in walls:

    if wall["entity"] == "LINE":

        p1 = wall["start"]
        p2 = wall["end"]

        n1 = add_node(p1)
        n2 = add_node(p2)

        edges.append((n1, n2))

    elif wall["entity"] == "LWPOLYLINE":

        pts = wall["points"]

        for i in range(len(pts)-1):

            n1 = add_node(pts[i])
            n2 = add_node(pts[i+1])

            edges.append((n1, n2))

# ======================================
# RAPOR
# ======================================

print("===================================")
print("      KaRar Geometry Core")
print("===================================")

print("Wall :", len(walls))
print("Door :", len(doors))
print("Window :", len(windows))
print("Column :", len(columns))
print("Stair :", len(stairs))

print("-----------------------------------")

print("Graph Node :", len(nodes))
print("Graph Edge :", len(edges))

print("===================================")