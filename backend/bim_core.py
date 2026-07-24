import os
import json
import logging
import uuid
import math
import time
import sys
import hashlib
import shapely

from backend.path_manager import PathManager

class BIMCoreEngine:
    def __init__(self):
        self.path_manager = PathManager()
        self.logger = logging.getLogger('KaRar')

    def _distance(self, p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    def _dist_point_to_segment(self, p, v, w):
        l2 = self._distance(v, w)**2
        if l2 == 0: return self._distance(p, v)
        t = max(0, min(1, ((p[0] - v[0]) * (w[0] - v[0]) + (p[1] - v[1]) * (w[1] - v[1])) / l2))
        proj = (v[0] + t * (w[0] - v[0]), v[1] + t * (w[1] - v[1]))
        return self._distance(p, proj)

    def run(self):
        bim_path = self.path_manager.get_path('outputs', 'bim_semantics.json')
        spaces_path = self.path_manager.get_path('outputs', 'spaces.json')
        graph_path = self.path_manager.get_path('outputs', 'geometry_graph.json')

        if not os.path.exists(bim_path) or not os.path.exists(spaces_path) or not os.path.exists(graph_path):
            self.logger.warning("Missing input files for BIM Core.")
            return

        with open(bim_path, 'rb') as f:
            sem_bytes = f.read()
            sem_sha256 = hashlib.sha256(sem_bytes).hexdigest()
            bim_elements = json.loads(sem_bytes.decode('utf-8')).get("elements", [])
            
        with open(spaces_path, 'rb') as f:
            spaces_bytes = f.read()
            spaces_sha256 = hashlib.sha256(spaces_bytes).hexdigest()
            spaces = json.loads(spaces_bytes.decode('utf-8')).get("spaces", [])
            
        with open(graph_path, 'rb') as f:
            graph_bytes = f.read()
            graph_sha256 = hashlib.sha256(graph_bytes).hexdigest()
            graph_data = json.loads(graph_bytes.decode('utf-8'))

        edges = graph_data.get('edges', [])
        nodes = graph_data.get('nodes', [])

        # Assign UUIDs to all BIM elements and separate them
        walls = []
        windows = []
        columns = []
        doors = []

        # Map edge index in graph to WALL uuid
        edge_idx_to_wall_uuid = {}

        wall_elements = [el for el in bim_elements if el.get('type') == 'Wall']
        if len(wall_elements) == len(edges):
            for i, wall in enumerate(wall_elements):
                if 'uuid' not in wall:
                    seed = f"wall_{wall.get('points')}"
                    wall['uuid'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))
                edge_idx_to_wall_uuid[i] = wall['uuid']
        else:
            for i, edge in enumerate(edges):
                p0 = (nodes[edge['from']]['x'], nodes[edge['from']]['y'])
                p1 = (nodes[edge['to']]['x'], nodes[edge['to']]['y'])
                for wall in wall_elements:
                    if 'uuid' in wall: 
                        edge_idx_to_wall_uuid[i] = wall['uuid']
                        continue
                    wp0, wp1 = wall['points'][0], wall['points'][1]
                    if (self._distance(p0, wp0) < 1.0 and self._distance(p1, wp1) < 1.0) or \
                       (self._distance(p0, wp1) < 1.0 and self._distance(p1, wp0) < 1.0):
                        seed = f"wall_{wp0}_{wp1}"
                        wall['uuid'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))
                        edge_idx_to_wall_uuid[i] = wall['uuid']
                        break

        # Generate UUIDs for all elements
        bim_idx_to_uuid = {}
        for i, el in enumerate(bim_elements):
            if 'uuid' not in el:
                seed = f"{el.get('type')}_{el.get('points') or el.get('boundary') or i}"
                el['uuid'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))
            bim_idx_to_uuid[i] = el['uuid']
            
            cat = el.get('type')
            if cat == 'Wall': walls.append(el)
            elif cat == 'Window': windows.append(el)
            elif cat == 'Column': columns.append(el)
            elif cat == 'Door': doors.append(el)

        # Map Spaces (preserve existing space uuid or compute deterministic uuid)
        for sp in spaces:
            if 'uuid' not in sp:
                seed = f"space_{sp.get('boundary')}"
                sp['uuid'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))
            sp['related_walls'] = []
            sp['related_windows'] = []
            sp['related_columns'] = []
            sp['related_doors'] = []
            sp['neighbors'] = []

        # 1. Space <-> Wall Relationships
        wall_to_spaces = {w['uuid']: [] for w in walls}
        
        for sp in spaces:
            for e_idx in sp.get('edge_indices', []):
                wall_uuid = edge_idx_to_wall_uuid.get(e_idx)
                if wall_uuid:
                    if wall_uuid not in sp['related_walls']:
                        sp['related_walls'].append(wall_uuid)
                    if sp['uuid'] not in wall_to_spaces[wall_uuid]:
                        wall_to_spaces[wall_uuid].append(sp['uuid'])

        for w in walls:
            w['related_spaces'] = wall_to_spaces[w['uuid']]

        # 2. Space <-> Neighbor Space
        for w in walls:
            s_list = w['related_spaces']
            if len(s_list) == 2:
                s1_uuid, s2_uuid = s_list[0], s_list[1]
                s1 = next((s for s in spaces if s['uuid'] == s1_uuid), None)
                s2 = next((s for s in spaces if s['uuid'] == s2_uuid), None)
                if s1 and s2:
                    if s2_uuid not in s1['neighbors']: s1['neighbors'].append(s2_uuid)
                    if s1_uuid not in s2['neighbors']: s2['neighbors'].append(s1_uuid)

        # 3. Window/Door <-> Wall Relationships
        for el in windows + doors:
            pts = el.get('points', [])
            if not pts: continue
            c_x = (pts[0][0] + pts[1][0]) / 2.0
            c_y = (pts[0][1] + pts[1][1]) / 2.0
            pt = (c_x, c_y)
            
            closest_wall = None
            min_dist = 9999.0
            for w in walls:
                wp0, wp1 = w['points'][0], w['points'][1]
                d = self._dist_point_to_segment(pt, wp0, wp1)
                if d < min_dist:
                    min_dist = d
                    closest_wall = w['uuid']
            
            if min_dist < 10.0 and closest_wall:
                el['parent_wall'] = closest_wall
                w_spaces = wall_to_spaces[closest_wall]
                for sp_uuid in w_spaces:
                    sp = next((s for s in spaces if s['uuid'] == sp_uuid), None)
                    if sp:
                        if el.get('type') == 'Window':
                            if el['uuid'] not in sp['related_windows']: sp['related_windows'].append(el['uuid'])
                        elif el.get('type') == 'Door':
                            if el['uuid'] not in sp['related_doors']: sp['related_doors'].append(el['uuid'])

        # 4. Column <-> Space
        for sp in spaces:
            for b_idx in sp.get('element_indices', []):
                el_uuid = bim_idx_to_uuid.get(b_idx)
                if not el_uuid: continue
                el = next((e for e in bim_elements if e['uuid'] == el_uuid), None)
                if el and el.get('type') == 'Column':
                    if el_uuid not in sp['related_columns']:
                        sp['related_columns'].append(el_uuid)
                    if 'parent_spaces' not in el:
                        el['parent_spaces'] = []
                    if sp['uuid'] not in el['parent_spaces']:
                        el['parent_spaces'].append(sp['uuid'])

        # Deterministic sorting helper for BIM elements
        def _elem_sort_key(el):
            pts = el.get('points') or el.get('boundary') or []
            c_x, c_y = 0.0, 0.0
            if pts:
                if isinstance(pts[0], list):
                    c_x = round(sum(p[0] for p in pts if isinstance(p, list)) / max(1, len(pts)), 2)
                    c_y = round(sum(p[1] for p in pts if isinstance(p, list)) / max(1, len(pts)), 2)
                elif isinstance(pts[0], dict):
                    c_x = round(sum(p.get('x', 0) for p in pts if isinstance(p, dict)) / max(1, len(pts)), 2)
                    c_y = round(sum(p.get('y', 0) for p in pts if isinstance(p, dict)) / max(1, len(pts)), 2)
            return (el.get('type', ''), c_x, c_y, el.get('uuid', ''))

        walls.sort(key=_elem_sort_key)
        windows.sort(key=_elem_sort_key)
        doors.sort(key=_elem_sort_key)
        columns.sort(key=_elem_sort_key)
        spaces.sort(key=_elem_sort_key)

        for sp in spaces:
            sp['related_walls'].sort()
            sp['related_windows'].sort()
            sp['related_columns'].sort()
            sp['related_doors'].sort()
            sp['neighbors'].sort()

        for w in walls:
            if 'related_spaces' in w:
                w['related_spaces'].sort()

        for col in columns:
            if 'parent_spaces' in col:
                col['parent_spaces'].sort()

        # Assemble Provenance Envelope Metadata
        provenance = {
            "engine": "KaRar BIM Core",
            "engine_version": "v1.0.0-RC1",
            "schema_version": "1.0",
            "python_version": sys.version.split()[0],
            "shapely_version": getattr(shapely, '__version__', 'unknown'),
            "generated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "input_hashes": {
                "bim_semantics_sha256": sem_sha256,
                "spaces_sha256": spaces_sha256,
                "geometry_graph_sha256": graph_sha256
            }
        }

        canonical_model = {
            "metadata": {
                "version": "1.0",
                "generated_by": "KaRar BIM Core Engine"
            },
            "provenance": provenance,
            "spaces": spaces,
            "walls": walls,
            "windows": windows,
            "columns": columns,
            "doors": doors
        }

        output_bytes = json.dumps(canonical_model, indent=4, sort_keys=True).encode('utf-8')
        canonical_sha256 = hashlib.sha256(output_bytes).hexdigest()
        canonical_model["provenance"]["canonical_bim_sha256"] = canonical_sha256

        output_path = self.path_manager.get_path('outputs', 'bim_model.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(json.dumps(canonical_model, indent=4, sort_keys=True).encode('utf-8'))
            
        self.logger.info(f"Canonical BIM Model generated with {len(spaces)} spaces, {len(walls)} walls, {len(windows)} windows. SHA-256: {canonical_sha256[:12]}")
        return canonical_model

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    engine = BIMCoreEngine()
    engine.run()
