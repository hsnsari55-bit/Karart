import json
from sklearn.cluster import DBSCAN
import numpy as np

INPUT = r"C:\KaRar\outputs\bim_tjunction_fixed.json"
OUTPUT = r"C:\KaRar\outputs\plan_only.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

centers = []
valid_objects = []

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
    valid_objects.append(obj)

X = np.array(centers)

db = DBSCAN(
    eps=1200,
    min_samples=15
).fit(X)

labels = db.labels_

# En büyük kümeyi bul
counts = {}

for l in labels:
    if l == -1:
        continue
    counts[l] = counts.get(l, 0) + 1

largest_cluster = max(counts, key=counts.get)

plan = []

for obj, label in zip(valid_objects, labels):

    if label == largest_cluster:
        plan.append(obj)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=4, ensure_ascii=False)

print("====================================")
print("      Cluster Exporter")
print("====================================")
print("Seçilen Küme :", largest_cluster)
print("Obje Sayısı  :", len(plan))
print("Kaydedildi   :", OUTPUT)
print("====================================")