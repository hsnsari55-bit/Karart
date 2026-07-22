import json
import matplotlib.pyplot as plt

with open(r"C:\KaRar\outputs\walls.json", "r", encoding="utf-8") as f:
    walls = json.load(f)

plt.figure(figsize=(10, 8))

for wall in walls:
    if wall["type"] == "LINE":
        x1, y1 = wall["start"]
        x2, y2 = wall["end"]

        plt.plot([x1, x2], [y1, y2])

plt.gca().set_aspect("equal")
plt.title("KaRar - Duvarlar")
plt.show()