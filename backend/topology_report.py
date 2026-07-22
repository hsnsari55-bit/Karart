import json
from math import hypot

INPUT = r"C:\KaRar\outputs\bim_clean.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

points = []

for obj in objects:

    if obj["category"] != "WALL":
        continue

    if obj["entity"] == "LINE":
        points.append(tuple(obj["start"]))
        points.append(tuple(obj["end"]))

    elif obj["entity"] == "LWPOLYLINE":
        for p in obj["points"]:
            points.append(tuple(p))

distances = []

for i in range(len(points)):
    for j in range(i + 1, len(points)):

        d = hypot(
            points[i][0] - points[j][0],
            points[i][1] - points[j][1]
        )

        if 0 < d < 100:
            distances.append(d)

print("================================")
print("Topology Report")
print("================================")
print("Toplam Nokta :", len(points))
print("Yakın Çift :", len(distances))

if distances:
    print("Minimum :", round(min(distances), 3))
    print("Maximum :", round(max(distances), 3))
    print("Ortalama :", round(sum(distances) / len(distances), 3))

print("================================")