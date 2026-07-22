import json
from shapely.geometry import LineString
from shapely.ops import polygonize

INPUT = r"C:\KaRar\outputs\plan_only.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

lines = []

for obj in objects:

    if obj["category"] != "WALL":
        continue

    if obj["entity"] == "LINE":

        lines.append(
            LineString([
                obj["start"],
                obj["end"]
            ])
        )

    elif obj["entity"] == "LWPOLYLINE":

        pts = obj["points"]

        if len(pts) >= 2:
            lines.append(LineString(pts))

rooms = list(polygonize(lines))

print("====================================")
print("       Room Detector v2")
print("====================================")
print("Wall Line :", len(lines))
print("Room Aday :", len(rooms))

for i, room in enumerate(rooms[:10]):
    print(
        f"Oda {i+1} | Alan : {room.area:.2f}"
    )

print("====================================")