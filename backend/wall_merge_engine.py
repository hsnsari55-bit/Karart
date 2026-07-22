import json
from math import hypot

INPUT = r"C:\KaRar\outputs\walls_normalized.json"
OUTPUT = r"C:\KaRar\outputs\walls_merged.json"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

line_walls = [w for w in walls if w["type"] == "LINE"]

used = set()
merged = []

TOL = 10.0

for i, w1 in enumerate(line_walls):

    if i in used:
        continue

    x1, y1 = w1["start"]
    x2, y2 = w1["end"]

    angle = w1.get("angle", 0)

    sx, sy = x1, y1
    ex, ey = x2, y2

    used.add(i)

    changed = True

    while changed:

        changed = False

        for j, w2 in enumerate(line_walls):

            if j in used:
                continue

            if abs(angle - w2.get("angle", 0)) > 3:
                continue

            a1 = w2["start"]
            a2 = w2["end"]

            d1 = hypot(ex - a1[0], ey - a1[1])
            d2 = hypot(ex - a2[0], ey - a2[1])
            d3 = hypot(sx - a1[0], sy - a1[1])
            d4 = hypot(sx - a2[0], sy - a2[1])

            if d1 < TOL:
                ex, ey = a2
                used.add(j)
                changed = True

            elif d2 < TOL:
                ex, ey = a1
                used.add(j)
                changed = True

            elif d3 < TOL:
                sx, sy = a2
                used.add(j)
                changed = True

            elif d4 < TOL:
                sx, sy = a1
                used.add(j)
                changed = True

    merged.append({
        "id": len(merged) + 1,
        "type": "LINE",
        "start": [sx, sy],
        "end": [ex, ey],
        "angle": angle
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(merged, f, indent=4, ensure_ascii=False)

print("====================================")
print("      WALL MERGE ENGINE")
print("====================================")
print("İlk Wall :", len(line_walls))
print("Yeni Wall:", len(merged))
print("Birleşen :", len(line_walls) - len(merged))
print("Kaydedildi :", OUTPUT)
print("====================================")