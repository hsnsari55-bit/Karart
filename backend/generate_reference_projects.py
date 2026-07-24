import os
import sys
import math
import ezdxf

def create_reference_dxf(
    filepath: str,
    btype: str,
    width: float,
    height: float,
    rooms_count: int,
    vendor: str = "AutoCAD",
    classification: str = "CLASS_A",
    coord_offset: tuple = (0.0, 0.0),
    angle_deg: float = 0.0
):
    """
    Programmatically generates realistic multi-vendor architectural DXF floor plans.
    Supports Class A-D difficulty classifications, CAD vendor signatures, coordinate shifts,
    and micro-drafting noise characteristics for P1 Benchmark Pool Expansion.
    """
    # Create DXF doc with vendor header attributes
    version_map = {
        "AutoCAD": "R2010",
        "BricsCAD": "R2010",
        "ZWCAD": "R2007",
        "DraftSight": "R2010",
        "LibreCAD": "R2004"
    }
    dxf_ver = version_map.get(vendor, "R2010")
    doc = ezdxf.new(dxfversion=dxf_ver)
    msp = doc.modelspace()
    
    # Vendor signature setup
    
    # Layer naming conventions according to vendor and classification
    if classification == "CLASS_C":
        wall_layer = "0" if vendor == "LibreCAD" else "WALL_UNSTRUCTURED"
        col_layer = "COLUMNS_EXPLODED"
        door_layer = "DOOR_RAW"
        win_layer = "WINDOW_RAW"
    else:
        wall_layer = "duvar" if vendor in ["AutoCAD", "BricsCAD"] else "A-WALL"
        col_layer = "kolon" if vendor in ["AutoCAD", "BricsCAD"] else "S-COL"
        door_layer = "kapı" if vendor in ["AutoCAD", "BricsCAD"] else "A-DOOR"
        win_layer = "k pencere" if vendor in ["AutoCAD", "BricsCAD"] else "A-GLAZ"

    doc.layers.new(name=wall_layer, dxfattribs={'color': 1})
    if col_layer != wall_layer:
        doc.layers.new(name=col_layer, dxfattribs={'color': 2})
    if door_layer != wall_layer:
        doc.layers.new(name=door_layer, dxfattribs={'color': 3})
    if win_layer != wall_layer:
        doc.layers.new(name=win_layer, dxfattribs={'color': 4})
        
    ox, oy = coord_offset
    rad = math.radians(angle_deg)
    
    def transform(x: float, y: float) -> tuple:
        """Applies coordinate offset and non-orthogonal rotation skew."""
        if angle_deg != 0.0:
            rx = x * math.cos(rad) - y * math.sin(rad)
            ry = x * math.sin(rad) + y * math.cos(rad)
            x, y = rx, ry
        return (round(x + ox, 3), round(y + oy, 3))

    # 1. External boundaries (outer walls)
    p00 = transform(0, 0)
    pW0 = transform(width, 0)
    pWH = transform(width, height)
    p0H = transform(0, height)
    
    if classification == "CLASS_B":
        # Introduce micro-gap / collinear split in bottom wall
        mid_x = width / 2
        pMid1 = transform(mid_x - 2.0, 0) # 2mm micro gap
        pMid2 = transform(mid_x + 2.0, 0)
        msp.add_line(p00, pMid1, dxfattribs={'layer': wall_layer})
        msp.add_line(pMid2, pW0, dxfattribs={'layer': wall_layer})
    else:
        msp.add_line(p00, pW0, dxfattribs={'layer': wall_layer})
        
    msp.add_line(pW0, pWH, dxfattribs={'layer': wall_layer})
    msp.add_line(pWH, p0H, dxfattribs={'layer': wall_layer})
    msp.add_line(p0H, p00, dxfattribs={'layer': wall_layer})
    
    # 2. Add structural Columns at corners and internal wall intersections
    col_w, col_h = 400.0, 400.0
    column_points = [
        (0, 0), (width - col_w, 0),
        (0, height - col_h), (width - col_w, height - col_h)
    ]
    
    # Internal dividing walls based on rooms_count
    for r in range(1, rooms_count):
        x_div = (width / rooms_count) * r
        p_bottom = transform(x_div, 0)
        p_top = transform(x_div, height)
        msp.add_line(p_bottom, p_top, dxfattribs={'layer': wall_layer})
        
        column_points.append((x_div - col_w / 2, 0))
        column_points.append((x_div - col_w / 2, height - col_h))
        
        # Add door in divider wall
        door_y = height / 3
        d1 = transform(x_div - 50, door_y)
        d2 = transform(x_div + 50, door_y + 100)
        msp.add_line(d1, d2, dxfattribs={'layer': door_layer})
        
    for cx, cy in column_points:
        pts = [
            transform(cx, cy),
            transform(cx + col_w, cy),
            transform(cx + col_w, cy + col_h),
            transform(cx, cy + col_h),
            transform(cx, cy)
        ]
        msp.add_lwpolyline(pts, format='xy', dxfattribs={'layer': col_layer, 'closed': True})
        
    # 3. Add Windows on outer walls
    win_w = 1200.0
    w1_start = width / 4 - win_w / 2
    w1_p1 = transform(w1_start, 0)
    w1_p2 = transform(w1_start + win_w, 0)
    msp.add_line(w1_p1, w1_p2, dxfattribs={'layer': win_layer})
    
    w2_start = (width * 3) / 4 - win_w / 2
    w2_p1 = transform(w2_start, height)
    w2_p2 = transform(w2_start + win_w, height)
    msp.add_line(w2_p1, w2_p2, dxfattribs={'layer': win_layer})
    
    doc.saveas(filepath)

def main():
    dest_dir = "data/reference_set"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Multi-vendor project templates (100 multi-vendor DXF benchmark projects)
    building_archetypes = [
        ("konut_standard", 12000, 10000, 3),
        ("konut_luks", 18000, 12000, 4),
        ("villa_dublex", 14000, 11000, 3),
        ("villa_triplex", 15000, 12000, 4),
        ("ofis_openplan", 20000, 15000, 2),
        ("ofis_bento", 16000, 12000, 4),
        ("hastane_clinic", 22000, 14000, 5),
        ("hastane_emergency", 25000, 16000, 6),
        ("okul_siniflar", 24000, 12000, 4),
        ("okul_idari", 18000, 10000, 3),
        ("otel_kat", 30000, 10000, 6),
        ("otel_suite", 20000, 12000, 3),
        ("restoran_bistro", 15000, 15000, 2),
        ("restoran_mutfak", 12000, 8000, 2),
        ("spor_gym", 25000, 20000, 2),
        ("muze_gallery", 30000, 18000, 3),
        ("kutuphane_calisma", 20000, 14000, 3),
        ("lab_kimya", 16000, 10000, 3),
        ("kafe_shop", 10000, 8000, 2),
        ("market_gida", 20000, 12000, 2)
    ]
    
    # 100 benchmark specifications matching P1 Vendor/Class distribution
    specs = []
    
    # 001 - 040: AutoCAD (40 projects)
    for i in range(1, 41):
        arch = building_archetypes[(i - 1) % len(building_archetypes)]
        cls = "CLASS_A" if i <= 25 else ("CLASS_B" if i <= 35 else "CLASS_C")
        offset = (0.0, 0.0) if cls != "CLASS_D" else (100000.0, 100000.0)
        specs.append((f"{i:03d}_{arch[0]}_acad", arch[0], arch[1], arch[2], arch[3], "AutoCAD", cls, offset, 0.0))
        
    # 041 - 060: BricsCAD (20 projects)
    for i in range(41, 61):
        arch = building_archetypes[(i - 1) % len(building_archetypes)]
        cls = "CLASS_A" if i <= 52 else "CLASS_B"
        specs.append((f"{i:03d}_{arch[0]}_brics", arch[0], arch[1], arch[2], arch[3], "BricsCAD", cls, (0.0, 0.0), 0.0))
        
    # 061 - 075: ZWCAD / StarCAD (15 projects)
    for i in range(61, 76):
        arch = building_archetypes[(i - 1) % len(building_archetypes)]
        cls = "CLASS_A" if i <= 70 else "CLASS_C"
        specs.append((f"{i:03d}_{arch[0]}_zwcad", arch[0], arch[1], arch[2], arch[3], "ZWCAD", cls, (0.0, 0.0), 0.0))
        
    # 076 - 090: DraftSight (15 projects - including UTM coordinate offsets)
    for i in range(76, 91):
        arch = building_archetypes[(i - 1) % len(building_archetypes)]
        cls = "CLASS_A" if i <= 83 else "CLASS_D"
        offset = (5000000.0, 2000000.0) if cls == "CLASS_D" else (0.0, 0.0)
        specs.append((f"{i:03d}_{arch[0]}_draftsight", arch[0], arch[1], arch[2], arch[3], "DraftSight", cls, offset, 0.0))
        
    # 091 - 100: LibreCAD & Open Source (10 projects - including non-orthogonal angle skew)
    for i in range(91, 101):
        arch = building_archetypes[(i - 1) % len(building_archetypes)]
        cls = "CLASS_A" if i <= 96 else "CLASS_D"
        angle = 0.8 if cls == "CLASS_D" else 0.0
        specs.append((f"{i:03d}_{arch[0]}_librecad", arch[0], arch[1], arch[2], arch[3], "LibreCAD", cls, (0.0, 0.0), angle))

    print(f"Generating {len(specs)} multi-vendor CAD DXF benchmark drawings under {dest_dir}...")
    for idx, (fname, btype, w, h, rooms, vendor, cls, offset, angle) in enumerate(specs, 1):
        filepath = os.path.join(dest_dir, f"{fname}.dxf")
        create_reference_dxf(filepath, btype, w, h, rooms, vendor, cls, offset, angle)
        if idx % 10 == 0 or idx == len(specs):
            print(f"  [{idx}/{len(specs)}] Created {filepath} ({vendor}, {cls}, {w}x{h}mm)")
            
    print(f"\n[OK] {len(specs)} multi-vendor reference benchmark projects generated successfully.")

if __name__ == "__main__":
    main()

