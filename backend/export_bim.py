import ezdxf
import json

from classifier import classify

# ======================================
# DOSYALAR
# ======================================

DXF_FILE = r"C:\KaRar\data\test_plan.dxf"
OUTPUT_FILE = r"C:\KaRar\outputs\bim.json"

# ======================================
# DXF OKU
# ======================================

doc = ezdxf.readfile(DXF_FILE)
msp = doc.modelspace()

objects = []

# ======================================
# ENTITYLER
# ======================================

for entity in msp:

    obj = {
        "category": classify(entity.dxf.layer),
        "layer": entity.dxf.layer,
        "entity": entity.dxftype()
    }

    # Handle
    try:
        obj["handle"] = entity.dxf.handle
    except:
        obj["handle"] = ""

    # ---------------- LINE ----------------

    if entity.dxftype() == "LINE":

        obj["start"] = [
            entity.dxf.start.x,
            entity.dxf.start.y
        ]

        obj["end"] = [
            entity.dxf.end.x,
            entity.dxf.end.y
        ]

    # ------------- LWPOLYLINE -------------

    elif entity.dxftype() == "LWPOLYLINE":

        pts = []

        for p in entity.get_points():

            pts.append([
                p[0],
                p[1]
            ])

        obj["points"] = pts
        obj["closed"] = entity.closed

    # ======================================

    objects.append(obj)

# ======================================
# JSON KAYDET
# ======================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        objects,
        f,
        indent=4,
        ensure_ascii=False
    )

# ======================================

print("--------------------------------")
print("BIM Object :", len(objects))
print("Saved :", OUTPUT_FILE)
print("--------------------------------")