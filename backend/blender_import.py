import bpy
import json
import math

# -------------------------------
# JSON DOSYASI
# -------------------------------
JSON_FILE = r"C:\KaRar\outputs\villa1.json"

# -------------------------------
# SAHNEYİ TEMİZLE
# -------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# -------------------------------
# JSON OKU
# -------------------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    walls = json.load(f)

SCALE = 0.001

created = 0

for wall in walls:

    if wall["type"] != "LINE":
        continue

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    x1 *= SCALE
    y1 *= SCALE
    x2 *= SCALE
    y2 *= SCALE

    dx = x2 - x1
    dy = y2 - y1

    length = math.sqrt(dx * dx + dy * dy)

    angle = math.atan2(dy, dx)

    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    bpy.ops.mesh.primitive_cube_add(
        location=(cx, cy, 1.5)
    )

    obj = bpy.context.object

    obj.scale.x = length / 2
    obj.scale.y = 0.10
    obj.scale.z = 1.50

    obj.rotation_euler[2] = angle

    created += 1

print("--------------------------------")
print("Duvar oluşturuldu :", created)
print("--------------------------------")