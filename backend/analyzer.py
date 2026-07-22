import ezdxf
from classifier import classify
from collections import Counter
from config import DXF

DXF_FILE = str(DXF)

doc = ezdxf.readfile(DXF_FILE)
msp = doc.modelspace()

counter = Counter()

for entity in msp:

    category = classify(entity.dxf.layer)

    counter[category] += 1

print("\n==============================")

for name, count in sorted(counter.items()):
    print(f"{name:<15} : {count}")

print("==============================")