import ezdxf
from collections import defaultdict

DXF = r"C:\KaRar\data\test_plan.dxf"

doc = ezdxf.readfile(DXF)
msp = doc.modelspace()

layers = defaultdict(int)
entities = defaultdict(int)
blocks = defaultdict(int)

for e in msp:

    entities[e.dxftype()] += 1

    try:
        layers[e.dxf.layer] += 1
    except:
        pass

    if e.dxftype() == "INSERT":
        blocks[e.dxf.name] += 1

print("====================================")
print("      PROJECT ANALYZER")
print("====================================")

print("\nEN ÇOK KULLANILAN LAYER")
print("------------------------------")

for name, count in sorted(layers.items(), key=lambda x:x[1], reverse=True)[:20]:
    print(f"{name:<25} {count}")

print("\nEN ÇOK KULLANILAN BLOCK")
print("------------------------------")

for name, count in sorted(blocks.items(), key=lambda x:x[1], reverse=True)[:30]:
    print(f"{name:<30} {count}")

print("\nENTITYLER")
print("------------------------------")

for name, count in sorted(entities.items()):
    print(f"{name:<20} {count}")

print("====================================")