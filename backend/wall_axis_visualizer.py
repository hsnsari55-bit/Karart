import json
import matplotlib.pyplot as plt

INPUT = r"C:\KaRar\outputs\wall_axis.json"

with open(INPUT, "r", encoding="utf-8") as f:
    axes = json.load(f)

plt.figure(figsize=(12, 8))

for axis in axes:

    x1, y1 = axis["start"]
    x2, y2 = axis["end"]

    plt.plot(
        [x1, x2],
        [y1, y2],
        linewidth=1
    )

plt.gca().set_aspect("equal")
plt.title("KaRar Wall Axis")
plt.grid(True)

print("====================================")
print("   WALL AXIS VISUALIZER")
print("====================================")
print("Axis :", len(axes))
print("Pencere açılıyor...")
print("====================================")

plt.show()