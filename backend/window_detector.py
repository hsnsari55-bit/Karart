import json
import math
import ezdxf
import time
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Ensure project root is in sys.path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.path_manager import PathManager

pm = PathManager()

# Cross-platform memory usage
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# -----------------------------
# CONFIGURATION
# -----------------------------
DXF_PATH = pm.get_path('data', 'test_plan.dxf')
WALLS_PATH = pm.get_path('outputs', 'walls_normalized.json')
ROOMS_PATH = pm.get_path('outputs', 'rooms.json')
OUTPUT_WINDOWS = pm.get_path('outputs', 'windows.json')
OUTPUT_REPORT = pm.get_path('outputs', 'window_report.json')

# Window layers (from export_windows.py)
WINDOW_LAYERS = [
    "pencere",
    "pen",
    "kapen",
    "kapı-pen",
    "kapi-pencere",
    "kapi___pencere",
    "k pencere",
    "doğrama",
    "cam"
]

# Geometry types to consider
GEOMETRY_TYPES = ["LINE", "LWPOLYLINE", "POLYLINE", "ARC"]

# Minimum length filter (similar to geometry_filter)
MIN_LENGTH = 50

# Scale conversion (DXF units to mm)
DXF_SCALE_MM_PER_UNIT = 32.0

# Offsets for coordinate normalization (from coordinate_normalizer.py)
NORMALIZATION_X_OFFSET = 18274.87
NORMALIZATION_Y_OFFSET = 16346.3

# Maximum distance to consider a wall match (mm)
MAX_MATCH_DISTANCE = 5000.0

# Expected window width range (mm)
WINDOW_WIDTH_MIN = 500.0  # mm
WINDOW_WIDTH_MAX = 3000.0  # mm

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def dxf_to_mm(dxf_value: float) -> float:
    """Convert DXF units to real-world millimeters."""
    return dxf_value * DXF_SCALE_MM_PER_UNIT

def mm_to_dxf(mm_value: float) -> float:
    """Convert real-world millimeters to DXF units."""
    return mm_value / DXF_SCALE_MM_PER_UNIT

def normalize_point(x: float, y: float) -> Tuple[float, float]:
    """Apply coordinate normalization offset."""
    return (x - NORMALIZATION_X_OFFSET, y - NORMALIZATION_Y_OFFSET)

def compute_center(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Compute centroid of a set of points."""
    if not points:
        return (0.0, 0.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys))

def bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Compute bounding box of a set of points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return (min_x, min_y, max_x, max_y)

def orientation_from_angle(angle_rad: float) -> float:
    """Convert radians to degrees and normalize to [0, 360)."""
    deg = math.degrees(angle_rad) % 360
    return deg

def distance_point_to_segment(point: Tuple[float, float],
                              seg_start: Tuple[float, float],
                              seg_end: Tuple[float, float]) -> float:
    """Calculate shortest distance from point to line segment."""
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end

    # Vector from start to end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        # Segment is a point
        return math.dist(point, seg_start)

    # Parameter t for projection of point onto line
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))  # Clamp to segment

    # Projection point
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.dist(point, (proj_x, proj_y))

def point_in_polygon(point: Tuple[float, float],
                     polygon: List[Tuple[float, float]]) -> bool:
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

# -----------------------------
# ENTITY PROCESSING
# -----------------------------
def process_line_entity(entity: Any) -> Dict[str, Any]:
    """Process a LINE entity and compute window properties."""
    start = entity.dxf.start
    end = entity.dxf.end

    # Normalize coordinates
    start_norm = normalize_point(start.x, start.y)
    end_norm = normalize_point(end.x, end.y)

    # Compute center
    center = compute_center([start_norm, end_norm])

    # Compute length (width)
    length_dxf = math.dist(start, end)
    width_mm = dxf_to_mm(length_dxf)

    # Orientation (angle of the line)
    dx = end.x - start.x
    dy = end.y - start.y
    orientation_rad = math.atan2(dy, dx)
    orientation_deg = orientation_from_angle(orientation_rad)

    # Height not inferable for LINE
    height_mm = None

    # Confidence placeholder (will be refined after matching)
    confidence_placeholder = 1.0

    return {
        "entity_type": "LINE",
        "center": [round(center[0], 2), round(center[1], 2)],
        "width": round(width_mm, 2),
        "height": height_mm,
        "orientation": round(orientation_deg, 2),
        "confidence_placeholder": round(confidence_placeholder, 2)
    }

def process_lwpolyline_entity(entity: Any) -> Dict[str, Any]:
    """Process a LWPOLYLINE entity and compute window properties."""
    # get_points() returns tuples of (x, y, start_width, end_width, bulge)
    points_raw = entity.get_points()
    if not points_raw:
        return {}

    # Extract only x, y coordinates
    points_dxf = [(p[0], p[1]) for p in points_raw]

    # Normalize all points
    points_norm = [normalize_point(x, y) for x, y in points_dxf]

    # Compute center
    center = compute_center(points_norm)

    # Compute bounding box to get width and height
    min_x, min_y, max_x, max_y = bounding_box(points_norm)
    width_mm = dxf_to_mm(max_x - min_x)
    height_mm = dxf_to_mm(max_y - min_y)

    # Orientation: angle of the first segment
    x1, y1 = points_dxf[0]
    x2, y2 = points_dxf[1] if len(points_dxf) > 1 else points_dxf[0]
    dx = x2 - x1
    dy = y2 - y1
    orientation_rad = math.atan2(dy, dx)
    orientation_deg = orientation_from_angle(orientation_rad)

    # Shape factor based on aspect ratio
    aspect_ratio = width_mm / (height_mm or 1.0)
    shape_factor = 1.0 if 0.5 <= aspect_ratio <= 2.0 else 0.5

    # Size factor based on expected window dimensions
    size_factor = 1.0
    if not (WINDOW_WIDTH_MIN <= width_mm <= WINDOW_WIDTH_MAX):
        size_factor = 0.5

    # Placeholder confidence
    confidence_placeholder = shape_factor * size_factor

    return {
        "entity_type": "LWPOLYLINE",
        "center": [round(center[0], 2), round(center[1], 2)],
        "width": round(width_mm, 2),
        "height": round(height_mm, 2),
        "orientation": round(orientation_deg, 2),
        "confidence_placeholder": round(confidence_placeholder, 2)
    }

def process_polyline_entity(entity: Any) -> Dict[str, Any]:
    """Process a POLYLINE entity (similar to LWPOLYLINE)."""
    # For POLYLINE, vertices is a property that returns a list of vertex objects
    points_dxf = []
    for vertex in entity.vertices:
        points_dxf.append((vertex.dxf.location.x, vertex.dxf.location.y))
    if not points_dxf:
        return {}

    points_norm = [normalize_point(x, y) for x, y in points_dxf]
    center = compute_center(points_norm)
    min_x, min_y, max_x, max_y = bounding_box(points_norm)
    width_mm = dxf_to_mm(max_x - min_x)
    height_mm = dxf_to_mm(max_y - min_y)

    # Orientation: angle of first segment
    x1, y1 = points_dxf[0]
    x2, y2 = points_dxf[1] if len(points_dxf) > 1 else points_dxf[0]
    dx = x2 - x1
    dy = y2 - y1
    orientation_rad = math.atan2(dy, dx)
    orientation_deg = orientation_from_angle(orientation_rad)

    aspect_ratio = width_mm / (height_mm or 1.0)
    shape_factor = 1.0 if 0.5 <= aspect_ratio <= 2.0 else 0.5

    size_factor = 1.0
    if not (WINDOW_WIDTH_MIN <= width_mm <= WINDOW_WIDTH_MAX):
        size_factor = 0.5

    confidence_placeholder = shape_factor * size_factor

    return {
        "entity_type": "POLYLINE",
        "center": [round(center[0], 2), round(center[1], 2)],
        "width": round(width_mm, 2),
        "height": round(height_mm, 2),
        "orientation": round(orientation_deg, 2),
        "confidence_placeholder": round(confidence_placeholder, 2)
    }

def process_arc_entity(entity: Any) -> Dict[str, Any]:
    """Process an ARC entity and compute window properties."""
    center = (entity.dxf.center.x, entity.dxf.center.y)
    radius_dxf = entity.dxf.radius

    # Normalize center
    center_norm = normalize_point(center[0], center[1])

    # Compute start and end angles
    start_angle = entity.dxf.start_angle
    end_angle = entity.dxf.end_angle

    # Normalize angles to 0-360
    start_angle = start_angle % 360
    end_angle = end_angle % 360

    # Compute sweep angle (smallest angle between start and end)
    sweep = abs(end_angle - start_angle)
    if sweep > 180:
        sweep = 360 - sweep

    # Width (diameter) in mm
    width_mm = dxf_to_mm(radius_dxf) * 2.0
    height_mm = width_mm  # For arcs, width and height are the same (diameter)

    # Orientation: angle to the start point of the arc
    start_rad = math.radians(start_angle)
    orientation_rad = start_rad  # orientation relative to x-axis
    orientation_deg = orientation_from_angle(orientation_rad)

    # Confidence based on sweep angle (typical window arcs are ~90 or ~180)
    if 80 <= sweep <= 100 or 170 <= sweep <= 190:
        type_factor = 1.0
    else:
        type_factor = 0.5

    # Size factor based on expected window dimensions
    size_factor = 1.0
    if not (WINDOW_WIDTH_MIN <= width_mm <= WINDOW_WIDTH_MAX):
        size_factor = 0.5

    confidence_placeholder = type_factor * size_factor

    return {
        "entity_type": "ARC",
        "center": [round(center_norm[0], 2), round(center_norm[1], 2)],
        "width": round(width_mm, 2),
        "height": round(height_mm, 2),
        "orientation": round(orientation_deg, 2),
        "confidence_placeholder": round(confidence_placeholder, 2)
    }

# -----------------------------
# MATCHING AND WINDOW BUILDING
# -----------------------------
def match_to_wall(center: Tuple[float, float],
                  walls: List[Dict]) -> Optional[Dict]:
    """Find the nearest wall to the given center point."""
    min_dist = float('inf')
    best_wall = None

    for wall in walls:
        # Consider only LINE walls for matching (as in door detector)
        if wall.get("type") != "LINE":
            continue
        wall_start = (wall["start"][0], wall["start"][1])
        wall_end = (wall["end"][0], wall["end"][1])
        dist = distance_point_to_segment(center, wall_start, wall_end)
        if dist < min_dist:
            min_dist = dist
            best_wall = wall
    if best_wall is None:
        return None
    # Return wall dict with id
    return best_wall

def assign_room_to_window(center: Tuple[float, float],
                         rooms: List[Dict]) -> Optional[str]:
    """Assign a room ID to the window based on point-in-polygon test."""
    for room in rooms:
        if point_in_polygon(center, room["polygon"]):
            return room["id"]
    return None

# -----------------------------
# MAIN DETECTION PIPELINE
# -----------------------------
def main() -> None:
    """Main function to detect windows and export results."""
    # Load normalized walls
    with open(WALLS_PATH, "r", encoding="utf-8") as f:
        walls = json.load(f)

    # Load rooms if available
    rooms = []
    try:
        with open(ROOMS_PATH, "r", encoding="utf-8") as f:
            rooms = json.load(f)
        # Convert room boundaries to normalized coordinates
        for room in rooms:
            # Assuming room['polygon'] is already in normalized coordinates
            # If not, we would need to normalize them
            pass
    except FileNotFoundError:
        rooms = []

    # Load DXF file
    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()

    windows: List[Dict[str, Any]] = []
    ignored_candidates = 0

    # Track processing start time
    start_time = time.time()

    # Iterate over entities
    for entity in msp:
        layer = entity.dxf.layer.lower() if hasattr(entity.dxf, "layer") else ""
        if layer not in WINDOW_LAYERS:
            continue
        if entity.dxftype() not in GEOMETRY_TYPES:
            continue

        # Process entity based on type
        if entity.dxftype() == "LINE":
            window_data = process_line_entity(entity)
        elif entity.dxftype() == "LWPOLYLINE":
            window_data = process_lwpolyline_entity(entity)
        elif entity.dxftype() == "POLYLINE":
            window_data = process_polyline_entity(entity)
        elif entity.dxftype() == "ARC":
            window_data = process_arc_entity(entity)
        else:
            # Should not happen due to GEOMETRY_TYPES filter
            continue

        if not window_data:
            ignored_candidates += 1
            continue

        # Match to nearest wall
        center = tuple(window_data["center"])
        matched_wall = match_to_wall(center, walls)
        if matched_wall is None:
            ignored_candidates += 1
            continue
        wall_id = matched_wall.get("id")

        # Assign room if possible
        room_id = None
        if rooms:
            room_id = assign_room_to_window(center, [room for room in rooms])  # Simplify for now

        # Final confidence scoring
        # Compute distance to matched wall (we have min_dist from match_to_wall? We need to modify match_to_wall to return distance)
        # For now, recompute distance
        min_dist = float('inf')
        for wall in walls:
            if wall.get("type") != "LINE":
                continue
            w_start = (wall["start"][0], wall["start"][1])
            w_end = (wall["end"][0], wall["end"][1])
            dist = distance_point_to_segment(center, w_start, w_end)
            if dist < min_dist:
                min_dist = dist
        # Normalize distance to [0,1] range
        distance_factor = max(0.0, 1.0 - (min_dist / MAX_MATCH_DISTANCE))
        # Combine with size factor (using width)
        size_factor = 1.0
        width_mm = window_data["width"]
        if width_mm < WINDOW_WIDTH_MIN or width_mm > WINDOW_WIDTH_MAX:
            size_factor = 0.5
        # Combine factors
        final_confidence = round(distance_factor * size_factor, 2)

        # Build final window object
        window_obj = {
            "window_id": len(windows) + 1,
            "wall_id": wall_id,
            "room_id": room_id,
            "center": window_data["center"],
            "width": window_data["width"],
            "height": window_data["height"],
            "orientation": window_data["orientation"],
            "confidence_score": final_confidence
        }
        windows.append(window_obj)

    # Processing end time
    end_time = time.time()
    processing_time = round(end_time - start_time, 3)

    # Compute memory usage (peak RSS in KB) - cross-platform
    if HAS_PSUTIL:
        process = psutil.Process()
        mem_usage_kb = round(process.memory_info().rss / 1024)
    else:
        # Fallback: use a reasonable estimate
        mem_usage_kb = 0

    # Write windows to JSON
    with open(OUTPUT_WINDOWS, "w", encoding="utf-8") as f:
        json.dump(windows, f, indent=4, ensure_ascii=False)

    # Generate window report
    total_windows = len(windows)
    # Compute confidence statistics
    if windows:
        confidences = [w["confidence_score"] for w in windows]
        avg_confidence = sum(confidences) / len(confidences)
        conf_min = min(confidences)
        conf_max = max(confidences)
        conf_std = (sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)) ** 0.5
        confidence_stats = {
            "mean": round(avg_confidence, 3),
            "min": round(conf_min, 3),
            "max": round(conf_max, 3),
            "std": round(conf_std, 3)
        }
    else:
        confidence_stats = {
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std": 0.0
        }

    # Average width
    avg_width = (sum(w["width"] for w in windows) / total_windows) if total_windows > 0 else 0.0
    avg_width_rounded = round(avg_width, 2)

    # Build report
    report = {
        "total_windows": total_windows,
        "confidence_stats": confidence_stats,
        "ignored_candidates": ignored_candidates,
        "average_width": avg_width_rounded,
        "processing_time_seconds": processing_time,
        "memory_usage_kb": mem_usage_kb
    }

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    print("====================================")
    print("      WINDOW DETECTION ENGINE")
    print("====================================")
    print(f"Detected windows: {total_windows}")
    print(f"Ignored candidates: {ignored_candidates}")
    print(f"Output: {OUTPUT_WINDOWS}")
    print(f"Report: {OUTPUT_REPORT}")
    print("====================================")

if __name__ == "__main__":
    main()