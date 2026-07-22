import math
from typing import List, Tuple, Dict
from backend.geometry_engine import GeometryEngine

engine = GeometryEngine()
walls = engine.run()
print(f"Original wall segments: {len(walls)}")

def is_collinear(p1, p2, p3, angle_tol=2.5):
    v1_x = p2[0] - p1[0]
    v1_y = p2[1] - p1[1]
    len1 = math.hypot(v1_x, v1_y)
    
    v2_x = p3[0] - p2[0]
    v2_y = p3[1] - p2[1]
    len2 = math.hypot(v2_x, v2_y)
    
    if len1 < 1e-5 or len2 < 1e-5: return True
    
    dot = (v1_x * v2_x + v1_y * v2_y) / (len1 * len2)
    dot = max(-1.0, min(1.0, dot))
    angle = math.degrees(math.acos(dot))
    return angle < angle_tol or (180.0 - angle) < angle_tol

def distance(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

# Basic line merging algorithm
def merge_collinear_segments(segments, tol_dist=5.0):
    merged = []
    used = [False] * len(segments)
    
    for i in range(len(segments)):
        if used[i]: continue
        
        current_pts = segments[i]['points']
        c_p0 = tuple(current_pts[0])
        c_p1 = tuple(current_pts[1])
        
        grown = True
        while grown:
            grown = False
            for j in range(len(segments)):
                if i == j or used[j]: continue
                
                # check if segment j touches current segment and is collinear
                j_p0 = tuple(segments[j]['points'][0])
                j_p1 = tuple(segments[j]['points'][1])
                
                touch_point = None
                other_point = None
                
                if distance(c_p0, j_p0) < tol_dist:
                    touch_point = c_p0; other_point = j_p1
                elif distance(c_p0, j_p1) < tol_dist:
                    touch_point = c_p0; other_point = j_p0
                elif distance(c_p1, j_p0) < tol_dist:
                    touch_point = c_p1; other_point = j_p1
                elif distance(c_p1, j_p1) < tol_dist:
                    touch_point = c_p1; other_point = j_p0
                
                if touch_point:
                    # check collinearity
                    p_base = c_p1 if touch_point == c_p0 else c_p0
                    if is_collinear(p_base, touch_point, other_point):
                        # merge
                        used[j] = True
                        if touch_point == c_p0:
                            c_p0 = other_point
                        else:
                            c_p1 = other_point
                        grown = True
        
        merged.append({
            'type': segments[i]['type'],
            'layer': segments[i]['layer'],
            'block_name': segments[i]['block_name'],
            'closed': False,
            'points': [list(c_p0), list(c_p1)]
        })
        used[i] = True
    return merged

merged_walls = merge_collinear_segments(walls)
print(f"Merged wall segments: {len(merged_walls)}")
