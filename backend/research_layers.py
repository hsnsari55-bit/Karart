import ezdxf
from pathlib import Path
from collections import Counter

# data klasöründeki ilk DXF dosyasını otomatik bul
data_dir = Path(r"C:\KaRar\data")
dxf_files = list(data_dir.glob("*.dxf"))

if not dxf_files:
    raise FileNotFoundError("C:\\KaRar\\data içinde DXF bulunamadı!")

DXF = dxf_files[0]

print("=" * 60)
print("DXF :", DXF)
print("=" * 60)

doc = ezdxf.readfile(str(DXF))
msp = doc.modelspace()

layers = Counter()

for entity in msp:
    layer = entity.dxf.layer
    etype = entity.dxftype()
    layers[(layer, etype)] += 1

print("\n===== LAYER ANALİZİ =====\n")

for (layer, etype), count in sorted(layers.items()):
    print(f"{layer:40} {etype:15} {count}")

print("\nToplam Layer/Entity :", len(layers))