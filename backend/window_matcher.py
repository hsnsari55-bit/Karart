import json
from math import hypot

WALL_FILE = r"C:\KaRar\outputs\walls_analyzed.json"
PLAN_FILE = r"C:\KaRar\outputs\plan_only.json"
OUTPUT = r"C:\KaRar\outputs\windows_matched.json"

with open(WALL_FILE, "r", encoding="utf-8") as f:
    walls = json.load(f)

with open(PLAN_FILE, "r", encoding="utf-8") as f:
    objects = json.load(f)

windows = []

for obj in objects:

    if obj.get("category") != "WINDOW":
        continue

    pts = []

    if obj["entity"] == "LINE":
        pts = [obj["start"], obj["end"]]

    elif obj["entity"] == "LWPOLYLINE":
        pts = obj.get("points", [])

    else:
        continue

    if len(pts) < 2:
        continue

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)

    best_wall = None
    best_dist = 1e9

    for wall in walls:

        if wall["type"] != "LINE":
            continue

        x1, y1 = wall["start"]
        x2, y2 = wall["end"]

        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2

        d = hypot(cx - mx, cy - my)

        if d < best_dist:
            best_dist = d
            best_wall = wall["id"]

    windows.append({
        "wall_id": best_wall,
        "center": [round(cx, 2), round(cy, 2)],
        "distance": round(best_dist, 2)
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(windows, f, indent=4, ensure_ascii=False)

print("====================================")
print("       WINDOW MATCHER")
print("====================================")
print("Window :", len(windows))
print("Kaydedildi :", OUTPUT)
print("====================================")