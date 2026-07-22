import json
from math import hypot

INPUT = r"C:\KaRar\outputs\walls_analyzed.json"
OUTPUT = r"C:\KaRar\outputs\walls_thickness.json"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

line_walls = [w for w in walls if w["type"] == "LINE"]

count = 0

for wall in line_walls:

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2

    angle = wall.get("angle", 0)

    best = None
    best_dist = 999999

    for other in line_walls:

        if wall["id"] == other["id"]:
            continue

        if abs(angle - other.get("angle", 0)) > 5:
            continue

        ox1, oy1 = other["start"]
        ox2, oy2 = other["end"]

        omx = (ox1 + ox2) / 2
        omy = (oy1 + oy2) / 2

        d = hypot(mx - omx, my - omy)

        if 50 < d < 400 and d < best_dist:
            best_dist = d
            best = other["id"]

    if best:

        wall["pair_wall"] = best
        wall["thickness"] = round(best_dist, 2)
        count += 1

    else:

        wall["pair_wall"] = None
        wall["thickness"] = None

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(walls, f, indent=4, ensure_ascii=False)

print("====================================")
print("   WALL THICKNESS DETECTOR")
print("====================================")
print("Wall :", len(line_walls))
print("Pair :", count)
print("Kaydedildi :", OUTPUT)
print("====================================")