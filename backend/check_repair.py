import json
from shapely.geometry import Polygon

with open("outputs/bim_model.json") as f:
    bim_data = json.load(f)

for c in bim_data.get("columns", []):
    pts = c.get("points", [])
    if len(pts) >= 3:
        p = Polygon(pts)
        if not p.is_valid:
            print(f"Invalid column: {c.get('uuid')} - repairing...")
            p = p.buffer(0)
            print(f"Repaired: {p.is_valid}, Type: {p.geom_type}")

for s in bim_data.get("spaces", []):
    pts = s.get("polygon", [])
    if len(pts) >= 3:
        p = Polygon(pts)
        if not p.is_valid:
            print(f"Invalid space: {s.get('uuid')} - repairing...")
            p = p.buffer(0)
            print(f"Repaired: {p.is_valid}, Type: {p.geom_type}")
