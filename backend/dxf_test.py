import ezdxf

dosya = r"C:\KaRar\data\test_plan.dxf"

doc = ezdxf.readfile(dosya)
msp = doc.modelspace()

xler = []
yler = []

for entity in msp:

    if entity.dxf.layer != "Duvar":
        continue

    if entity.dxftype() == "LINE":

        xler.extend([entity.dxf.start.x, entity.dxf.end.x])
        yler.extend([entity.dxf.start.y, entity.dxf.end.y])

print("DUVAR SINIRLARI")
print("Min X:", min(xler))
print("Max X:", max(xler))
print("Min Y:", min(yler))
print("Max Y:", max(yler))