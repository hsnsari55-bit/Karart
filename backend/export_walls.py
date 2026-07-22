import ezdxf
import json
from config import DXF, OUTPUT_DIR

print("==========================================")
print("     KaRar Duvar Çıkarıcı Devrede")
print("==========================================")

DXF_FILE = str(DXF)
# Çıktı adı düzeltildi (room_detector.py'nin aradığı isim)
OUTPUT = OUTPUT_DIR / "walls.json" 

doc = ezdxf.readfile(DXF_FILE)
msp = doc.modelspace()

walls = []

# SADECE GERÇEK DUVARLAR
for entity in msp:
    layer = entity.dxf.layer.strip().lower()
    
    # Katman adı 'duvar' değilse atla
    if layer != "duvar":
        continue
        
    # Eğer tekli çizgi (LINE) ise
    if entity.dxftype() == "LINE":
        walls.append({
            "type": "LINE",
            "layer": entity.dxf.layer,
            "start": [entity.dxf.start.x, entity.dxf.start.y],
            "end": [entity.dxf.end.x, entity.dxf.end.y]
        })
        
    # Eğer birleşik çizgi (LWPOLYLINE) ise
    elif entity.dxftype() == "LWPOLYLINE":
        points = list(entity.get_points())
        # Birleşik çizgiyi, oda bulucunun anlayacağı start/end parçalarına böl
        for i in range(len(points) - 1):
            walls.append({
                "type": "LINE", 
                "layer": entity.dxf.layer,
                "start": [points[i][0], points[i][1]],
                "end": [points[i+1][0], points[i+1][1]]
            })
        # Çizgi kapalı (closed) olarak çizildiyse, son noktayı ilk noktaya bağla
        if entity.closed and len(points) > 2:
             walls.append({
                "type": "LINE",
                "layer": entity.dxf.layer,
                "start": [points[-1][0], points[-1][1]],
                "end": [points[0][0], points[0][1]]
            })

# KAYDET
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(walls, f, indent=4, ensure_ascii=False)

print("--------------------------------")
print(f"Duvar Çizgisi Sayısı : {len(walls)}")
print(f"Çıktı : {OUTPUT}")
print("--------------------------------")
