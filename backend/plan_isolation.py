import json
from collections import Counter

INPUT = r"C:\KaRar\outputs\bim_tjunction_fixed.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

# Bounding Box hesapla
boxes = []

for obj in objects:

    pts = []

    if obj["entity"] == "LINE":
        pts = [obj["start"], obj["end"]]

    elif obj["entity"] == "LWPOLYLINE":
        pts = obj.get("points", [])

    if not pts:
        continue

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    boxes.append((
        min(xs),
        min(ys),
        max(xs),
        max(ys)
    ))

print("====================================")
print("     Plan Isolation Analyzer")
print("====================================")
print("Geometri Sayısı :", len(boxes))

xmin = min(b[0] for b in boxes)
ymin = min(b[1] for b in boxes)
xmax = max(b[2] for b in boxes)
ymax = max(b[3] for b in boxes)

print()
print("GLOBAL BOUNDING BOX")
print("--------------------")
print("X Min :", xmin)
print("Y Min :", ymin)
print("X Max :", xmax)
print("Y Max :", ymax)

print()
print("Genişlik :", round(xmax - xmin,2))
print("Yükseklik:", round(ymax - ymin,2))

print("====================================")