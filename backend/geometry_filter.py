import json
from math import hypot

JSON_FILE = r"C:\KaRar\outputs\villa1.json"

MIN_LENGTH = 50

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

filtered = []

removed = 0

for obj in data:

    if obj["type"] == "LINE":

        x1, y1 = obj["start"]
        x2, y2 = obj["end"]

        length = hypot(x2 - x1, y2 - y1)

        if length >= MIN_LENGTH:
            filtered.append(obj)
        else:
            removed += 1

    elif obj["type"] == "LWPOLYLINE":

        pts = obj["points"]

        if len(pts) < 2:
            removed += 1
            continue

        length = 0

        for i in range(len(pts) - 1):

            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]

            length += hypot(x2 - x1, y2 - y1)

        if length >= MIN_LENGTH:
            filtered.append(obj)
        else:
            removed += 1

with open(
    r"C:\KaRar\outputs\villa1_filtered.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        filtered,
        f,
        indent=4,
        ensure_ascii=False
    )

print("--------------------------------")
print("İlk Eleman :", len(data))
print("Kalan :", len(filtered))
print("Silinen :", removed)
print("villa1_filtered.json oluşturuldu")
print("--------------------------------")