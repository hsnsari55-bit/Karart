import bpy
import json
import os
import math

print("==========================================")
print("     KaRar 3D İnşa & Delme Motoru Devrede...")
print("==========================================")

# 1. Sahneyi temizle
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Sabit Ölçüler (Metre cinsinden)
DUVAR_YUKSEKLIK = 2.8
DUVAR_KALINLIK = 0.2
KAPI_YUKSEKLIK = 2.1
PENCERE_YUKSEKLIK = 1.2
PENCERE_ALT_BOSLUK = 0.9 # Yerden yüksekliği

# OLCU BIRIMI AYARI (Santimetre -> Metre)
# AutoCAD'de 1 birim 1 cm çizildiği için 100'e bölüyoruz. (Önceki 1000'di, o yüzden ev presleniyordu!)
OLCEK = 100

# Dosya Yolları
yol_duvar = r"C:\KaRar\outputs\walls.json"
yol_kapi = r"C:\KaRar\outputs\doors.json"
yol_pencere = r"C:\KaRar\outputs\windows.json"

orulen_duvarlar = []
kesici_objeler = []

# ==========================================
# 1. AŞAMA: DUVARLARI ÖR
# ==========================================
if os.path.exists(yol_duvar):
    with open(yol_duvar, "r", encoding="utf-8") as f:
        walls = json.load(f)
    
    for idx, wall in enumerate(walls):
        if "start" in wall and "end" in wall:
            x1, y1 = wall["start"][0] / OLCEK, wall["start"][1] / OLCEK
            x2, y2 = wall["end"][0] / OLCEK, wall["end"][1] / OLCEK
            
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = math.atan2(y2 - y1, x2 - x1)
            
            if length < 0.01: continue
                
            bpy.ops.mesh.primitive_cube_add(location=(mid_x, mid_y, DUVAR_YUKSEKLIK / 2))
            duvar = bpy.context.active_object
            duvar.name = f"Duvar_{idx}"
            duvar.scale = (DUVAR_KALINLIK / 2, length / 2, DUVAR_YUKSEKLIK / 2)
            duvar.rotation_euler[2] = angle + math.radians(90)
            orulen_duvarlar.append(duvar)

# ==========================================
# 2. AŞAMA: KAPILARI DEL (Cutter Oluştur)
# ==========================================
if os.path.exists(yol_kapi):
    with open(yol_kapi, "r", encoding="utf-8") as f:
        doors = json.load(f)
        
    for idx, door in enumerate(doors):
        x, y = 0, 0
        genislik = door.get("width", 90) / OLCEK # Varsayılan 90cm
        
        # Kapının orta noktasını bul
        if door["type"] == "ARC":
            x, y = door["center"][0] / OLCEK, door["center"][1] / OLCEK
        elif door["type"] == "LINE":
            x = ((door["start"][0] + door["end"][0]) / 2) / OLCEK
            y = ((door["start"][1] + door["end"][1]) / 2) / OLCEK
            
        # Görünmez kesici küpü oluştur (Duvarı delecek alet)
        bpy.ops.mesh.primitive_cube_add(location=(x, y, KAPI_YUKSEKLIK / 2))
        cutter = bpy.context.active_object
        cutter.name = f"Kapi_Delici_{idx}"
        # Duvarı tam kesmesi için kalınlığı abartıyoruz (0.5m)
        cutter.scale = (0.5, genislik / 2, KAPI_YUKSEKLIK / 2) 
        cutter.display_type = 'WIRE' # Ekranda sadece tel çerçeve görünsün
        kesici_objeler.append(cutter)

# ==========================================
# 3. AŞAMA: PENCERELERİ DEL (Cutter Oluştur)
# ==========================================
if os.path.exists(yol_pencere):
    with open(yol_pencere, "r", encoding="utf-8") as f:
        windows = json.load(f)
        
    for idx, win in enumerate(windows):
        if win["type"] == "LINE":
            x1, y1 = win["start"][0] / OLCEK, win["start"][1] / OLCEK
            x2, y2 = win["end"][0] / OLCEK, win["end"][1] / OLCEK
            
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            genislik = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = math.atan2(y2 - y1, x2 - x1)
            
            # Pencere kesici küpü (Yerden yüksekte)
            z_konum = PENCERE_ALT_BOSLUK + (PENCERE_YUKSEKLIK / 2)
            bpy.ops.mesh.primitive_cube_add(location=(mid_x, mid_y, z_konum))
            cutter = bpy.context.active_object
            cutter.name = f"Pencere_Delici_{idx}"
            cutter.scale = (0.5, genislik / 2, PENCERE_YUKSEKLIK / 2)
            cutter.rotation_euler[2] = angle + math.radians(90)
            cutter.display_type = 'WIRE'
            kesici_objeler.append(cutter)

# ==========================================
# 4. AŞAMA: BOOLEAN (FARK) İŞLEMİNİ UYGULA
# ==========================================
for duvar in orulen_duvarlar:
    for cutter in kesici_objeler:
        # Her duvara boolean modifier ekle
        bool_mod = duvar.modifiers.new(type='BOOLEAN', name=f"Kes_{cutter.name}")
        bool_mod.object = cutter
        bool_mod.operation = 'DIFFERENCE'

print("🚀 3D Duvarlar örüldü, Kapı ve Pencereler başarıyla delindi!")
