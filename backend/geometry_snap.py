import json
from math import hypot

INPUT = r"C:\KaRar\outputs\villa1_filtered.json"
OUTPUT = r"C:\KaRar\outputs\villa1_snapped.json"

SNAP_DISTANCE = 5.0

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

points = []

for obj in data:

    if obj["type"] == "LINE":
        points.append(obj["start"])
        points.append(obj["end"])

    elif obj["type"] == "LWPOLYLINE":
        points.extend(obj["points"])

clusters = []

for p in points:

    found = False

    for c in clusters:

        if hypot(p[0] - c[0], p[1] - c[1]) <= SNAP_DISTANCE:
            found = True
            break

    if not found:
        clusters.append(p)

def snap(pt):

    best = pt
    best_d = SNAP_DISTANCE

    for c in clusters:

        d = hypot(pt[0] - c[0], pt[1] - c[1])

        if d < best_d:
            best = c
            best_d = d

    return best

for obj in data:

    if obj["type"] == "LINE":

        obj["start"] = list(snap(obj["start"]))
        obj["end"] = list(snap(obj["end"]))

    elif obj["type"] == "LWPOLYLINE":

        obj["points"] = [list(snap(p)) for p in obj["points"]]

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("--------------------------------")
print("İlk Nokta :", len(points))
print("Snap Nokta :", len(clusters))
print("villa1_snapped.json oluşturuldu")
print("--------------------------------")