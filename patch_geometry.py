import json

with open('backend/geometry_engine.py', 'r') as f:
    content = f.read()

merge_func = """
    def _merge_collinear_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged = []
        used = [False] * len(segments)
        
        for i in range(len(segments)):
            if used[i]: continue
            
            c_p0 = tuple(segments[i]['points'][0])
            c_p1 = tuple(segments[i]['points'][1])
            
            grown = True
            while grown:
                grown = False
                for j in range(len(segments)):
                    if i == j or used[j]: continue
                    
                    j_p0 = tuple(segments[j]['points'][0])
                    j_p1 = tuple(segments[j]['points'][1])
                    
                    touch_point = None
                    other_point = None
                    
                    if self._distance(c_p0, j_p0) < self.snap_tolerance:
                        touch_point = c_p0; other_point = j_p1
                    elif self._distance(c_p0, j_p1) < self.snap_tolerance:
                        touch_point = c_p0; other_point = j_p0
                    elif self._distance(c_p1, j_p0) < self.snap_tolerance:
                        touch_point = c_p1; other_point = j_p1
                    elif self._distance(c_p1, j_p1) < self.snap_tolerance:
                        touch_point = c_p1; other_point = j_p0
                    
                    if touch_point:
                        p_base = c_p1 if touch_point == c_p0 else c_p0
                        if self._is_collinear(p_base, touch_point, other_point):
                            used[j] = True
                            if touch_point == c_p0:
                                c_p0 = other_point
                            else:
                                c_p1 = other_point
                            grown = True
            
            merged.append({
                "type": segments[i]['type'],
                "layer": segments[i]['layer'],
                "block_name": segments[i]['block_name'],
                "closed": False,
                "points": [list(c_p0), list(c_p1)]
            })
            used[i] = True
        return merged
"""

# Insert _merge_collinear_segments before run()
content = content.replace('    def run(self) -> List[Dict[str, Any]]:', merge_func + '\n    def run(self) -> List[Dict[str, Any]]:')

# Update run() to use it
old_save = """        # Save to outputs/walls_clean.json"""
new_save = """        # Collinear Merge Pass
        cleaned_walls = self._merge_collinear_segments(cleaned_walls)
        self.logger.info(f"Collinear merge reduced segments to {len(cleaned_walls)}.")
        
        # Save to outputs/walls_clean.json"""

content = content.replace(old_save, new_save)

with open('backend/geometry_engine.py', 'w') as f:
    f.write(content)
