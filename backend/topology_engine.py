import os
import json
import logging
import math
import time
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from backend.spatial_index import index
from shapely.geometry import LineString
from shapely.ops import unary_union, polygonize

from backend.path_manager import PathManager
from backend.config import ConfigManager

class TopologyEngine:
    """
    Topology Engine (Step 3 of the KaRar Pipeline) - Production Ready & Deterministic.
    Features: Fast O(N log N) T-Junction Resolution with interior segment parameter checks (0 < t < 1),
    X-Junction Resolution via unary_union, Node and Edge Graph Extraction with angle-based L/Straight classification,
    Face (Closed Loop) Detection, Adjacency mapping, SHA256 topology verification.
    """
    def __init__(self):
        self.path_manager = PathManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger('KaRar-TopologyEngine')
        
        # Pull snap tolerance from config, or default 5.0
        self.snap_tolerance = self.config.get("tolerances.snapping_distance_mm", 5.0)
        self.min_segment_length = float(self.config.get("tolerances.min_segment_length_mm", 1.0))

        self.stats = self._build_empty_stats()

    def _build_empty_stats(self) -> Dict[str, Any]:
        return {
            "initial_segments": 0,
            "filtered_short_segments": 0,
            "t_junctions_snapped": 0,
            "final_nodes": 0,
            "final_edges": 0,
            "straight_nodes_count": 0,
            "L_corner_nodes_count": 0,
            "T_nodes_count": 0,
            "X_nodes_count": 0,
            "closed_loops_found": 0,
            "processing_time_ms": 0,
            "topology_sha256": ""
        }

    def _reset_stats(self) -> None:
        self.stats = self._build_empty_stats()

    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _project_pt_to_line(self, p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[Tuple[float, float], float, float]:
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx*dx + dy*dy
        if l2 < 1e-10:
            return a, self._distance(p, a), 0.0
        t = ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / l2
        t_clamped = max(0.0, min(1.0, t))
        proj = (a[0] + t_clamped*dx, a[1] + t_clamped*dy)
        d = self._distance(p, proj)
        return proj, d, t

    def _calculate_angle(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 180.0
        if angle >= 180.0:
            angle -= 180.0
        return round(angle, 1)

    def _canonicalize_closed_boundary(self, boundary: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        coords = [
            (round(float(point["x"]), 3), round(float(point["y"]), 3))
            for point in boundary
        ]

        if len(coords) >= 2 and coords[0] == coords[-1]:
            coords = coords[:-1]

        if not coords:
            return []

        def _rotate_from_smallest(seq: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
            smallest_index = min(range(len(seq)), key=lambda idx: seq[idx])
            rotated = seq[smallest_index:] + seq[:smallest_index]
            return rotated + [rotated[0]]

        forward = _rotate_from_smallest(coords)
        reverse = _rotate_from_smallest(list(reversed(coords)))
        canonical = min(tuple(forward), tuple(reverse))
        return [{"x": x, "y": y} for x, y in canonical]

    def _canonicalize_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        loops: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        sorted_nodes = sorted(nodes, key=lambda n: (n["x"], n["y"], n["id"]))
        node_id_map = {node["id"]: idx for idx, node in enumerate(sorted_nodes)}

        canonical_nodes = []
        for idx, node in enumerate(sorted_nodes):
            canonical_nodes.append({
                "id": idx,
                "x": node["x"],
                "y": node["y"],
                "degree": node["degree"],
                "type": node["type"],
            })

        remapped_edges = []
        for edge in edges:
            from_id = node_id_map[edge["from"]]
            to_id = node_id_map[edge["to"]]
            if from_id > to_id:
                from_id, to_id = to_id, from_id

            remapped_edges.append({
                "old_id": edge["id"],
                "from": from_id,
                "to": to_id,
                "length": edge["length"],
                "angle": self._calculate_angle(
                    (canonical_nodes[from_id]["x"], canonical_nodes[from_id]["y"]),
                    (canonical_nodes[to_id]["x"], canonical_nodes[to_id]["y"]),
                ),
            })

        remapped_edges.sort(
            key=lambda e: (e["from"], e["to"], e["length"], e["angle"], e["old_id"])
        )
        edge_id_map = {edge["old_id"]: idx for idx, edge in enumerate(remapped_edges)}

        canonical_edges = []
        for idx, edge in enumerate(remapped_edges):
            canonical_edges.append({
                "id": idx,
                "from": edge["from"],
                "to": edge["to"],
                "length": edge["length"],
                "angle": edge["angle"],
            })

        remapped_loops = []
        for loop in loops:
            remapped_loop_edge_ids = sorted(
                edge_id_map[edge_id]
                for edge_id in loop.get("edges", [])
                if edge_id in edge_id_map
            )
            canonical_boundary = self._canonicalize_closed_boundary(loop.get("boundary", []))

            remapped_loops.append({
                "old_id": loop["id"],
                "area": loop["area"],
                "edges": remapped_loop_edge_ids,
                "boundary": canonical_boundary,
            })

        remapped_loops.sort(
            key=lambda loop: (
                loop["area"],
                tuple((point["x"], point["y"]) for point in loop["boundary"]),
                tuple(loop["edges"]),
                loop["old_id"],
            )
        )

        canonical_loops = []
        for idx, loop in enumerate(remapped_loops):
            canonical_loops.append({
                "id": idx,
                "area": loop["area"],
                "edges": loop["edges"],
                "boundary": loop["boundary"],
            })

        return {
            "nodes": canonical_nodes,
            "edges": canonical_edges,
            "loops": canonical_loops,
        }

    def _normalize_line_endpoints(
        self,
        line: LineString,
        protected_short_edges: Optional[set] = None,
    ) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        coords = list(line.coords)
        if len(coords) < 2:
            return None

        p0 = (round(coords[0][0], 3), round(coords[0][1], 3))
        p1 = (round(coords[-1][0], 3), round(coords[-1][1], 3))

        if p0 == p1:
            return None

        normalized = (p0, p1) if p0 <= p1 else (p1, p0)
        is_protected = normalized in (protected_short_edges or set())
        if (
            line.length < self.min_segment_length
            or self._distance(p0, p1) < self.min_segment_length
        ) and not is_protected:
            self.stats["filtered_short_segments"] += 1
            return None

        return normalized

    def _filter_planar_lines(
        self,
        lines: List[LineString],
        protected_short_edges: Optional[set] = None,
    ) -> List[LineString]:
        unique_lines: Dict[Tuple[Tuple[float, float], Tuple[float, float]], LineString] = {}

        for line in lines:
            normalized = self._normalize_line_endpoints(line, protected_short_edges)
            if normalized is None:
                continue

            if normalized not in unique_lines:
                unique_lines[normalized] = LineString([normalized[0], normalized[1]])

        return [unique_lines[key] for key in sorted(unique_lines.keys())]

    def _determine_node_type(self, node_id: int, deg: int, node_edges: List[Dict[str, Any]], node_coords: Tuple[float, float]) -> str:
        if deg <= 1:
            return "end"
        if deg == 2 and len(node_edges) == 2:
            # Distinguish straight continuation vs L-corner based on vector dot product
            e1, e2 = node_edges[0], node_edges[1]
            p1_other = (e1["to_x"], e1["to_y"]) if (e1["from_x"], e1["from_y"]) == node_coords else (e1["from_x"], e1["from_y"])
            p2_other = (e2["to_x"], e2["to_y"]) if (e2["from_x"], e2["from_y"]) == node_coords else (e2["from_x"], e2["from_y"])
            
            v1_x, v1_y = p1_other[0] - node_coords[0], p1_other[1] - node_coords[1]
            v2_x, v2_y = p2_other[0] - node_coords[0], p2_other[1] - node_coords[1]
            len1, len2 = math.hypot(v1_x, v1_y), math.hypot(v2_x, v2_y)
            if len1 > 1e-5 and len2 > 1e-5:
                dot = (v1_x * v2_x + v1_y * v2_y) / (len1 * len2)
                dot = max(-1.0, min(1.0, dot))
                angle_deg = math.degrees(math.acos(dot))
                # angle_deg near 180 means straight line continuation
                if angle_deg > 165.0:
                    self.stats["straight_nodes_count"] += 1
                    return "straight"
            self.stats["L_corner_nodes_count"] += 1
            return "L_corner"
        if deg == 3:
            self.stats["T_nodes_count"] += 1
            return "T"
        self.stats["X_nodes_count"] += 1
        return "X"

    def run(self) -> Dict[str, Any]:
        start_time = time.time()
        self._reset_stats()
        
        walls_path = self.path_manager.get_path('outputs', 'walls_clean.json')
        if not os.path.exists(walls_path):
            self.logger.error("walls_clean.json not found.")
            return {}
            
        with open(walls_path, 'r', encoding='utf-8') as f:
            walls_data = json.load(f)
            
        self.stats["initial_segments"] = len(walls_data)
        self.logger.info(f"Loaded {len(walls_data)} clean wall segments. Reconstructing topological network...")
        
        # 1. Prepare segments & Spatial Index for T-Junction snap
        segments = []
        rt = index.Index()
        for ent in walls_data:
            pts = ent.get('points', [])
            if len(pts) >= 2:
                p0 = (pts[0][0], pts[0][1])
                p1 = (pts[1][0], pts[1][1])

                if self._distance(p0, p1) < self.min_segment_length:
                    self.stats["filtered_short_segments"] += 1
                    continue

                segment_idx = len(segments)
                segments.append([p0, p1])
                
                minx, miny = min(p0[0], p1[0]), min(p0[1], p1[1])
                maxx, maxy = max(p0[0], p1[0]), max(p0[1], p1[1])
                rt.insert(segment_idx, (minx, miny, maxx, maxy))
                
        # 2. T-Junction Snap Pass
        snapped_segments = []
        accepted_snaps = []
        for i, s in enumerate(segments):
            new_s = []
            for endpoint_index, p in enumerate(s):
                # Query R-Tree for candidate lines
                bbox = (p[0]-self.snap_tolerance, p[1]-self.snap_tolerance, 
                        p[0]+self.snap_tolerance, p[1]+self.snap_tolerance)
                raw_neighbors = list(rt.intersection(bbox))
                
                # Deterministic candidate sorting
                candidates = []
                for j in raw_neighbors:
                    if i == j: continue
                    proj, d, t = self._project_pt_to_line(p, segments[j][0], segments[j][1])
                    # Strictly interior projection: 0.001 < t < 0.999 prevents projection onto segment endpoints
                    if 0.001 < t < 0.999 and 1e-4 < d < self.snap_tolerance:
                        candidates.append((d, proj[0], proj[1], j, proj))
                        
                if candidates:
                    candidates.sort(key=lambda c: (c[0], c[1], c[2], c[3]))
                    _, _, _, best_target_idx, best_proj = candidates[0]
                    new_s.append(best_proj)
                    accepted_snaps.append((i, endpoint_index, best_target_idx, best_proj))
                    self.stats["t_junctions_snapped"] += 1
                else:
                    new_s.append(p)
            snapped_segments.append(new_s)

        # Reproject accepted coordinates against the immutable final target geometry.
        # Applying these adjustments together avoids order-dependent cascading snaps.
        final_snap_coordinates = []
        for source_index, endpoint_index, target_index, original_projection in accepted_snaps:
            target_start, target_end = snapped_segments[target_index]
            final_projection, _, _ = self._project_pt_to_line(
                original_projection,
                target_start,
                target_end,
            )
            final_snap_coordinates.append(
                (source_index, endpoint_index, target_index, final_projection)
            )

        target_split_points = defaultdict(list)
        for source_index, endpoint_index, target_index, final_projection in final_snap_coordinates:
            snapped_segments[source_index][endpoint_index] = final_projection
            target_split_points[target_index].append(final_projection)

        # Explicitly split every target segment at accepted T-junction projections.
        # Moving only the approaching endpoint is insufficient for near-collinear
        # floating-point inputs because GEOS may not node the target at that point.
        noding_segments = []
        protected_short_edges = set()
        for i, (a, b) in enumerate(snapped_segments):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length_squared = dx*dx + dy*dy
            ordered_points = [(0.0, a), (1.0, b)]
            interior_split_points = set()

            if length_squared >= 1e-10:
                for split_point in target_split_points.get(i, []):
                    t = (
                        (split_point[0] - a[0]) * dx
                        + (split_point[1] - a[1]) * dy
                    ) / length_squared
                    if 0.0 < t < 1.0:
                        ordered_points.append((t, split_point))
                        interior_split_points.add(split_point)

            ordered_points.sort(key=lambda item: (item[0], item[1][0], item[1][1]))
            unique_points = []
            for _, point in ordered_points:
                if not unique_points or point != unique_points[-1]:
                    unique_points.append(point)

            segment_parts = [
                [unique_points[j], unique_points[j + 1]]
                for j in range(len(unique_points) - 1)
            ]
            noding_segments.extend(segment_parts)

            if interior_split_points:
                for part_start, part_end in segment_parts:
                    if (
                        part_start not in interior_split_points
                        and part_end not in interior_split_points
                    ):
                        continue
                    normalized = (
                        (round(part_start[0], 3), round(part_start[1], 3)),
                        (round(part_end[0], 3), round(part_end[1], 3)),
                    )
                    if normalized[0] != normalized[1]:
                        protected_short_edges.add(tuple(sorted(normalized)))
            
        # 3. Unary Union to create planar noded graph (X-junction resolution)
        self.logger.info("Executing unary_union for precise noding...")
        linestrings = [LineString(s) for s in noding_segments]
        if not linestrings:
            self.logger.warning("No valid segments found to node.")
            return {}
            
        noded = unary_union(linestrings)
        
        if noded.geom_type == 'MultiLineString':
            final_lines = list(noded.geoms)
        elif noded.geom_type == 'LineString':
            final_lines = [noded]
        else:
            final_lines = []

        final_lines = self._filter_planar_lines(final_lines, protected_short_edges)
            
        self.logger.info(f"Noding complete. Found {len(final_lines)} planar edges.")
        
        # 4. Extract Nodes and Edges
        node_coords = []
        node_map = {}
        node_degrees = defaultdict(int)
        node_edges_map = defaultdict(list)
        
        edges = []
        
        for idx, line in enumerate(final_lines):
            coords = list(line.coords)
            if len(coords) < 2: continue
            
            p0 = (round(coords[0][0], 3), round(coords[0][1], 3))
            p1 = (round(coords[-1][0], 3), round(coords[-1][1], 3))
            
            if p0 not in node_map:
                node_map[p0] = len(node_coords)
                node_coords.append(p0)
            if p1 not in node_map:
                node_map[p1] = len(node_coords)
                node_coords.append(p1)
                
            n0 = node_map[p0]
            n1 = node_map[p1]
            
            node_degrees[n0] += 1
            node_degrees[n1] += 1
            
            length = self._distance(p0, p1)
            angle = self._calculate_angle(p0, p1)
            
            edge_obj = {
                "id": idx,
                "from": n0,
                "to": n1,
                "from_x": p0[0],
                "from_y": p0[1],
                "to_x": p1[0],
                "to_y": p1[1],
                "length": round(length, 3),
                "angle": angle
            }
            edges.append(edge_obj)
            node_edges_map[n0].append(edge_obj)
            node_edges_map[n1].append(edge_obj)
            
        # Format Nodes with accurate degree & angular classification (L-corner vs Straight)
        nodes = []
        for i, coord in enumerate(node_coords):
            deg = node_degrees[i]
            n_edges = node_edges_map[i]
            node_type = self._determine_node_type(i, deg, n_edges, coord)
            nodes.append({
                "id": i,
                "x": coord[0],
                "y": coord[1],
                "degree": deg,
                "type": node_type
            })
            
        self.stats["final_nodes"] = len(nodes)
        self.stats["final_edges"] = len(edges)
        
        # Edge lookup for fast polygon mapping
        edge_lookup = {}
        for edge in edges:
            n0, n1 = edge["from"], edge["to"]
            edge_lookup[(n0, n1)] = edge["id"]
            edge_lookup[(n1, n0)] = edge["id"]
            
        # 5. Extract Closed Loops (Faces)
        self.logger.info("Extracting closed loops (faces)...")
        polygons = list(polygonize(final_lines))
        
        loops = []
        for i, poly in enumerate(polygons):
            boundary_coords = list(poly.exterior.coords)
            poly_edges = set()
            
            # Map boundary coordinates to node IDs, then to Edge IDs
            for c_idx in range(len(boundary_coords) - 1):
                p0 = (round(boundary_coords[c_idx][0], 3), round(boundary_coords[c_idx][1], 3))
                p1 = (round(boundary_coords[c_idx+1][0], 3), round(boundary_coords[c_idx+1][1], 3))
                
                n0 = node_map.get(p0)
                n1 = node_map.get(p1)
                
                if n0 is not None and n1 is not None:
                    edge_id = edge_lookup.get((n0, n1))
                    if edge_id is not None:
                        poly_edges.add(edge_id)
                        
            loops.append({
                "id": i,
                "area": round(poly.area, 2),
                "edges": sorted(list(poly_edges)),
                "boundary": [{"x": round(p[0], 3), "y": round(p[1], 3)} for p in boundary_coords]
            })
            
        self.stats["closed_loops_found"] = len(loops)
        self.stats["processing_time_ms"] = int((time.time() - start_time) * 1000)
        
        graph_payload = self._canonicalize_graph(nodes, edges, loops)
        
        output_bytes = json.dumps(graph_payload, indent=4, sort_keys=True).encode('utf-8')
        self.stats["topology_sha256"] = hashlib.sha256(output_bytes).hexdigest()
        
        # Save output
        output_path = self.path_manager.get_path('outputs', 'geometry_graph.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(output_bytes)
            
        self._generate_qa_report()
            
        self.logger.info(f"Topological network built successfully in {self.path_manager.get_relative_path(output_path)}")
        return graph_payload
        
    def _generate_qa_report(self):
        report = f"""# Topology Engine QA ve İyileştirme Raporu

**Tarih/Zaman:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**İşlem Süresi:** {self.stats['processing_time_ms']} ms
**Topoloji SHA-256 Özeti:** `{self.stats['topology_sha256']}`

## İşlem Özeti (Benchmark)
- **Başlangıç Duvar Çizgileri:** {self.stats['initial_segments']}
- **Elenen Kısa/Degenerate Segmentler:** {self.stats['filtered_short_segments']} (min length < {self.min_segment_length}mm)
- **Snapping ile Kapatılan T-Junctions (Strict 0 < t < 1 Interior Projection):** {self.stats['t_junctions_snapped']}
- **Çıkarılan Unik Düğümler (Nodes):** {self.stats['final_nodes']}
  - Straight Continuations: {self.stats['straight_nodes_count']}
  - L-Corners: {self.stats['L_corner_nodes_count']}
  - T-Junction Nodes: {self.stats['T_nodes_count']}
  - X-Junction Nodes: {self.stats['X_nodes_count']}
- **Ayrıştırılan Kesişimsiz Kenarlar (Edges):** {self.stats['final_edges']}
- **Oluşturulan Kapalı Alanlar (Loops/Faces):** {self.stats['closed_loops_found']}

## Mimari Başarımlar ve Determinizm
- **R-Tree T-Junction Yakalama:** Iz düşüm parametresi `0 < t < 1` kontrolüyle uç noktalara hatalı yapışmalar önlenmiş, deterministik aday sıralaması ile T-kesişimler O(N log N) performansında çözülmüştür.
- **Kısa Segment Gürültü Filtresi:** `min_segment_length_mm` altında kalan kaynak ve unary-union sonrası mikro segmentler elenerek near-degenerate drafting noise'ın graf topolojisini kirletmesi önlenmiştir.
- **Kesişim (X-Junction) Çözümü:** Shapely `unary_union` ile planarizing ve kesişim tespiti yapılmış, merkez hattı ağının tam planarizasyonu sağlanmıştır.
- **Düğüm Tip Sınıflandırması:** Degree=2 düğümler incident vektörlerin açısal skaler çarpımı ile `straight` (düz devam) ve `L_corner` (L köşe) olarak hassasiyetle ayrıştırılmıştır.
- **Closed Loop (Faces) Üretimi:** Graf teorisi üzerinden `polygonize` edilerek dış çerçevesi kapanan alanlar tespit edilmiş ve SHA-256 imzası ile kilitlenmiştir.

Bu yapı, Semantic Engine (Step 4) aşamasının gerektirdiği mekansal sınır ve bağlantı grafını eksiksiz şekilde sağlar.
"""
        report_path = self.path_manager.get_path('outputs', 'topology_qa_report.md')
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    engine = TopologyEngine()
    graph = engine.run()
    if graph:
        print(f"Topology Engine complete! Extracted {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, and {len(graph['loops'])} loops.")
