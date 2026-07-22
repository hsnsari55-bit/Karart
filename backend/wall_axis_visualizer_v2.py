import json
import matplotlib.pyplot as plt

INPUT = r"C:\KaRar\outputs\wall_axis_v2.json"

with open(INPUT, "r", encoding="utf-8") as f:
    axes = json.load(f)

plt.figure(figsize=(14, 10))

for axis in axes:

    x1, y1 = axis["start"]
    x2, y2 = axis["end"]

    plt.plot(
        [x1, x2],
        [y1, y2],
        linewidth=2
    )

    plt.scatter(
        axis["center"][0],
        axis["center"][1],
        s=8
    )

plt.gca().set_aspect("equal")
plt.title(f"KaRar Wall Axis V2 ({len(axes)} Axis)")
plt.grid(True)

print("====================================")
print("    WALL AXIS VISUALIZER V2")
print("====================================")
print("Axis :", len(axes))
print("Pencere Açılıyor...")
print("====================================")

plt.show()