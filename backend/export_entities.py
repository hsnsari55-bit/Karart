import ezdxf
import json
from classifier import classify

DXF_FILE = r"C:\KaRar\data\test_plan.dxf"
OUTPUT = r"C:\KaRar\outputs\entities.json"

doc = ezdxf.readfile(DXF_FILE)
msp = doc.modelspace()

entities = []

for entity in msp:

    entities.append({

        "type": entity.dxftype(),
        "layer": entity.dxf.layer,
        "category": classify(entity.dxf.layer)

    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(entities, f, indent=4, ensure_ascii=False)

print("--------------------------------")
print("Toplam :", len(entities))
print("Çıktı :", OUTPUT)
print("--------------------------------")