import json
from math import atan2, degrees

INPUT = r"C:\KaRar\outputs\walls_objects.json"
OUTPUT = r"C:\KaRar\outputs\walls_analyzed.json"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

for wall in walls:

    if wall["type"] != "LINE":
        continue

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    angle = degrees(atan2(y2 - y1, x2 - x1))

    if angle < 0:
        angle += 180

    wall["angle"] = round(angle, 2)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(walls, f, indent=4, ensure_ascii=False)

angles = [w["angle"] for w in walls if "angle" in w]

print("====================================")
print("        WALL ANALYZER")
print("====================================")
print("Toplam Wall :", len(walls))
print("LINE Angle  :", len(angles))
print("Kaydedildi  :", OUTPUT)
print("====================================")