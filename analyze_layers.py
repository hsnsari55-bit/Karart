import ezdxf
import json

dxf_path = r"data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

layers = {}
for e in msp:
    layer = e.dxf.layer
    if layer not in layers:
        layers[layer] = 0
    layers[layer] += 1

sorted_layers = dict(sorted(layers.items(), key=lambda x: x[1], reverse=True)[:30])
print(json.dumps(sorted_layers, indent=2, ensure_ascii=False))
