import json
from sklearn.cluster import DBSCAN
import numpy as np

INPUT = r"C:\KaRar\outputs\bim_tjunction_fixed.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

centers = []
valid = []

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

    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2

    centers.append([cx, cy])
    valid.append(obj)

X = np.array(centers)

db = DBSCAN(
    eps=1200,
    min_samples=15
).fit(X)

labels = db.labels_

clusters = {}

for label in labels:

    clusters[label] = clusters.get(label, 0) + 1

print("====================================")
print("      Cluster Detector")
print("====================================")

for k, v in sorted(clusters.items()):
    print(f"Küme {k:>3} : {v}")

print("------------------------------------")
print("Toplam Küme :", len(clusters))
print("====================================")