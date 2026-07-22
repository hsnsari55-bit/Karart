import json
from math import hypot

INPUT = r"C:\KaRar\outputs\plan_only.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

walls = []

for obj in objects:

    if obj.get("category") != "WALL":
        continue

    if obj["entity"] == "LINE":

        p1 = obj["start"]
        p2 = obj["end"]

        length = hypot(
            p2[0] - p1[0],
            p2[1] - p1[1]
        )

        walls.append({
            "id": len(walls) + 1,
            "type": "LINE",
            "start": p1,
            "end": p2,
            "length": round(length, 2)
        })

    elif obj["entity"] == "LWPOLYLINE":

        pts = obj["points"]

        total = 0

        for i in range(len(pts) - 1):
            total += hypot(
                pts[i + 1][0] - pts[i][0],
                pts[i + 1][1] - pts[i][1]
            )

        walls.append({
            "id": len(walls) + 1,
            "type": "POLYLINE",
            "points": pts,
            "length": round(total, 2)
        })

print("====================================")
print("         WALL BUILDER")
print("====================================")
print("Wall Object :", len(walls))

line_count = sum(1 for w in walls if w["type"] == "LINE")
poly_count = sum(1 for w in walls if w["type"] == "POLYLINE")

print("LINE      :", line_count)
print("POLYLINE  :", poly_count)

if walls:
    avg = sum(w["length"] for w in walls) / len(walls)
    longest = max(w["length"] for w in walls)

    print("Ortalama Uzunluk :", round(avg, 2))
    print("En Uzun Duvar    :", round(longest, 2))

with open(r"C:\KaRar\outputs\walls_objects.json", "w", encoding="utf-8") as f:
    json.dump(walls, f, indent=4, ensure_ascii=False)

print("------------------------------------")
print("Kaydedildi : C:\\KaRar\\outputs\\walls_objects.json")
print("====================================")