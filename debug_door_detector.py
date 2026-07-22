#!/usr/bin/env python3

import ezdxf
import json
import math
from typing import List, Dict, Any, Optional, Tuple

# Configuration
DXF_PATH = r'C:/KaRar/data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf'
WALLS_PATH = r'C:/KaRar/outputs/walls_normalized.json'
ROOMS_PATH = r'C:/KaRar/outputs/rooms.json'
OUTPUT_PATH = r'C:/KaRar/outputs/doors.json'
REPORT_PATH = r'C:/KaRar/outputs/door_report.json'

# Coordinate offset to align DXF door coordinates with normalized wall coordinates
# From coordinate_normalizer.py: X Offset = 18274.87, Y Offset = 16346.3
NORMALIZATION_X_OFFSET = 18274.87
NORMALIZATION_Y_OFFSET = 16346.3

# Door layers to consider (based on actual DXF investigation)
DOOR_LAYERS = [
    'kapı', 'kapi', 'kapi___pencere', 'kapi ve pencereler', 'kapı ve pencereler',
    'KAPI VE PENCERELER', 'kap�'  # Handle encoding issue
]

# Geometry types to consider
GEOMETRY_TYPES = ['LINE', 'LWPOLYLINE', 'ARC']

# Door detection parameters (real-world mm)
MIN_DOOR_WIDTH = 50    # Minimum door width in mm (adjusted for actual door sizes seen in DXF)
MAX_DOOR_WIDTH = 1500  # Maximum door width in mm (reasonable maximum for door widths)
MIN_ARC_RADIUS = 50    # Minimum arc radius for door swing (mm)
MAX_ARC_RADIUS = 1500  # Maximum arc radius for door swing (mm)
MIN_ARC_SWEEP = 30     # Minimum sweep angle for door arc (degrees) - more permissive for door swings
MAX_ARC_SWEEP = 180    # Maximum sweep angle for door arc (degrees) - allow full swings
WALL_MATCH_DISTANCE_THRESHOLD = 5000  # Maximum distance to consider a wall match (mm) - increased for better matching after coordinate normalization

# DXF scale conversion (based on analysis: ~32 mm per DXF unit)
DXF_SCALE_MM_PER_UNIT = 32.0  # mm per DXF unit

def dxf_to_mm(dxf_value: float) -> float:
    """Convert DXF units to real-world millimeters."""
    return dxf_value * DXF_SCALE_MM_PER_UNIT

def mm_to_dxf(mm_value: float) -> float:
    """Convert real-world millimeters to DXF units."""
    return mm_value / DXF_SCALE_MM_PER_UNIT

# Convert door detection parameters to DXF units for internal comparison
MIN_DOOR_WIDTH_DXF = mm_to_dxf(MIN_DOOR_WIDTH)
MAX_DOOR_WIDTH_DXF = mm_to_dxf(MAX_DOOR_WIDTH)
MIN_ARC_RADIUS_DXF = mm_to_dxf(MIN_ARC_RADIUS)
MAX_ARC_RADIUS_DXF = mm_to_dxf(MAX_ARC_RADIUS)

def main():
    """Main function to detect doors and generate outputs."""
    print("Loading walls and rooms...")
    walls = load_walls(WALLS_PATH)
    rooms = load_rooms(ROOMS_PATH)
    
    print(f"Loaded {len(walls)} walls and {len(rooms)} rooms")
    
    print("Processing DXF for door entities...")
    door_entities = get_door_entities(DXF_PATH)
    
    print(f"Found {len(door_entities)} raw door candidates")
    
    doors = []
    ignored_candidates = 0
    door_id = 1
    
    for i, entity in enumerate(door_entities):
        print(f"\nProcessing entity {i+1}:")
        print(f"  Layer: {entity.dxf.layer}")
        print(f"  Type: {entity.dxftype()}")
        
        # Process entity to get door properties
        door_data = process_door_entity(entity)
        if door_data is None:
            print(f"  -> Failed to process entity")
            ignored_candidates += 1
            continue
        
        print(f"  -> Processed: center={door_data['center']}, width={door_data['width']:.2f} DXF units, swing={door_data['swing_angle']:.2f}°")
        
        # Convert door measurements to real-world mm for validation
        width_mm = dxf_to_mm(door_data['width'])
        print(f"  -> Width in mm: {width_mm:.2f}")
        
        # Validate door width
        if width_mm < MIN_DOOR_WIDTH or width_mm > MAX_DOOR_WIDTH:
            print(f"  -> Width out of range ({MIN_DOOR_WIDTH}-{MAX_DOOR_WIDTH} mm)")
            ignored_candidates += 1
            continue
        
        # For arcs, validate swing angle
        if entity.dxftype() == 'ARC':
            sweep = door_data['swing_angle']
            if sweep < MIN_ARC_SWEEP or sweep > MAX_ARC_SWEEP:
                print(f"  -> Sweep angle out of range ({MIN_ARC_SWEEP}-{MAX_ARC_SWEEP}°)")
                ignored_candidates += 1
                continue
        
        # Match to nearest wall
        wall_id = match_to_wall(door_data['center'], walls)
        if wall_id is None:
            print(f"  -> No wall match found")
            ignored_candidates += 1
            continue
        
        print(f"  -> Matched to wall ID: {wall_id}")
        
        # Assign room
        room_id = assign_room_to_door(door_data['center'], rooms)
        print(f"  -> Assigned to room ID: {room_id}")
        
        # Classify door type (Single/Double)
        door_type = classify_door_type(entity, door_data)
        print(f"  -> Classified as: {door_type}")
        
        # Build final door object
        door_obj = {
            'id': door_id,
            'wall_id': wall_id,
            'room_id': room_id,
            'center': door_data['center'],
            'width': width_mm,  # Store in real-world mm
            'swing_angle': door_data['swing_angle'],
            'orientation': door_data['orientation'],
            'type': door_type
        }
        doors.append(door_obj)
        door_id += 1
        print(f"  -> Door added successfully!")
    
    # Save doors to JSON
    save_doors(doors, OUTPUT_PATH)
    
    # Generate and save report
    generate_report(doors, ignored_candidates, REPORT_PATH)
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully detected {len(doors)} doors")
    print(f"Ignored {ignored_candidates} candidates")
    print(f"Doors saved to {OUTPUT_PATH}")
    print(f"Report saved to {REPORT_PATH}")

def load_walls(filepath: str) -> List[Dict]:
    """Load walls from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_rooms(filepath: str) -> List[Dict]:
    """Load rooms from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_door_entities(dxf_path: str) -> List[Any]:
    """Extract LINE, LWPOLYLINE, and ARC entities from door layers."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    entities = []
    
    for entity in msp:
        # Case-insensitive layer matching
        entity_layer = entity.dxf.layer
        layer_match = False
        
        for door_layer in DOOR_LAYERS:
            if entity_layer.lower() == door_layer.lower():
                layer_match = True
                break
        
        if not layer_match:
            continue
            
        if entity.dxftype() not in GEOMETRY_TYPES:
            continue
        entities.append(entity)
    
    return entities

def process_door_entity(entity: Any) -> Optional[Dict]:
    """Process a door entity and compute its properties."""
    try:
        if entity.dxftype() == 'LINE':
            return process_line(entity)
        elif entity.dxftype() == 'LWPOLYLINE':
            return process_lwpolyline(entity)
        elif entity.dxftype() == 'ARC':
            return process_arc(entity)
    except Exception as e:
        print(f"Error processing entity: {e}")
        return None
    return None

def process_line(entity: Any) -> Dict:
    """Process a LINE entity."""
    start = entity.dxf.start
    end = entity.dxf.end
    center_x = (start[0] + end[0]) / 2 - NORMALIZATION_X_OFFSET
    center_y = (start[1] + end[1]) / 2 - NORMALIZATION_Y_OFFSET
    center = [center_x, center_y]
    width = math.dist(start, end)  # Length of the line in DXF units
    # For a line, we assume it represents the door width (e.g., a threshold line)
    swing_angle = 0  # Lines don't have swing angle
    # Orientation is the angle of the line
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    orientation = math.degrees(math.atan2(dy, dx)) % 360
    
    return {
        'center': center,
        'width': width,  # Still in DXF units, will be converted later
        'swing_angle': swing_angle,
        'orientation': orientation
    }

def process_lwpolyline(entity: Any) -> Dict:
    """Process an LWPOLYLINE entity."""
    points = [tuple(p) for p in entity.get_points()]
    if not points:
        return None
    
    # Compute center as average of points
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    center = [sum(xs) / len(xs), sum(ys) / len(ys)]
    
    # Compute width as the maximum dimension of bounding box
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    width = max(width, height)  # Take the larger dimension
    
    # For polyline, we assume it's a door frame (no swing)
    swing_angle = 0
    # Orientation: we'll compute the dominant direction (simplified)
    orientation = 0  # Placeholder
    
    return {
        'center': center,
        'width': width,  # Still in DXF units
        'swing_angle': swing_angle,
        'orientation': orientation
    }

def process_arc(entity: Any) -> Optional[Dict]:
    """Process an ARC entity."""
    center = [entity.dxf.center[0], entity.dxf.center[1]]
    radius = entity.dxf.radius  # Still in DXF units
    start_angle = entity.dxf.start_angle
    end_angle = entity.dxf.end_angle
    
    # Normalize angles to 0-360
    start_angle = start_angle % 360
    end_angle = end_angle % 360
    
    # Compute sweep angle (smallest angle between start and end)
    sweep = abs(end_angle - start_angle)
    if sweep > 180:
        sweep = 360 - sweep
    
    # For an arc, width is the radius (door width equals swing radius)
    width = radius
    # Swing angle is the sweep angle
    swing_angle = sweep
    # Orientation: angle to the start point of the arc
    dx = entity.dxf.center[0] + radius * math.cos(math.radians(start_angle)) - entity.dxf.center[0]
    dy = entity.dxf.center[1] + radius * math.sin(math.radians(start_angle)) - entity.dxf.center[1]
    orientation = math.degrees(math.atan2(dy, dx)) % 360
    
    return {
        'center': center,
        'width': width,  # Still in DXF units
        'swing_angle': sweep,
        'orientation': orientation
    }

def match_to_wall(door_center: List[float], walls: List[Dict]) -> Optional[int]:
    """Find the nearest wall to the door center."""
    min_dist = float('inf')
    best_wall_id = None
    
    for wall in walls:
        # Use layer to identify walls (all walls have layer="wall")
        if wall.get('layer') != 'wall':
            continue
        
        wall_start = wall['start']
        wall_end = wall['end']
        dist = point_to_line_segment_distance(door_center, wall_start, wall_end)
        
        if dist < min_dist:
            min_dist = dist
            best_wall_id = wall['id']
    
    # Convert distance threshold to DXF units for comparison
    max_dist_dxf = mm_to_dxf(WALL_MATCH_DISTANCE_THRESHOLD)
    
    if min_dist > max_dist_dxf:
        return None
    
    return best_wall_id

def point_to_line_segment_distance(point: List[float], 
                                   line_start: List[float], 
                                   line_end: List[float]) -> float:
    """Calculate the shortest distance from a point to a line segment."""
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Vector from line start to end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        # Line segment is a point
        return math.dist(point, line_start)
    
    # Parameter t for projection of point onto line
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))  # Clamp to line segment
    
    # Projection point
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    
    return math.dist(point, [proj_x, proj_y])

def assign_room_to_door(door_center: List[float], rooms: List[Dict]) -> Optional[int]:
    """Assign a room ID to the door based on point-in-polygon test."""
    for room in rooms:
        if point_in_polygon(door_center, room['boundary']):
            return room['id']
    return None

def point_in_polygon(point: List[float], polygon: List[List[float]]) -> bool:
    """Ray casting algorithm to check if point is inside polygon."""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def classify_door_type(entity: Any, door_data: Dict) -> str:
    """Classify door as Single or Double."""
    if entity.dxftype() == 'ARC':
        sweep = door_data['swing_angle']
        # Typical single door swing: 90 degrees (range 80-100)
        if 80 <= sweep <= 100:
            return 'Single'
        # Double door might be represented as two 90-degree arcs (not detectable per entity)
        # or sometimes as a 180-degree arc (less common for doors)
        elif 170 <= sweep <= 190:
            return 'Double'
        else:
            # Default to single for arcs that don't match typical swings
            return 'Single'
    else:
        # For LINE and LWPOLYLINE, we assume single door (no reliable way to detect double)
        return 'Single'

def save_doors(doors: List[Dict], filepath: str) -> None:
    """Save doors to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(doors, f, indent=4, ensure_ascii=False)

def generate_report(doors: List[Dict], ignored_candidates: int, filepath: str) -> None:
    """Generate door report JSON."""
    total_doors = len(doors)
    single_doors = sum(1 for d in doors if d['type'] == 'Single')
    double_doors = sum(1 for d in doors if d['type'] == 'Double')
    avg_width = sum(d['width'] for d in doors) / total_doors if total_doors > 0 else 0
    
    report = {
        'total doors': total_doors,
        'single doors': single_doors,
        'double doors': double_doors,
        'average width': round(avg_width, 2),
        'ignored candidates': ignored_candidates
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    main()