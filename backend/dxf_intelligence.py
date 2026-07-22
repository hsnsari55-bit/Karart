import ezdxf
from collections import Counter

DXF_FILE = r"C:\KaRar\data\test_plan.dxf"

doc = ezdxf.readfile(DXF_FILE)
msp = doc.modelspace()

entity_counter = Counter()
layer_counter = Counter()

print("===================================")
print("      KaRar DXF Intelligence")
print("===================================")

for entity in msp:

    entity_type = entity.dxftype()
    layer = entity.dxf.layer

    entity_counter[entity_type] += 1
    layer_counter[layer] += 1

print("\n===== ENTITYLER =====\n")

for name, count in entity_counter.most_common():
    print(f"{name:<15} : {count}")

print("\n===== LAYERLAR =====\n")

for name, count in layer_counter.most_common():
    print(f"{name:<30} : {count}")

print("\n===================================")
print("Toplam Entity :", sum(entity_counter.values()))
print("Toplam Layer  :", len(layer_counter))
print("===================================")