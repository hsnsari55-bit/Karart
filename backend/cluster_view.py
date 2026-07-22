import json
import matplotlib.pyplot as plt
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

model = DBSCAN(eps=1500, min_samples=10)
labels = model.fit_predict(points)

colors = {
    -1: "black",
    0: "blue",
    1: "red",
    2: "green",
    3: "orange"
}

plt.figure(figsize=(10,8))

for i, p in enumerate(points):
    plt.scatter(
        p[0],
        p[1],
        color=colors.get(labels[i], "purple"),
        s=10
    )

plt.gca().set_aspect("equal")
plt.title("KaRar - Villa Kümeleri")
plt.show()