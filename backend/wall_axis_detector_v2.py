import json
from math import atan2, degrees, hypot

INPUT = r"C:\KaRar\outputs\walls_merged_v2.json"
OUTPUT = r"C:\KaRar\outputs\wall_axis_v2.json"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

axes = []

for i, wall in enumerate(walls, start=1):

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    length = hypot(x2 - x1, y2 - y1)

    angle = degrees(atan2(y2 - y1, x2 - x1))
    if angle < 0:
        angle += 180

    axes.append({
        "id": i,
        "start": [x1, y1],
        "end": [x2, y2],
        "center": [
            round((x1 + x2) / 2, 3),
            round((y1 + y2) / 2, 3)
        ],
        "length": round(length, 3),
        "angle": round(angle, 3)
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(axes, f, indent=4, ensure_ascii=False)

print("====================================")
print("     WALL AXIS DETECTOR V2")
print("====================================")
print("Axis :", len(axes))
print("Toplam Uzunluk :", round(sum(a["length"] for a in axes), 2))
print("En Uzun :", round(max(a["length"] for a in axes), 2))
print("Kaydedildi :", OUTPUT)
print("====================================")