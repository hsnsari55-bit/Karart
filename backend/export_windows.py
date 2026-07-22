import ezdxf
import json
from config import DXF

doc = ezdxf.readfile(DXF)
msp = doc.modelspace()

windows = []

WINDOW_LAYERS = [
    "pencere",
    "pen",
    "kapen",
    "kapı-pen",
    "kapi-pencere",
    "kapi___pencere",
    "k pencere",
    "doğrama",
    "cam"
]

for entity in msp:

    layer = entity.dxf.layer.lower()

    if layer not in WINDOW_LAYERS:
        continue

    if entity.dxftype() == "LINE":

        windows.append({
            "layer": entity.dxf.layer,
            "type": "LINE",
            "start": [
                entity.dxf.start.x,
                entity.dxf.start.y
            ],
            "end": [
                entity.dxf.end.x,
                entity.dxf.end.y
            ]
        })

    elif entity.dxftype() == "LWPOLYLINE":

        points = []

        for p in entity.get_points():
            points.append([p[0], p[1]])

        windows.append({
            "layer": entity.dxf.layer,
            "type": "LWPOLYLINE",
            "points": points
        })

with open(
    r"C:\KaRar\outputs\windows.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        windows,
        f,
        indent=4,
        ensure_ascii=False
    )

print("windows.json oluşturuldu")
print("Toplam pencere elemanı:", len(windows))