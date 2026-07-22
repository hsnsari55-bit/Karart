import json
import os
import sys

# Ensure project root is in sys.path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.path_manager import PathManager

pm = PathManager()
JSON_FILE = pm.get_path("outputs", "walls_clean.json")

if not os.path.exists(JSON_FILE):
    print(f"Hata: Doğrulama dosyası bulunamadı: {JSON_FILE}")
    sys.exit(1)

with open(JSON_FILE, "r", encoding="utf-8") as f:
    walls = json.load(f)

endpoints = {}

for wall in walls:

    if wall["type"] == "LINE":

        pts = [
            tuple(wall["start"]),
            tuple(wall["end"])
        ]

    elif wall["type"] == "LWPOLYLINE":

        pts = [tuple(p) for p in wall["points"]]

        if wall.get("closed", False):
            continue

        pts = [
            pts[0],
            pts[-1]
        ]

    else:
        continue

    for p in pts:

        endpoints[p] = endpoints.get(p, 0) + 1

open_points = []

for p, c in endpoints.items():

    if c == 1:
        open_points.append(p)

print("--------------------------------")
print("Toplam Endpoint :", len(endpoints))
print("Açık Endpoint :", len(open_points))
print("--------------------------------")

print("İlk 20 Açık Nokta")

for p in open_points[:20]:
    print(p)

print("--------------------------------")