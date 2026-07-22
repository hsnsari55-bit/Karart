import json
from math import hypot

INPUT = r"C:\KaRar\outputs\walls_normalized.json"
OUTPUT = r"C:\KaRar\outputs\walls_merged_v2.json"

ANGLE_TOL = 2.0
DIST_TOL = 20.0

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

walls = [w for w in walls if w["type"] == "LINE"]

def angle_diff(a, b):
    d = abs(a - b)
    return min(d, 180 - d)

merged = True

while merged:

    merged = False
    result = []
    used = [False] * len(walls)

    for i, w1 in enumerate(walls):

        if used[i]:
            continue

        sx, sy = w1["start"]
        ex, ey = w1["end"]
        ang = w1["angle"]

        for j, w2 in enumerate(walls):

            if i == j or used[j]:
                continue

            if angle_diff(ang, w2["angle"]) > ANGLE_TOL:
                continue

            p = [
                (sx, sy),
                (ex, ey),
                tuple(w2["start"]),
                tuple(w2["end"])
            ]

            best = None
            best_d = 1e9

            for a in p[:2]:
                for b in p[2:]:

                    d = hypot(a[0]-b[0], a[1]-b[1])

                    if d < best_d:
                        best_d = d
                        best = (a, b)

            if best_d > DIST_TOL:
                continue

            pts = p

            if abs(ex-sx) >= abs(ey-sy):

                pts.sort(key=lambda x: x[0])

            else:

                pts.sort(key=lambda x: x[1])

            sx, sy = pts[0]
            ex, ey = pts[-1]

            used[j] = True
            merged = True

        used[i] = True

        result.append({
            "id": len(result)+1,
            "type": "LINE",
            "start": [sx, sy],
            "end": [ex, ey],
            "angle": ang
        })

    walls = result

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(walls, f, indent=4, ensure_ascii=False)

print("====================================")
print("    WALL MERGE ENGINE V2")
print("====================================")
print("Yeni Wall :", len(walls))
print("Kaydedildi :", OUTPUT)
print("====================================")