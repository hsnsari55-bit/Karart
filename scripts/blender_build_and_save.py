import runpy
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
BUILDER_SCRIPT = ROOT / "backend" / "blender_builder.py"
OUTPUT_BLEND = ROOT / "tmp_blender_preview.blend"


print("==========================================")
print(" KaRar Blender preview build+save script ")
print("==========================================")
print(f"Builder script: {BUILDER_SCRIPT}")
print(f"Output blend:   {OUTPUT_BLEND}")

runpy.run_path(str(BUILDER_SCRIPT), run_name="__main__")

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"Saved preview scene to: {OUTPUT_BLEND}")