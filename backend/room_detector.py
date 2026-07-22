import json
import math
import os
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union
from collections import defaultdict

print("==========================================")
print("     KaRar Oda Tespit Motoru Devrede...")
print("==========================================")

# -----------------------------
# DİNAMİK DOSYA YOLLARI (Klasör Nereye Giderse Gitsin Çalışır)
# -----------------------------
# Scriptin çalıştığı 'backend' klasörünün bir üst dizinini ana proje klasörü olarak bul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Eğer outputs klasörü yoksa otomatik oluştur
os.makedirs(OUTPUT_DIR, exist_ok=True)

INPUT_FILE = os.path.join(OUTPUT_DIR, "walls.json")
OUTPUT_ROOMS_FILE = os.path.join(OUTPUT_DIR, "rooms.json")
OUTPUT_REPORT_FILE = os.path.join(OUTPUT_DIR, "room_report.json")

# Snap tolerance for connecting wall endpoints (in DXF units)
SNAP_TOLERANCE = 5.0  # Adjust based on DXF scale

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def find_cluster_center(points):
    """Find the center of a cluster of points."""
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys))

def snap_walls(walls, tolerance):
    """Snap wall endpoints to create connected topology."""
    endpoints = []
    for wall in walls:
        if "start" in wall and "end" in wall:
            endpoints.append(tuple(wall["start"]))
            endpoints.append(tuple(wall["end"]))
    
    clusters = []
    used = set()
    
    for i, point in enumerate(endpoints):
        if i in used:
            continue
        
        cluster = [point]
        used.add(i)
        
        for j, other_point in enumerate(endpoints):
            if j in used:
                continue
            dist = math.sqrt((point[0] - other_point[0])**2 + (point[1] - other_point[1])**2)
            if dist <= tolerance:
                cluster.append(other_point)
                used.add(j)
        
        clusters.append(cluster)
    
    snap_dict = {}
    for cluster in clusters:
        center = find_cluster_center(cluster)
        for point in cluster:
            snap_dict[point] = center
    
    snapped_walls = []
    for wall in walls:
        if "start" in wall and "end" in wall:
            start = tuple(wall["start"])
            end = tuple(wall["end"])
            
            snapped_start = snap_dict.get(start, start)
            snapped_end = snap_dict.get(end, end)
            
            if snapped_start == snapped_end:
                continue
                
            snapped_wall = wall.copy()
            snapped_wall["start"] = list(snapped_start)
            snapped_wall["end"] = list(snapped_end)
            snapped_walls.append(snapped_wall)
    
    return snapped_walls

# -----------------------------
# LOAD WALLS
# -----------------------------
if not os.path.exists(INPUT_FILE):
    print(f"❌ HATA: {INPUT_FILE} bulunamadı. Önce duvarların çıkarılması gerekiyor.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    walls = json.load(f)

print(f"📥 {len(walls)} adet duvar çizgisi yüklendi.")

# -----------------------------
# SNAP WALLS TO FIX TOPOLOGY
# -----------------------------
walls = snap_walls(walls, SNAP_TOLERANCE)
print(f"🧲 Mıknatıs (Snap) işlemi sonrası: {len(walls)} duvar")

wall_lookup = {}
for wall in walls:
    if "start" in wall and "end" in wall:
        start = tuple(wall["start"])
        end = tuple(wall["end"])
        wall_lookup[(start, end)] = wall.get("id", "")
        wall_lookup[(end, start)] = wall.get("id", "")

lines = []

# -----------------------------
# COLLECT LINES
# -----------------------------
for wall in walls:
    if "start" not in wall or "end" not in wall:
        continue

    x1, y1 = wall["start"]
    x2, y2 = wall["end"]
    lines.append(LineString([(x1, y1), (x2, y2)]))

# -----------------------------
# FIND CLOSED POLYGONS (ROOMS)
# -----------------------------
polygons = list(polygonize(lines))

print("--------------------------------")
print(f"🏠 Tespit Edilen Kapalı Alan (Oda) Sayısı: {len(polygons)}")
print("--------------------------------")

# -----------------------------
# PROCESS ROOMS
# -----------------------------
rooms = []

for i, poly in enumerate(polygons):
    area_mm2 = poly.area
    perimeter_mm = poly.length
    center = poly.centroid
    
    # Gerçek dünya ölçülerine çevirme (DXF mm bazlı olduğu varsayımıyla)
    area_m2 = area_mm2 / 1000000.0
    perimeter_m = perimeter_mm / 1000.0
    
    polygon_coords = list(poly.exterior.coords)
    
    wall_ids = []
    for j in range(len(polygon_coords) - 1):
        start = polygon_coords[j]
        end = polygon_coords[j + 1]
        if (start, end) in wall_lookup:
            wall_ids.append(wall_lookup[(start, end)])
        elif (end, start) in wall_lookup:
            wall_ids.append(wall_lookup[(end, start)])
    
    seen = set()
    unique_wall_ids = []
    for wid in wall_ids:
        if wid not in seen:
            seen.add(wid)
            unique_wall_ids.append(wid)

    room_id = f'room_{i+1}'

    rooms.append({
        'id': room_id,
        'wall_ids': unique_wall_ids,
        'polygon': polygon_coords, # Koordinatlar veri bozulmasın diye orijinal bırakıldı
        'area_m2': round(area_m2, 2),
        'perimeter_m': round(perimeter_m, 2),
        'center': [round(center.x, 2), round(center.y, 2)]
    })

# -----------------------------
# EXPORT ROOMS
# -----------------------------
with open(OUTPUT_ROOMS_FILE, 'w', encoding='utf-8') as f:
    json.dump(rooms, f, indent=4, ensure_ascii=False)

# -----------------------------
# GENERATE REPORT
# -----------------------------
if rooms:
    areas = [room['area_m2'] for room in rooms]
    largest_room = max(rooms, key=lambda x: x['area_m2'])
    smallest_room = min(rooms, key=lambda x: x['area_m2'])
    average_area = sum(areas) / len(areas)
else:
    areas = []
    largest_room = None
    smallest_room = None
    average_area = 0

report = {
    'total_rooms': len(rooms),
    'room_areas_m2': areas,
    'largest_room_id': largest_room['id'] if largest_room else None,
    'largest_room_area_m2': largest_room['area_m2'] if largest_room else 0,
    'smallest_room_id': smallest_room['id'] if smallest_room else None,
    'smallest_room_area_m2': smallest_room['area_m2'] if smallest_room else 0,
    'average_area_m2': round(average_area, 2)
}

with open(OUTPUT_REPORT_FILE, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=4, ensure_ascii=False)

# Print summary
for room in rooms:
    print(f"📌 {room['id'].capitalize()} | Alan: {room['area_m2']} m² | Çevre: {room['perimeter_m']} m")

print("--------------------------------")
print("✅ Oda tespit işlemi ve raporlama başarıyla tamamlandı!")
