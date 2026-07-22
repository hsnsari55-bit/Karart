import json

INPUT = r"C:\KaRar\outputs\walls_thickness.json"
OUTPUT = r"C:\KaRar\outputs\walls_normalized.json"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

xs = []
ys = []

for wall in walls:

    if wall["type"] != "LINE":
        continue

    xs.extend([wall["start"][0], wall["end"][0]])
    ys.extend([wall["start"][1], wall["end"][1]])

xmin = min(xs)
ymin = min(ys)

for wall in walls:

    if wall["type"] != "LINE":
        continue

    wall["start"][0] -= xmin
    wall["start"][1] -= ymin

    wall["end"][0] -= xmin
    wall["end"][1] -= ymin

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(walls, f, indent=4, ensure_ascii=False)

print("====================================")
print("    COORDINATE NORMALIZER")
print("====================================")
print("Wall :", len([w for w in walls if w['type']=='LINE']))
print("X Offset :", round(xmin,2))
print("Y Offset :", round(ymin,2))
print("Kaydedildi :", OUTPUT)
print("====================================")