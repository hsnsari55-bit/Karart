import ezdxf

doc = ezdxf.readfile(r"C:\KaRar\data\test_plan.dxf")
msp = doc.modelspace()

print("=== INSERT ANALİZİ ===\n")

sayac = 0

for entity in msp:
    if entity.dxftype() == "INSERT":
        sayac += 1

        print(f"INSERT #{sayac}")
        print(f"Blok Adı : {entity.dxf.name}")
        print(f"Katman   : {entity.dxf.layer}")
        print(f"Konum    : ({entity.dxf.insert.x:.2f}, {entity.dxf.insert.y:.2f})")
        print("-" * 40)

print(f"\nToplam INSERT: {sayac}")