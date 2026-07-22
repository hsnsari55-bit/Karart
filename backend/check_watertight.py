import json
import trimesh

scene = trimesh.load("outputs/model.glb", force="scene")
geometries = scene.geometry
for name, geom in geometries.items():
    if not geom.is_watertight:
        print(f"Non-watertight mesh found: {name}")

