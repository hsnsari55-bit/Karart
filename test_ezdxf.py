import ezdxf
try:
    doc = ezdxf.readfile('data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf', encoding='cp1254')
    print("Normal success:", len(doc.modelspace()))
except Exception as e:
    print("Normal cp1254 failed:", e)
