import ezdxf

DXF = r"C:\KaRar\data\test_plan.dxf"

doc = ezdxf.readfile(DXF)

print("====================================")
print("          CAD AUDIT")
print("====================================")

print("BLOCK SAYISI :", len(doc.blocks))

print()

for block in doc.blocks:

    if block.name.startswith("*"):
        continue

    print("--------------------------------")
    print(block.name)

    counts = {}

    for e in block:

        t = e.dxftype()
        counts[t] = counts.get(t, 0) + 1

    for k, v in sorted(counts.items()):
        print(f"{k:<15} {v}")

print("====================================")