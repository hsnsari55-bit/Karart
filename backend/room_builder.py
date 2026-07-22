import json
from shapely.geometry import LineString
from shapely.ops import polygonize

INPUT = r"C:\KaRar\outputs\plan_only.json"
OUTPUT = r"C:\KaRar\outputs\rooms.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

lines = []

for obj in objects:

    if obj.get("category") != "WALL":
        continue

    if obj["entity"] == "LINE":

        lines.append(
            LineString([
                obj["start"],
                obj["end"]
            ])
        )

    elif obj["entity"] == "LWPOLYLINE":

        pts = obj.get("points", [])

        if len(pts) >= 2:
            lines.append(LineString(pts))

rooms = list(polygonize(lines))

result = []

for i, room in enumerate(rooms):

    result.append({
        "id": i + 1,
        "area": round(room.area, 2),
        "perimeter": round(room.length, 2),
        "center": [
            round(room.centroid.x, 2),
            round(room.centroid.y, 2)
        ],
        "boundary": [
            [round(x, 3), round(y, 3)]
            for x, y in room.exterior.coords
        ]
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4, ensure_ascii=False)

print("====================================")
print("        ROOM BUILDER")
print("====================================")
print("Room :", len(result))
print("Kaydedildi :", OUTPUT)
print("====================================")