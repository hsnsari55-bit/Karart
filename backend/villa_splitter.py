import json
from sklearn.cluster import DBSCAN

with open(
    r"C:\KaRar\outputs\walls.json",
    "r",
    encoding="utf-8"
) as f:
    walls = json.load(f)

points = []

for wall in walls:

    if wall["type"] == "LINE":

        x = (wall["start"][0] + wall["end"][0]) / 2
        y = (wall["start"][1] + wall["end"][1]) / 2

    else:

        xs = [p[0] for p in wall["points"]]
        ys = [p[1] for p in wall["points"]]

        x = sum(xs) / len(xs)
        y = sum(ys) / len(ys)

    points.append([x, y])

model = DBSCAN(
    eps=1500,
    min_samples=10
)

labels = model.fit_predict(points)

clusters = {}

for i, label in enumerate(labels):

    if label not in clusters:
        clusters[label] = 0

    clusters[label] += 1

print("\nKümeler:\n")

for label, count in clusters.items():
    print(f"Küme {label}: {count} eleman")