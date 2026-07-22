import json
from math import atan2, degrees, radians, hypot

INPUT = r"C:\KaRar\outputs\walls_thickness.json"
OUTPUT = r"C:\KaRar\outputs\wall_mesh.py"

with open(INPUT, "r", encoding="utf-8") as f:
    walls = json.load(f)

script = []

script.append("import bpy")
script.append("from math import radians")
script.append("")
script.append("bpy.ops.object.select_all(action='SELECT')")
script.append("bpy.ops.object.delete(use_global=False)")
script.append("")

count = 0

for wall in walls:

    if wall["type"] != "LINE":
        continue

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2

    length = hypot(x2 - x1, y2 - y1) / 1000

    thickness = wall.get("thickness")

    if thickness is None:
        thickness = 200

    thickness /= 1000

    angle = wall.get("angle", 0)

    script.append("bpy.ops.mesh.primitive_cube_add()")
    script.append("obj=bpy.context.object")
    script.append(f"obj.name='Wall_{wall['id']}'")
    script.append(
        f"obj.location=({mx/1000:.3f},{my/1000:.3f},1.500)"
    )
    script.append(
        f"obj.scale=({length/2:.3f},{thickness/2:.3f},1.500)"
    )
    script.append(
        f"obj.rotation_euler=(0,0,radians({angle:.3f}))"
    )
    script.append("")

    count += 1

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(script))

print("====================================")
print("      WALL MESH GENERATOR")
print("====================================")
print("Mesh Wall :", count)
print("Kaydedildi :", OUTPUT)
print("====================================")