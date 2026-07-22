import os
import json
import logging
import uuid
import math
from typing import List, Dict, Any

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

        with open(bim_path, 'r', encoding='utf-8') as f:
            bim_elements = json.load(f).get("elements", [])
        with open(spaces_path, 'r', encoding='utf-8') as f:
            spaces = json.load(f).get("spaces", [])
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        edges = graph_data.get('edges', [])
        nodes = graph_data.get('nodes', [])

        # Assign UUIDs to all BIM elements and separate them
        walls = []
        windows = []
        columns = []
        doors = []

        # Map edge index in graph to WALL uuid
        edge_idx_to_wall_uuid = {}

        # Since semantic engine loops over edges to create walls first:
        # the first len(edges) elements in bim_clean might be walls. 
        # But let's just find them by points to be sure. Or better, just map them directly.
        # Let's map wall elements to edges by center point or just assume order if they match.
        
        # Actually, semantic engine created WALL elements EXACTLY from edges in order?
        wall_elements = [el for el in bim_elements if el.get('type') == 'Wall']
        if len(wall_elements) == len(edges):
            for i, wall in enumerate(wall_elements):
                wall['uuid'] = str(uuid.uuid4())
                edge_idx_to_wall_uuid[i] = wall['uuid']
        else:
            # Fallback mapping
            for i, edge in enumerate(edges):
                p0 = (nodes[edge['from']]['x'], nodes[edge['from']]['y'])
                p1 = (nodes[edge['to']]['x'], nodes[edge['to']]['y'])
                # find matching wall
                for wall in wall_elements:
                    if 'uuid' in wall: continue
                    wp0, wp1 = wall['points'][0], wall['points'][1]
                    if (self._distance(p0, wp0) < 1.0 and self._distance(p1, wp1) < 1.0) or \
                       (self._distance(p0, wp1) < 1.0 and self._distance(p1, wp0) < 1.0):
                        wall['uuid'] = str(uuid.uuid4())
                        edge_idx_to_wall_uuid[i] = wall['uuid']
                        break

        # Generate UUIDs for all elements
        bim_idx_to_uuid = {}
        for i, el in enumerate(bim_elements):
            if 'uuid' not in el:
                el['uuid'] = str(uuid.uuid4())
            bim_idx_to_uuid[i] = el['uuid']
            
            cat = el.get('type')
            if cat == 'Wall': walls.append(el)
            elif cat == 'Window': windows.append(el)
            elif cat == 'Column': columns.append(el)
            elif cat == 'Door': doors.append(el)

        # Map Spaces
        for sp in spaces:
            sp['uuid'] = str(uuid.uuid4())
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
                # the two spaces are neighbors
                s1_uuid, s2_uuid = s_list[0], s_list[1]
                s1 = next(s for s in spaces if s['uuid'] == s1_uuid)
                s2 = next(s for s in spaces if s['uuid'] == s2_uuid)
                if s2_uuid not in s1['neighbors']: s1['neighbors'].append(s2_uuid)
                if s1_uuid not in s2['neighbors']: s2['neighbors'].append(s1_uuid)

        # 3. Window/Door <-> Wall Relationships
        # A window/door belongs to a wall if its centroid is close to the wall segment
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
                # Also assign to spaces that this wall bounds
                w_spaces = wall_to_spaces[closest_wall]
                for sp_uuid in w_spaces:
                    sp = next(s for s in spaces if s['uuid'] == sp_uuid)
                    if el.get('type') == 'Window':
                        if el['uuid'] not in sp['related_windows']: sp['related_windows'].append(el['uuid'])
                    elif el.get('type') == 'Door':
                        if el['uuid'] not in sp['related_doors']: sp['related_doors'].append(el['uuid'])

        # 4. Column <-> Space (Based on element_indices from space engine)
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
                    el['parent_spaces'].append(sp['uuid'])

        # Assemble the Canonical BIM Model
        canonical_model = {
            "metadata": {
                "version": "1.0",
                "generated_by": "KaRar BIM Core"
            },
            "spaces": spaces,
            "walls": walls,
            "windows": windows,
            "columns": columns,
            "doors": doors
        }

        output_path = self.path_manager.get_path('outputs', 'bim_model.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(canonical_model, f, indent=4)
            
        self.logger.info(f"Canonical BIM Model generated with {len(spaces)} spaces, {len(walls)} walls, {len(windows)} windows.")
        return canonical_model

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    engine = BIMCoreEngine()
    engine.run()
