import json
from math import atan2, degrees, hypot

INPUT = r"C:\KaRar\outputs\walls_merged.json"
OUTPUT = r"C:\KaRar\outputs\wall_axis.json"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

axis = []

for wall in walls:

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2

    length = hypot(x2 - x1, y2 - y1)

    angle = degrees(atan2(y2 - y1, x2 - x1))

    if angle < 0:
        angle += 180

    axis.append({
        "id": wall["id"],
        "start": [x1, y1],
        "end": [x2, y2],
        "center": [round(mx, 3), round(my, 3)],
        "length": round(length, 3),
        "angle": round(angle, 3)
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(axis, f, indent=4, ensure_ascii=False)

print("====================================")
print("      WALL AXIS DETECTOR")
print("====================================")
print("Axis :", len(axis))

if axis:
    longest = max(axis, key=lambda x: x["length"])
    print("En Uzun Axis :", round(longest["length"], 2))

print("Kaydedildi :", OUTPUT)
print("====================================")