import os
import sys
import ezdxf

def create_reference_dxf(filepath: str, btype: str, width: float, height: float, rooms_count: int):
    """
    Programmatically generates a realistic architectural DXF floor plan with:
    - Walls (duvar)
    - Columns (kolon)
    - Doors (kapı)
    - Windows (k pencere)
    """
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    
    # Define layers
    doc.layers.new(name='duvar', dxfattribs={'color': 1}) # Red
    doc.layers.new(name='kolon', dxfattribs={'color': 2}) # Yellow
    doc.layers.new(name='kapı', dxfattribs={'color': 3}) # Green
    doc.layers.new(name='k pencere', dxfattribs={'color': 4}) # Blue
    doc.layers.new(name='tefriş', dxfattribs={'color': 8}) # Gray
    
    # 1. External boundaries (outer walls)
    msp.add_line((0, 0), (width, 0), dxfattribs={'layer': 'duvar'})
    msp.add_line((width, 0), (width, height), dxfattribs={'layer': 'duvar'})
    msp.add_line((width, height), (0, height), dxfattribs={'layer': 'duvar'})
    msp.add_line((0, height), (0, 0), dxfattribs={'layer': 'duvar'})
    
    # 2. Add structural Columns at corners and intersections
    col_width, col_height = 400.0, 400.0 # mm
    column_points = [
        (0, 0), (width - col_width, 0),
        (0, height - col_height), (width - col_width, height - col_height)
    ]
    
    # Add an internal wall dividing the space based on rooms_count
    for r in range(1, rooms_count):
        x_div = (width / rooms_count) * r
        msp.add_line((x_div, 0), (x_div, height), dxfattribs={'layer': 'duvar'})
        # Add column at intersection
        column_points.append((x_div - col_width/2, 0))
        column_points.append((x_div - col_width/2, height - col_height))
        
        # Add a door in each divider wall
        door_y = height / 3
        msp.add_line((x_div - 50, door_y), (x_div + 50, door_y + 100), dxfattribs={'layer': 'kapı'})
        
    for cx, cy in column_points:
        pts = [
            (cx, cy),
            (cx + col_width, cy),
            (cx + col_width, cy + col_height),
            (cx, cy + col_height),
            (cx, cy)
        ]
        msp.add_lwpolyline(pts, format='xy', dxfattribs={'layer': 'kolon', 'closed': True})
        
    # 3. Add Windows on outer walls
    window_width = 1200.0
    # Window 1 on bottom wall
    w1_start = width / 4 - window_width / 2
    msp.add_line((w1_start, 0), (w1_start + window_width, 0), dxfattribs={'layer': 'k pencere'})
    # Window 2 on top wall
    w2_start = (width * 3) / 4 - window_width / 2
    msp.add_line((w2_start, height), (w2_start + window_width, height), dxfattribs={'layer': 'k pencere'})
    
    # Save the generated file
    doc.saveas(filepath)

def main():
    dest_dir = "data/reference_set"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Defining 20 different architectural project variants
    building_types = [
        ("konut_standard", 12000, 10000, 3),   # Standard Residential Apartment
        ("konut_luks", 18000, 12000, 4),       # Luxury Apartment Flat
        ("villa_dublex", 14000, 11000, 3),     # Doublex Villa Ground Floor
        ("villa_triplex", 15000, 12000, 4),    # Triplex Villa Main Floor
        ("ofis_openplan", 20000, 15000, 2),    # Open Plan Office Floor
        ("ofis_bento", 16000, 12000, 4),       # Bento-style Office Suite
        ("hastane_clinic", 22000, 14000, 5),   # Medical Clinic Section
        ("hastane_emergency", 25000, 16000, 6),# Emergency Room Ward
        ("okul_siniflar", 24000, 12000, 4),    # School Classrooms Floor
        ("okul_idari", 18000, 10000, 3),       # School Administrative Block
        ("otel_kat", 30000, 10000, 6),         # Typical Hotel Guest Rooms Floor
        ("otel_suite", 20000, 12000, 3),       # Luxury Suite Hotel Floor
        ("restoran_bistro", 15000, 15000, 2),  # Bistro Restaurant Interior
        ("restoran_mutfak", 12000, 8000, 2),   # Restaurant Kitchen/Storage
        ("spor_gym", 25000, 20000, 2),         # Gymnasium Fitness Center
        ("muze_gallery", 30000, 18000, 3),     # Art Museum Exhibition Gallery
        ("kutuphane_calisma", 20000, 14000, 3),# Library Study Hall
        ("lab_kimya", 16000, 10000, 3),        # Chemical Laboratory Floor
        ("kafe_shop", 10000, 8000, 2),         # Coffe Shop / Patisserie
        ("market_gida", 20000, 12000, 2)       # Grocery Market Layout
    ]
    
    print(f"Creating {len(building_types)} programmatically generated CAD DXF plans under {dest_dir}...")
    for idx, (btype, w, h, rooms) in enumerate(building_types, 1):
        filename = f"{idx:02d}_{btype}.dxf"
        filepath = os.path.join(dest_dir, filename)
        create_reference_dxf(filepath, btype, w, h, rooms)
        print(f"  [{idx}/20] Successfully created {filepath} ({w}x{h} mm, {rooms} rooms)")
        
    print("\n[OK] 20 high-fidelity reference projects generated successfully.")

if __name__ == "__main__":
    main()
