import json

INPUT = r"C:\KaRar\outputs\bim_model.json"
OUTPUT = r"C:\KaRar\outputs\blender_scene.py"

with open(INPUT, "r", encoding="utf-8") as f:
    bim = json.load(f)

script = []

script.append("import bpy")
script.append("")
script.append("bpy.ops.object.select_all(action='SELECT')")
script.append("bpy.ops.object.delete(use_global=False)")
script.append("")

for wall in bim["walls"]:

    if wall["type"] != "LINE":
        continue

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]

    script.append(f"# WALL {wall['id']}")
    script.append("bpy.ops.mesh.primitive_cube_add()")
    script.append("obj=bpy.context.object")
    script.append(f"obj.name='Wall_{wall['id']}'")
    script.append(f"obj.location=({((x1+x2)/2)/1000:.3f},{((y1+y2)/2)/1000:.3f},1.5)")
    script.append("obj.scale=(0.10,0.10,1.50)")
    script.append("")

for column_id, column in enumerate(bim["columns"], start=1):

    x, y = column["center"]

    script.append(f"# COLUMN {column_id}")
    script.append("bpy.ops.mesh.primitive_cube_add()")
    script.append("obj=bpy.context.object")
    script.append(f"obj.name='Column_{column_id}'")
    script.append(f"obj.location=({x/1000:.3f},{y/1000:.3f},1.5)")
    script.append("obj.scale=(0.20,0.20,1.50)")
    script.append("")

for door_id, door in enumerate(bim["doors"], start=1):

    x, y = door["center"]

    script.append(f"# DOOR {door_id}")
    script.append("bpy.ops.object.empty_add(type='CUBE')")
    script.append("obj=bpy.context.object")
    script.append(f"obj.name='Door_{door_id}'")
    script.append(f"obj.location=({x/1000:.3f},{y/1000:.3f},1.0)")
    script.append("")

for window_id, window in enumerate(bim["windows"], start=1):

    x, y = window["center"]

    script.append(f"# WINDOW {window_id}")
    script.append("bpy.ops.object.empty_add(type='PLAIN_AXES')")
    script.append("obj=bpy.context.object")
    script.append(f"obj.name='Window_{window_id}'")
    script.append(f"obj.location=({x/1000:.3f},{y/1000:.3f},1.2)")
    script.append("")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(script))

print("====================================")
print("      BLENDER EXPORTER")
print("====================================")
print("Walls   :", len(bim["walls"]))
print("Doors   :", len(bim["doors"]))
print("Windows :", len(bim["windows"]))
print("Columns :", len(bim["columns"]))
print("------------------------------------")
print("Kaydedildi :", OUTPUT)
print("====================================")