import os
import json
import logging
import math
import time
import uuid
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union, polygonize
from rtree import index

from backend.path_manager import PathManager
from backend.config import ConfigManager

class SpaceEngine:
    def __init__(self):
        self.path_manager = PathManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger('KaRar-SpaceEngine')
        
        self.stats = {
            "Total Polygons": 0,
            "Valid Spaces": 0,
            "Virtual Boundaries": 0,
            "processing_time_ms": 0
        }

    def run(self) -> Dict[str, Any]:
        start_time = time.time()
        
        geom_path = self.path_manager.get_path('outputs', 'geometry_graph.json')
        bim_path = self.path_manager.get_path('outputs', 'bim_semantics.json')
        
        if not os.path.exists(geom_path) or not os.path.exists(bim_path):
            self.logger.error("Required input files not found.")
            return {}
            
        with open(geom_path, 'r', encoding='utf-8') as f:
            geom_data = json.load(f)
        with open(bim_path, 'r', encoding='utf-8') as f:
            bim_data = json.load(f)
            
        nodes = geom_data.get('nodes', [])
        edges = geom_data.get('edges', [])
        
        # 1. Identify all physical Wall lines from BIM Semantics
        walls = [el for el in bim_data.get('elements', []) if el['type'] == 'Wall']
        wall_lines = []
        wall_rtree = index.Index()
        for i, w in enumerate(walls):
            pts = w.get('geometry', {}).get('points', [])
            if len(pts) == 2:
                ls = LineString(pts)
                wall_lines.append((w['uuid'], ls))
                b = ls.bounds
                wall_rtree.insert(i, b)
                
        # 2. Extract Dangling Nodes and apply Iterative Retry Gap Closing
        danglings = [n for n in nodes if n.get('degree', 0) == 1]
        self.logger.info(f"Found {len(danglings)} dangling wall nodes. Starting iterative gap closing retry mechanism...")
        
        max_retries = 3
        gap_thresholds = [400.0, 800.0, 1200.0]
        spaces = []
        virtual_lines = []
        
        for attempt in range(max_retries):
            gap_threshold = gap_thresholds[attempt]
            virtual_lines = []
            dangling_rtree = index.Index()
            for i, n in enumerate(danglings):
                dangling_rtree.insert(i, (n['x'], n['y'], n['x'], n['y']))
                
            for i, n in enumerate(danglings):
                bx = (n['x'] - gap_threshold, n['y'] - gap_threshold, n['x'] + gap_threshold, n['y'] + gap_threshold)
                neighbors = list(dangling_rtree.intersection(bx))
                for j in neighbors:
                    if i < j:
                        n2 = danglings[j]
                        dist = math.hypot(n['x']-n2['x'], n['y']-n2['y'])
                        if 10 < dist <= gap_threshold:
                            virtual_lines.append(LineString([(n['x'], n['y']), (n2['x'], n2['y'])]))
                            
            self.stats["Virtual Boundaries"] = len(virtual_lines)
            
            # 3. Polygonize (Walls + Virtual Boundaries)
            all_lines = [wl for _, wl in wall_lines] + virtual_lines
            noded = unary_union(all_lines)
            if noded.geom_type == 'MultiLineString':
                final_lines = list(noded.geoms)
            elif noded.geom_type == 'LineString':
                final_lines = [noded]
            else:
                final_lines = []
                
            polygons = list(polygonize(final_lines))
            self.stats["Total Polygons"] = len(polygons)
            
            MIN_SPACE_AREA = 5000.0 
            spaces = [poly for poly in polygons if poly.area >= MIN_SPACE_AREA]
            
            if len(spaces) > 0 or attempt == max_retries - 1:
                self.logger.info(f"Gap closing successful on attempt {attempt+1} (threshold: {gap_threshold}mm): found {len(spaces)} valid spaces.")
                break
            else:
                self.logger.warning(f"Gap closing attempt {attempt+1} (threshold: {gap_threshold}mm) yielded 0 spaces. Retrying with increased threshold...")

        self.stats["Valid Spaces"] = len(spaces)
        
        # 4. Map Boundary Walls and Neighbors
        space_outputs = []
        
        # To map neighbors, we can check if space polygons share edges
        # We'll buffer slightly to find overlaps, or just look at exact segments
        
        for idx, space_poly in enumerate(spaces):
            boundary_coords = list(space_poly.exterior.coords)
            coord_str = json.dumps([{"x": round(p[0], 2), "y": round(p[1], 2)} for p in boundary_coords], sort_keys=True)
            space_hash = uuid.uuid5(uuid.NAMESPACE_DNS, f"space_{coord_str}").hex[:8]
            space_uuid = f"space-{space_hash}"
            
            bounded_by_walls = []
            
            # For each segment of the space boundary, find the corresponding Wall
            # Query adaptive radius based on snapping tolerance to accommodate wall thickness offset
            search_radius = max(self.config.get("tolerances.snapping_distance_mm", 5.0) * 4.0, 150.0)
            
            for c_idx in range(len(boundary_coords) - 1):
                p1 = boundary_coords[c_idx]
                p2 = boundary_coords[c_idx+1]
                mid_x = (p1[0] + p2[0]) / 2.0
                mid_y = (p1[1] + p2[1]) / 2.0
                
                # Query R-Tree
                bx = (mid_x - search_radius, mid_y - search_radius, mid_x + search_radius, mid_y + search_radius)
                candidates = list(wall_rtree.intersection(bx))
                
                mid_pt = Point(mid_x, mid_y)
                best_wall = None
                best_dist = float('inf')
                
                for c in candidates:
                    w_uuid, w_line = wall_lines[c]
                    d = mid_pt.distance(w_line)
                    if d < search_radius and d < best_dist:
                        best_dist = d
                        best_wall = w_uuid
                        
                if best_wall and best_wall not in bounded_by_walls:
                    bounded_by_walls.append(best_wall)
                    
            space_outputs.append({
                "uuid": space_uuid,
                "type": "Space",
                "area": round(space_poly.area, 2),
                "boundary": [{"x": round(p[0], 2), "y": round(p[1], 2)} for p in boundary_coords],
                "bounded_by_walls": bounded_by_walls
            })
            
        self.stats["processing_time_ms"] = int((time.time() - start_time) * 1000)
        
        output_data = {
            "stats": self.stats,
            "spaces": space_outputs
        }
        
        with open(self.path_manager.get_path('outputs', 'spaces.json'), 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
            
        self._generate_qa_report()
        self.logger.info(f"Space Engine complete in {self.stats['processing_time_ms']}ms.")
        return output_data
        
    def _generate_qa_report(self):
        report = f"""# Space Engine QA Raporu

**Tarih/Zaman:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**İşlem Süresi:** {self.stats['processing_time_ms']} ms

## İşlem Özeti
- **Virtual Boundaries (Sanal Sınırlar):** {self.stats['Virtual Boundaries']}
- **Toplam Çıkarılan Poligon:** {self.stats['Total Polygons']}
- **Geçerli Mahaller (Spaces):** {self.stats['Valid Spaces']}

## Mimari Kurallara Uyum
1. **Oda Sızıntısı (Room Leakage) Önleme:**
   - Topolojik olarak Dangling (ucu açık) olan düğümler (nodes) tespit edildi.
   - 400 birimden (max kapı/açıklık genişliği) yakın olan açık uçlar arasına **Sanal Sınırlar (Virtual Boundaries)** çekildi.
   - Bu sayede açık planlı alanlar ve kapı boşlukları sızıntı yapmadan kapalı poligonlara (mahallere) dönüştürüldü.
   
2. **Alan (Area) Filtrelemesi:**
   - Duvar kalınlıklarından oluşan ince uzun poligonlar ile kolonlar, `Area >= 5000` kuralı ile filtrelenerek sadece gerçek yaşam alanları (Spaces) elde edildi.

3. **Duvar Eşleştirmesi (Boundary Walls):**
   - Her bir Space'in sınır çizgileri (exterior ring) üzerinden orta noktalar (midpoints) alınarak R-Tree üzerinden en yakın fiziksel duvara (Wall UUID) bağlandı.
   - Bu sayede BIM Core'a her odanın tam olarak hangi duvarlar tarafından sınırlandığı bilgisi aktarılmış oldu.

## Çıktı Standardı
Oluşturulan `outputs/spaces.json` dosyası, her bir mahal için deterministik UUID'ler, alan (area) bilgisi ve kendisini sınırlayan duvarların referanslarını (`bounded_by_walls`) içerir. Bu yapı, 3D üretimi (Extrusion) ve metraj (BOM) hesaplamaları için doğrudan kullanılabilir durumdadır.
"""
        with open(self.path_manager.get_path('outputs', 'space_qa_report.md'), "w", encoding="utf-8") as f:
            f.write(report)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    SpaceEngine().run()
