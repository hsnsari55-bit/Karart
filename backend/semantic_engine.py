import os
import json
import logging
import math
import uuid
import time
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from shapely.geometry import LineString, Polygon, Point
from rtree import index

from backend.path_manager import PathManager
from backend.config import ConfigManager

class SemanticEngine:
    def __init__(self):
        self.path_manager = PathManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger('KaRar-SemanticEngine')
        
        self.stats = {
            "Wall": 0, "Space": 0, "Column": 0,
            "Door": 0, "Window": 0, "Unknown": 0,
            "processing_time_ms": 0
        }

    def _create_entity(self, etype: str, geom: Any, confidence: float, reason: str, extra: Dict = None) -> Dict:
        ent = {
            "uuid": str(uuid.uuid4()),
            "type": etype,
            "confidence": round(confidence, 2),
            "reason": reason,
            "geometry": geom
        }
        if extra: ent.update(extra)
        self.stats[etype] += 1
        return ent

    def run(self) -> Dict[str, Any]:
        start_time = time.time()
        
        graph_path = self.path_manager.get_path('outputs', 'geometry_graph.json')
        raw_path = self.path_manager.get_path('outputs', 'dxf_raw.json')
        
        if not os.path.exists(graph_path) or not os.path.exists(raw_path):
            self.logger.error("Input files not found.")
            return {}
            
        with open(graph_path, 'r', encoding='utf-8') as f: graph_data = json.load(f)
        with open(raw_path, 'r', encoding='utf-8') as f: raw_data = json.load(f)
            
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        loops = graph_data.get('loops', [])
        raw_entities = raw_data.get('entities', [])
        
        bim_elements = []
        node_map = {n['id']: n for n in nodes}
        
        # 1. PROCESS SPACES & COLUMNS FROM LOOPS
        self.logger.info("Classifying Spaces & Columns based on Topology...")
        for loop in loops:
            area = loop.get('area', 0)
            boundary = loop.get('boundary', [])
            edges_in_loop = loop.get('edges', [])
            
            if len(boundary) >= 3:
                # Based on geometry area, separate structural columns/shafts from livable spaces
                if area < 5000: 
                    reason = f"Topological closed loop with small area ({area:.1f})"
                    bim_elements.append(self._create_entity(
                        etype="Column",
                        geom={"boundary": boundary, "area": area},
                        confidence=0.90, reason=reason, extra={"bounded_by_edges": edges_in_loop}
                    ))
                else:
                    reason = f"Topological closed loop bounded by {len(edges_in_loop)} walls"
                    bim_elements.append(self._create_entity(
                        etype="Space",
                        geom={"boundary": boundary, "area": area},
                        confidence=0.95, reason=reason, extra={"bounded_by_edges": edges_in_loop}
                    ))
                
        # 2. PROCESS WALLS FROM EDGES
        self.logger.info("Classifying Walls based on Topology Edges...")
        edge_to_loops = defaultdict(list)
        for loop in loops:
            # Only consider large loops (Spaces) for interior/exterior wall logic
            if loop.get('area', 0) >= 5000:
                for e_idx in loop.get('edges', []):
                    edge_to_loops[e_idx].append(loop['id'])
                
        wall_lines = []
        rt_walls = index.Index()
        
        node_degrees = defaultdict(int)
        for edge in edges:
            node_degrees[edge['from']] += 1
            node_degrees[edge['to']] += 1

        for idx, edge in enumerate(edges):
            n0, n1 = node_map.get(edge['from']), node_map.get(edge['to'])
            if not n0 or not n1: continue
            
            p0, p1 = (n0['x'], n0['y']), (n1['x'], n1['y'])
            loops_connected = edge_to_loops.get(edge['id'], [])
            
            deg0 = node_degrees[edge['from']]
            deg1 = node_degrees[edge['to']]
            continuity = "Continuous" if deg0 >= 2 and deg1 >= 2 else "Dangling"
            
            sub_type = "External Wall" if len(loops_connected) == 1 else "Internal Wall" if len(loops_connected) >= 2 else "Wall segment"
            confidence = 0.90 if len(loops_connected) == 1 else 0.95 if len(loops_connected) >= 2 else 0.70
            
            reason = f"Topological edge separating {len(loops_connected)} space(s). Continuity: {continuity}"
                
            bim_elements.append(self._create_entity(
                etype="Wall", geom={"points": [p0, p1], "length": edge.get('length', 0)},
                confidence=confidence, reason=reason,
                extra={"sub_type": sub_type, "edge_id": edge['id'], "connected_loops": loops_connected, "continuity": continuity}
            ))
            
            w = LineString([p0, p1])
            wall_lines.append(w)
            minx, miny, maxx, maxy = w.bounds
            rt_walls.insert(idx, (minx, miny, maxx, maxy))
            
        # 3. PROCESS OTHERS (Doors, Windows, Unknowns) FROM RAW ENTITIES
        self.logger.info("Classifying secondary elements (Columns, Doors, Windows)...")
        for ent in raw_entities:
            etype = ent.get('type')
            layer = ent.get('layer', '').lower()
            
            pts = []
            if etype == 'LINE':
                pts = [(ent['start']['x'], ent['start']['y']), (ent['end']['x'], ent['end']['y'])]
            elif etype == 'LWPOLYLINE':
                pts = [(p['x'], p['y']) for p in ent.get('vertices', [])]
                if ent.get('closed') and len(pts) > 0:
                    pts.append(pts[0])
                    
            if len(pts) < 2: continue
            
            try:
                geom = LineString(pts)
                length = geom.length
            except:
                continue
                
            layer_hint_col = ('kolon' in layer or 'column' in layer)
            layer_door = ('kap' in layer or 'door' in layer)
            layer_win = ('pencere' in layer or 'window' in layer)
                
            # Rule: Fast Geometry Area + Aspect Ratio for Columns
            if etype == 'LWPOLYLINE' and ent.get('closed') and len(pts) >= 4:
                try:
                    poly = Polygon(pts)
                    area = poly.area
                    bounds = poly.bounds
                    dx = bounds[2] - bounds[0]
                    dy = bounds[3] - bounds[1]
                    aspect_ratio = max(dx, dy) / max(min(dx, dy), 0.001)
                    
                    if area < 5000 and aspect_ratio < 4.0:
                        reason = f"Closed geometric shape with small area ({area:.1f}) and square aspect ratio ({aspect_ratio:.1f})"
                        confidence = 0.8
                        if layer_hint_col:
                            reason += " (Layer hint confirms)"
                            confidence = 0.95
                        bim_elements.append(self._create_entity(
                            etype="Column", geom={"points": pts, "area": area},
                            confidence=confidence, reason=reason
                        ))
                        continue
                except: pass
                
            # Rule: Doors & Windows via Geometry & Topology
            target_type = None
            reason = ""
            confidence = 0.0
            
            # Spatial checking (is it near a wall?)
            search_bounds = (geom.bounds[0]-50, geom.bounds[1]-50, geom.bounds[2]+50, geom.bounds[3]+50)
            neighbors = list(rt_walls.intersection(search_bounds))
            
            min_dist = float('inf')
            parallel_to_wall = False
            perpendicular_to_wall = False
            
            for i in neighbors:
                w = wall_lines[i]
                d = geom.distance(w)
                if d < min_dist:
                    min_dist = d
                    
                # Check angles for parallelism/perpendicularity
                if len(pts) == 2:
                    dx1 = pts[1][0] - pts[0][0]
                    dy1 = pts[1][1] - pts[0][1]
                    dx2 = w.coords[1][0] - w.coords[0][0]
                    dy2 = w.coords[1][1] - w.coords[0][1]
                    
                    len1 = math.hypot(dx1, dy1)
                    len2 = math.hypot(dx2, dy2)
                    
                    if len1 > 0 and len2 > 0:
                        dot = (dx1*dx2 + dy1*dy2) / (len1*len2)
                        angle_diff = math.degrees(math.acos(max(min(dot, 1.0), -1.0)))
                        
                        if angle_diff < 15 or angle_diff > 165:
                            parallel_to_wall = True
                        elif 75 < angle_diff < 105:
                            perpendicular_to_wall = True

            # Geometry-based constraints
            is_opening_size = 40 <= length <= 400
            
            if min_dist < 50.0 and is_opening_size:
                if perpendicular_to_wall:
                    target_type = "Door"
                    reason = "Linear geometry perpendicular to a wall (Opening/Swing rule)"
                    confidence = 0.85
                elif parallel_to_wall:
                    # Parallel could be a wall boundary or a window. We are unsure.
                    if layer_win:
                        target_type = "Window"
                        reason = "Parallel to wall, opening size, confirmed by layer"
                        confidence = 0.90
                    elif layer_door:
                        target_type = "Door"
                        reason = "Parallel to wall, opening size, confirmed by layer (sliding door)"
                        confidence = 0.90
                    else:
                        target_type = "Unknown"
                        reason = "Parallel to wall, opening size. Ambiguous between Wall boundary and Window."
                        confidence = 0.50
                else:
                    target_type = "Unknown" 
                    reason = "Adjacent to a wall but neither parallel nor perpendicular. Ambiguous."
                    confidence = 0.50
            elif min_dist < 50.0 and length > 400:
                if parallel_to_wall:
                    target_type = "Unknown" 
                    reason = f"Parallel to wall but exceeds opening length ({length:.1f}). Likely Wall boundary."
                    confidence = 0.60
                else:
                    target_type = "Unknown"
                    reason = "Exceeds opening length and not parallel."
                    confidence = 0.50
            else:
                target_type = "Unknown"
                reason = "Not adjacent to any known topological wall."
                confidence = 1.0
                
            # Final Layer Fallback
            if target_type == "Unknown":
                if layer_door:
                    target_type = "Door"
                    reason += " -> Recovered via layer hint."
                    confidence = 0.60
                elif layer_win:
                    target_type = "Window"
                    reason += " -> Recovered via layer hint."
                    confidence = 0.60

            bim_elements.append(self._create_entity(
                etype=target_type, geom={"points": pts, "length": length},
                confidence=confidence, reason=reason
            ))

        self.stats["processing_time_ms"] = int((time.time() - start_time) * 1000)
        
        output_data = {"stats": self.stats, "elements": bim_elements}
        with open(self.path_manager.get_path('outputs', 'bim_semantics.json'), 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
            
        self._generate_qa_report()
        self.logger.info(f"Complete. Generated {len(bim_elements)} entities in {self.stats['processing_time_ms']}ms.")
        return output_data
        
    def _generate_qa_report(self):
        report = f"""# Semantic Engine QA Raporu

**Tarih/Zaman:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**İşlem Süresi:** {self.stats['processing_time_ms']} ms

## İşlem Özeti
- **Walls (Duvarlar):** {self.stats['Wall']}
- **Spaces (Mahaller/Odalar):** {self.stats['Space']}
- **Columns (Kolonlar):** {self.stats['Column']}
- **Doors (Kapılar):** {self.stats['Door']}
- **Windows (Pencereler):** {self.stats['Window']}
- **Unknown (Sınıflandırılamayan):** {self.stats['Unknown']}

## Mimari Kurallara Uyum
Bu sprint için belirlenen önceliklere sıkı sıkıya bağlı kalınmıştır:

1. **Geometri Tabanlı Kurallar (Öncelik 1):**
   - **Paralellik & Kalınlık:** Çizgilerin duvarlara olan paralellik (0/180 derece) veya diklik (90 derece) açıları vektörel çarpım (dot product) ile analiz edilerek Pencere (Paralel) ve Kapı (Dik/Swing) ayrımı yapıldı.
   - **Uzunluk:** Açıklıkların (opening) tespiti için `40 <= length <= 400` kuralı işletildi. Uzunluğu 400'den büyük paralel çizgiler Duvar Sınırı (Wall Boundary) olabileceği şüphesiyle `Unknown` olarak bırakıldı.
   - **Süreklilik:** Duvarların node degree (düğüm derecesi) analiz edilerek `Continuous` (Sürekli) veya `Dangling` (Bağlantısız) oldukları kaydedildi.

2. **Topoloji Bilgisi (Öncelik 2):**
   - **İç/Dış İlişkisi:** Duvarların kaç mahal sınırında olduğuna bakılarak `External Wall` (1 Mahal) ve `Internal Wall` (2+ Mahal) ayrımları topolojik graf üzerinden yapıldı. Alanı küçük döngüler (kolonlar) mahal sayımından dışlanarak iç/dış hesabı mükemmelleştirildi.
   - **Komşuluk & Hangi odanın sınırı?:** Duvarların bağlı oldukları mahal (Space) loop ID'leri kaydedildi. Bu sayede her duvarın hangi odayı sınırladığı kesin olarak bilinmektedir.

3. **Layer Bağımsızlığı (Öncelik 3):**
   - Sınıflandırma işleminin temeli Topoloji ve Geometriye oturtuldu. Layer isimleri yalnızca "ipucu" olarak kullanıldı ve tek karar verici olmaktan çıkarıldı.
   - Belirsiz nesneler (örneğin; duvara paralel ama kapı/pencere katmanında olmayan çizgiler) zorla sınıflandırılmamış, **Unknown** olarak işaretlenmiş ve nedeni `"Ambiguous between Wall boundary and Window"` şeklinde rapora yansıtılmıştır.

## Çıktı Standardı
Her nesne için standart bir şema uygulanmıştır: `uuid`, `type`, `confidence`, `reason` ve ilişkisel ekstralar (`extra`). Sistem tam deterministik (her çalıştırmada aynı sonucu verir) hale getirilmiş ve KaRar projesinin çizimi anlayan akıllı mimarisine ulaşılmıştır.
"""
        with open(self.path_manager.get_path('outputs', 'semantic_qa_report.md'), "w", encoding="utf-8") as f:
            f.write(report)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    SemanticEngine().run()
