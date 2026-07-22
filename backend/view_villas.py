import json
import matplotlib.pyplot as plt

def draw(file_name, color):

    with open(file_name, "r", encoding="utf-8") as f:
        walls = json.load(f)

    for wall in walls:

        if wall["type"] == "LINE":

            x1, y1 = wall["start"]
            x2, y2 = wall["end"]

            plt.plot([x1, x2], [y1, y2], color=color)

        elif wall["type"] == "LWPOLYLINE":

            xs = []
            ys = []

            for p in wall["points"]:
                xs.append(p[0])
                ys.append(p[1])

            plt.plot(xs, ys, color=color)

draw(r"C:\KaRar\outputs\villa1.json", "blue")
draw(r"C:\KaRar\outputs\villa2.json", "red")

plt.gca().set_aspect("equal")
plt.title("KaRar - Villa 1 / Villa 2")
plt.show()