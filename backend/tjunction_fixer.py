import json
from shapely.geometry import LineString, Point
from shapely.ops import split

INPUT = r"C:\KaRar\outputs\bim_no_duplicates.json"
OUTPUT = r"C:\KaRar\outputs\bim_tjunction_fixed.json"

# ======================================

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

wall_lines = []
others = []

for obj in objects:

    if obj["category"] == "WALL" and obj["entity"] == "LINE":

        wall_lines.append({
            "object": obj,
            "line": LineString([
                obj["start"],
                obj["end"]
            ])
        })

    else:
        others.append(obj)

# ======================================

new_objects = []

for i, target in enumerate(wall_lines):

    current = target["line"]
    split_points = []

    for j, other in enumerate(wall_lines):

        if i == j:
            continue

        inter = current.intersection(other["line"])

        if inter.is_empty:
            continue

        if inter.geom_type != "Point":
            continue

        p = (inter.x, inter.y)

        if p == tuple(current.coords[0]):
            continue

        if p == tuple(current.coords[-1]):
            continue

        split_points.append(Point(p))

    if not split_points:

        new_objects.append(target["object"])
        continue

    pieces = [current]

    for pt in split_points:

        temp = []

        for seg in pieces:

            try:
                result = split(seg, pt)

                if len(result.geoms) > 1:
                    temp.extend(result.geoms)
                else:
                    temp.append(seg)

            except:
                temp.append(seg)

        pieces = temp

    for seg in pieces:

        coords = list(seg.coords)

        obj = {
            "category": "WALL",
            "entity": "LINE",
            "layer": target["object"]["layer"],
            "start": list(coords[0]),
            "end": list(coords[-1])
        }

        new_objects.append(obj)

# ======================================

new_objects.extend(others)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(new_objects, f, indent=4, ensure_ascii=False)

print("====================================")
print("      T Junction Fixer")
print("====================================")
print("Eski WALL :", len(wall_lines))
print("Yeni WALL :", len([o for o in new_objects if o['category']=='WALL']))
print("Toplam Obj :", len(new_objects))
print("Kaydedildi :", OUTPUT)
print("====================================")