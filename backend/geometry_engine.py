import os
import json
import logging
import math
import time
import hashlib
from typing import List, Dict, Any, Tuple
from shapely.geometry import Polygon
from rtree import index

from backend.path_manager import PathManager
from backend.config import ConfigManager

class GeometryEngine:
    """
    Geometry Engine (Step 2 of the KaRar Pipeline) - Production Ready & Deterministic.
    Features: Spatial Indexing (R-Tree) with deterministic candidate sorting, Overlap Detection,
    Self-Intersection Repair with sliver filtering, Zero-length cleanup, SHA256 digest verification.
    """
    def __init__(self):
        self.path_manager = PathManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger('KaRar-GeometryEngine')
        
        # Configured tolerance preference
        self.configured_snap_tolerance = self.config.get("tolerances.snapping_distance_mm", 5.0)
        self.snap_tolerance = self.configured_snap_tolerance
        self.collinear_angle_deg = self.config.get("tolerances.collinear_angle_threshold_deg", 2.5)
        self.min_length = self.config.get("tolerances.min_segment_length_mm", 1.0)
        self.min_wall_area = self.config.get("tolerances.min_wall_area_mm2", 50.0)
        
        # Statistics for QA Report & Production Benchmarking
        self.stats = {
            "initial_entities": 0,
            "zero_length_removed": 0,
            "self_intersections_repaired": 0,
            "slivers_filtered": 0,
            "invalid_polygons_dropped": 0,
            "points_snapped_count": 0,
            "avg_snap_distance_mm": 0.0,
            "max_snap_distance_mm": 0.0,
            "overlapping_merged": 0,
            "total_segments_out": 0,
            "processing_time_ms": 0,
            "geometry_sha256": ""
        }
        self._total_snap_dist = 0.0

    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _is_collinear(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> bool:
        v1_x, v1_y = p2[0] - p1[0], p2[1] - p1[1]
        v2_x, v2_y = p3[0] - p2[0], p3[1] - p2[1]
        len1 = math.hypot(v1_x, v1_y)
        len2 = math.hypot(v2_x, v2_y)
        if len1 < 1e-5 or len2 < 1e-5: return True
        dot = (v1_x * v2_x + v1_y * v2_y) / (len1 * len2)
        dot = max(-1.0, min(1.0, dot))
        angle = math.degrees(math.acos(dot))
        return angle < self.collinear_angle_deg or (180.0 - angle) < self.collinear_angle_deg

    def _validate_and_clean_polygon(self, pts: List[Tuple[float, float]], ent_id: str) -> List[List[Tuple[float, float]]]:
        if len(pts) < 3: return []
        try:
            poly = Polygon(pts)
            if not poly.is_valid:
                self.logger.warning(f"Self-intersecting geometry detected in {ent_id}. Auto-repairing with buffer(0)...")
                self.stats["self_intersections_repaired"] += 1
                poly = poly.buffer(0)
            
            if poly.is_empty:
                self.stats["invalid_polygons_dropped"] += 1
                return []
                
            polys = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
            # Sort polygons by area descending so primary wall bodies take precedence over slivers
            polys.sort(key=lambda p: p.area, reverse=True)
            
            cleaned = []
            for p in polys:
                if p.is_valid and not p.is_empty:
                    if p.area < self.min_wall_area:
                        self.stats["slivers_filtered"] += 1
                        continue
                    c_pts = list(p.exterior.coords)
                    dedup = []
                    for pt in c_pts:
                        if not dedup or self._distance(dedup[-1], pt) > 1e-2:
                            dedup.append(pt)
                    if len(dedup) >= 3:
                        cleaned.append(dedup)
            return cleaned
        except Exception as e:
            self.logger.error(f"Error repairing polygon {ent_id}: {e}")
            self.stats["invalid_polygons_dropped"] += 1
            return []

    def _snap_points(self, points: List[Tuple[float, float]]) -> Dict[Tuple[float, float], Tuple[float, float]]:
        idx = index.Index()
        snapped_map = {}
        unique_points = []
        
        for p in points:
            bbox = (p[0] - self.snap_tolerance, p[1] - self.snap_tolerance, 
                    p[0] + self.snap_tolerance, p[1] + self.snap_tolerance)
            
            # Deterministic Candidate Selection: Collect all neighbors in tolerance box,
            # calculate distance, and sort by (distance, x, y, original_index) to prevent R-Tree order instability.
            candidates = []
            for j in idx.intersection(bbox):
                up = unique_points[j]
                d = self._distance(p, up)
                if d < self.snap_tolerance:
                    candidates.append((d, up[0], up[1], j, up))
                    
            if candidates:
                candidates.sort(key=lambda c: (c[0], c[1], c[2], c[3]))
                best_d, _, _, _, best_up = candidates[0]
                snapped_map[p] = best_up
                if best_d > 1e-5:
                    self.stats["points_snapped_count"] += 1
                    self._total_snap_dist += best_d
                    if best_d > self.stats["max_snap_distance_mm"]:
                        self.stats["max_snap_distance_mm"] = best_d
            else:
                new_idx = len(unique_points)
                unique_points.append(p)
                snapped_map[p] = p
                idx.insert(new_idx, (p[0], p[1], p[0], p[1]))
                
        if self.stats["points_snapped_count"] > 0:
            self.stats["avg_snap_distance_mm"] = round(self._total_snap_dist / self.stats["points_snapped_count"], 4)
        self.stats["max_snap_distance_mm"] = round(self.stats["max_snap_distance_mm"], 4)
        return snapped_map

    def _merge_overlapping_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not segments: return []
        
        idx = index.Index()
        for i, seg in enumerate(segments):
            p0, p1 = seg['points'][0], seg['points'][1]
            minx, miny = min(p0[0], p1[0]), min(p0[1], p1[1])
            maxx, maxy = max(p0[0], p1[0]), max(p0[1], p1[1])
            tol = self.snap_tolerance
            idx.insert(i, (minx - tol, miny - tol, maxx + tol, maxy + tol))
            
        merged = []
        used = [False] * len(segments)
        
        for i in range(len(segments)):
            if used[i]: continue
            
            c_p0 = tuple(segments[i]['points'][0])
            c_p1 = tuple(segments[i]['points'][1])
            layer = segments[i]['layer']
            bname = segments[i]['block_name']
            
            grown = True
            while grown:
                grown = False
                minx, miny = min(c_p0[0], c_p1[0]), min(c_p0[1], c_p1[1])
                maxx, maxy = max(c_p0[0], c_p1[0]), max(c_p0[1], c_p1[1])
                tol = self.snap_tolerance
                bbox = (minx - tol, miny - tol, maxx + tol, maxy + tol)
                
                # Sort spatial query neighbors deterministically by candidate segment coordinates
                raw_neighbors = list(idx.intersection(bbox))
                sorted_neighbors = []
                for j in raw_neighbors:
                    if i == j or used[j]: continue
                    j_p0, j_p1 = segments[j]['points'][0], segments[j]['points'][1]
                    s_pts = sorted([(j_p0[0], j_p0[1]), (j_p1[0], j_p1[1])])
                    sorted_neighbors.append((s_pts[0], s_pts[1], j))
                sorted_neighbors.sort(key=lambda item: (item[0], item[1], item[2]))
                
                for _, _, j in sorted_neighbors:
                    if segments[j]['layer'] != layer or segments[j]['block_name'] != bname:
                        continue
                        
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
                            self.stats["overlapping_merged"] += 1
                            if touch_point == c_p0:
                                c_p0 = other_point
                            else:
                                c_p1 = other_point
                            grown = True
                            break 
                            
            merged.append({
                "type": "LWPOLYLINE",
                "layer": layer,
                "block_name": bname,
                "closed": False,
                "points": [list(c_p0), list(c_p1)]
            })
            used[i] = True
            
        return merged

    def run(self) -> List[Dict[str, Any]]:
        start_time = time.time()
        raw_path = self.path_manager.get_path('outputs', 'dxf_raw.json')
        if not os.path.exists(raw_path):
            self.logger.error("dxf_raw.json not found.")
            return []
            
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        entities = raw_data.get('entities', [])
        
        # Compute adaptive fuzzy snapping tolerance based on drawing bounding box extent
        bbox = raw_data.get('bounding_box', {})
        dx = bbox.get('max_x', 0.0) - bbox.get('min_x', 0.0)
        dy = bbox.get('max_y', 0.0) - bbox.get('min_y', 0.0)
        extent = max(dx, dy)
        
        # Check if tolerance is explicitly overridden in config; if adaptive fallback, bound strictly [1.0mm, 15.0mm]
        if self.config.get("tolerances.snapping_distance_mm") is not None:
            self.snap_tolerance = float(self.config.get("tolerances.snapping_distance_mm"))
            self.logger.info(f"Using explicitly configured snap tolerance: {round(self.snap_tolerance, 2)}mm")
        elif extent > 0:
            adaptive_tol = max(1.0, min(15.0, extent * 0.0005))
            self.snap_tolerance = adaptive_tol
            self.logger.info(f"Adaptive fuzzy snapping tolerance computed: {round(self.snap_tolerance, 2)}mm (drawing extent: {round(extent, 2)})")

        wall_layers = [w.lower() for w in self.config.get_layer_mapping("walls")] + ['walls', 'duvar', 'duvarlar']
        
        wall_entities = []
        for i, ent in enumerate(entities):
            layer = ent.get('layer', '').lower()
            if any(wl in layer for wl in wall_layers):
                if not any(ex in layer for ex in ['kolon', 'column', 'pencere', 'window', 'aks', 'axis', 'kapı', 'door', 'kt']):
                    ent['_id'] = f"wall_{i}"
                    wall_entities.append(ent)

        # Canonical sort wall entities to guarantee entity order invariance regardless of DXF read sequence
        def _entity_sort_key(ent):
            etype = ent.get('type', '')
            layer = ent.get('layer', '')
            bname = ent.get('block_name', '')
            if etype == 'LINE':
                p0 = (round(ent.get('start', {}).get('x', 0), 2), round(ent.get('start', {}).get('y', 0), 2))
                p1 = (round(ent.get('end', {}).get('x', 0), 2), round(ent.get('end', {}).get('y', 0), 2))
                pts = sorted([p0, p1])
                return (layer, bname, etype, pts[0], pts[1])
            elif etype in ['LWPOLYLINE', 'POLYLINE']:
                pts = [(round(p.get('x', 0), 2), round(p.get('y', 0), 2)) for p in ent.get('points', [])]
                first_pt = pts[0] if pts else (0, 0)
                return (layer, bname, etype, first_pt)
            return (layer, bname, etype, (0, 0))

        wall_entities.sort(key=_entity_sort_key)
        
        self.stats["initial_entities"] = len(wall_entities)
        self.logger.info(f"Filtering wall layers found {len(wall_entities)} candidate entities.")
        
        entities_by_block: Dict[str, List[Dict[str, Any]]] = {}
        for ent in wall_entities:
            bname = ent.get('block_name', 'default')
            entities_by_block.setdefault(bname, []).append(ent)
            
        cleaned_walls = []
        
        for bname, block_ents in entities_by_block.items():
            all_points: List[Tuple[float, float]] = []
            
            for ent in block_ents:
                if ent['type'] == 'LINE':
                    all_points.extend([(ent['start']['x'], ent['start']['y']), (ent['end']['x'], ent['end']['y'])])
                elif ent['type'] in ['LWPOLYLINE', 'POLYLINE']:
                    pts = [(v['x'], v['y']) for v in ent.get('vertices', [])]
                    
                    if ent.get('closed', False) and len(pts) >= 3:
                        # Auto-repair invalid/self-intersecting closed polylines (polygons)
                        repaired = self._validate_and_clean_polygon(pts, ent.get('_id', 'unknown'))
                        for r_pts in repaired:
                            all_points.extend(r_pts)
                    else:
                        all_points.extend(pts)
                        
            # O(N log N) Snapping with R-Tree
            snapped_map = self._snap_points(all_points)
            self.logger.info(f"Block '{bname}' R-Tree Grid Locked: {len(all_points)} coords to {len(set(snapped_map.values()))} unique.")
            
            seen_segments = set()
            for ent in block_ents:
                pts = []
                if ent['type'] == 'LINE':
                    pts = [(ent['start']['x'], ent['start']['y']), (ent['end']['x'], ent['end']['y'])]
                elif ent['type'] in ['LWPOLYLINE', 'POLYLINE']:
                    pts = [(v['x'], v['y']) for v in ent.get('vertices', [])]
                    if ent.get('closed', False) and len(pts) >= 3:
                        repaired = self._validate_and_clean_polygon(pts, ent.get('_id', 'unknown'))
                        if repaired:
                            # Use first repaired polygon for segment extraction
                            pts = repaired[0]
                            
                snapped_pts = []
                for p in pts:
                    sp = snapped_map.get(p, p)
                    if not snapped_pts or self._distance(snapped_pts[-1], sp) > 1e-2:
                        snapped_pts.append(sp)
                        
                if len(snapped_pts) < 2:
                    self.stats["zero_length_removed"] += 1
                    continue
                    
                # Split into strictly deduplicated 2-point segments
                for idx in range(len(snapped_pts) - 1):
                    sp0 = snapped_pts[idx]
                    sp1 = snapped_pts[idx+1]
                    if self._distance(sp0, sp1) < self.min_length:
                        self.stats["zero_length_removed"] += 1
                        continue
                        
                    k0 = (round(sp0[0], 2), round(sp0[1], 2))
                    k1 = (round(sp1[0], 2), round(sp1[1], 2))
                    seg_key = tuple(sorted([k0, k1]))
                    
                    if seg_key not in seen_segments:
                        seen_segments.add(seg_key)
                        cleaned_walls.append({
                            "type": "LWPOLYLINE",
                            "layer": ent.get('layer', 'Duvar'),
                            "block_name": bname,
                            "closed": False,
                            "points": [list(sp0), list(sp1)]
                        })

        # O(N log N) Overlap/Collinear Merge with R-Tree
        merged_walls = self._merge_overlapping_segments(cleaned_walls)
        
        # Sort merged_walls deterministically
        def _wall_sort_key(w):
            pts = w.get("points", [])
            if len(pts) >= 2:
                p0 = (round(pts[0][0], 2), round(pts[0][1], 2))
                p1 = (round(pts[1][0], 2), round(pts[1][1], 2))
                p_sorted = sorted([p0, p1])
                return (w.get("layer", ""), p_sorted[0], p_sorted[1])
            return (w.get("layer", ""), (0, 0), (0, 0))

        merged_walls.sort(key=_wall_sort_key)
        self.stats["total_segments_out"] = len(merged_walls)
        
        self.logger.info(f"Collinear merge reduced segments from {len(cleaned_walls)} to {len(merged_walls)}.")
        
        self.stats["processing_time_ms"] = int((time.time() - start_time) * 1000)
        
        output_bytes = json.dumps(merged_walls, indent=4, sort_keys=True).encode('utf-8')
        self.stats["geometry_sha256"] = hashlib.sha256(output_bytes).hexdigest()
        
        # Save Geometry QA Report
        self._generate_qa_report()
        
        output_path = self.path_manager.get_path('outputs', 'walls_clean.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(output_bytes)
            
        self.logger.info(f"Cleaned wall structures exported successfully to {self.path_manager.get_relative_path(output_path)}")
        return merged_walls
        
    def _generate_qa_report(self):
        report = f"""# Geometry Engine QA ve İyileştirme Raporu

**Tarih/Zaman:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**İşlem Süresi:** {self.stats['processing_time_ms']} ms
**Geometri SHA-256 Özeti:** `{self.stats['geometry_sha256']}`

## İşlem Özeti (Benchmark)
- **Başlangıç Duvar Elemanı (Entities):** {self.stats['initial_entities']}
- **Sıfır Uzunluklu (Zero-Length) Çizgi Temizliği:** {self.stats['zero_length_removed']}
- **Kendiyle Kesişen (Self-Intersecting) Poligon Onarımı:** {self.stats['self_intersections_repaired']}
- **Küçük Parça (Sliver) Poligon Filtreleme:** {self.stats['slivers_filtered']}
- **Geçersiz (Invalid) Geometri Düşürme:** {self.stats['invalid_polygons_dropped']}
- **Nokta Yapışması (Point Snappings):** {self.stats['points_snapped_count']} (Ort: {self.stats['avg_snap_distance_mm']} mm, Max: {self.stats['max_snap_distance_mm']} mm)
- **Örtüşen/Kolinear (Overlapping) Çizgi Birleştirme:** {self.stats['overlapping_merged']}
- **Topolojiye Aktarılan Nihai Çizgi Sayısı:** {self.stats['total_segments_out']}

## Optimizasyon ve Determinizm Notları
- **R-Tree (Spatial Indexing):** Nokta yapışması (Snapping) ve doğru birleştirme (Collinear Merging) işlemlerindeki O(N²) zaman karmaşıklığı, bölgesel kutu (Bounding Box) sorgulamaları ve deterministik aday sıralaması (sorted candidate indices) sayesinde O(N log N) performansına ve %100 tekrarlanabilirliğe kavuşturulmuştur.
- **Tolerans Yönetimi:** Çizim boyut aralığına göre bağlı [1.0mm, 15.0mm] aralığında kontrol edilen ve konfigürasyondan override edilebilen tolerans mantığı uygulanmıştır.
- **Topolojik Kararlılık:** Geçersiz çokgenler `.buffer(0)` algoritmasıyla temizlenmiş, alan sıralaması ile ana duvarlar önceliklendirilmiş ve küçük kıymık poligonlar filtrelenmiştir.
- **Sonuç:** Çıktı tamamen standartlaştırılmış, SHA-256 doğrulama özeti ile kilitlenmiş ve Topology Engine için hazır hale getirilmiştir.
"""
        report_path = self.path_manager.get_path('outputs', 'geometry_qa_report.md')
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    engine = GeometryEngine()
    walls = engine.run()
    print(f"Geometry Engine complete! Generated {len(walls)} clean wall structures.")
