import json

def patch_semantic():
    with open('backend/semantic_engine.py', 'r') as f:
        content = f.read()
    
    content = content.replace('''            # Match columns (ONLY closed polylines with at least 3 vertices representing column boundaries)
            if etype == 'LWPOLYLINE' and ('kolon' in layer or 'column' in layer):
                pts = ent.get('vertices', [])
                if len(pts) >= 3:
                    pts_list = [[p['x'], p['y']] for p in pts if 'x' in p]
                    if pts_list:
                        bim_elements.append({
                            "category": "COLUMN",
                            "layer": ent.get('layer', 'Kolon'),
                            "points": pts_list,
                            "closed": True
                        })
                    
            # Match doors
            elif etype == 'LINE' and ('kap' in layer or 'door' in layer):
                bim_elements.append({
                    "category": "DOOR",
                    "layer": ent.get('layer', 'Kapı'),
                    "points": [[ent['start']['x'], ent['start']['y']], [ent['end']['x'], ent['end']['y']]],
                    "width": self._distance((ent['start']['x'], ent['start']['y']), (ent['end']['x'], ent['end']['y']))
                })
                
            # Match windows
            elif etype in ['LWPOLYLINE', 'LINE'] and ('pencere' in layer or 'window' in layer):
                pts = ent.get('vertices', []) if etype == 'LWPOLYLINE' else [ent['start'], ent['end']]
                pts_list = [[p['x'], p['y']] for p in pts if 'x' in p]
                if len(pts_list) >= 2:
                    bim_elements.append({
                        "category": "WINDOW",
                        "layer": ent.get('layer', 'Pencere'),
                        "points": pts_list
                    })

        # Append structured walls
        for wall in walls:
            bim_elements.append({
                "category": "WALL",
                "wall_id": wall.get('wall_id'),
                "type": wall.get('wall_type', 'Partition Wall'),
                "points": wall.get('points'),
                "thickness": wall.get('thickness'),
                "angle": wall.get('angle', 0.0)
            })''', '''            bname = ent.get('block_name', 'default')
            # Match columns (ONLY closed polylines with at least 3 vertices representing column boundaries)
            if etype == 'LWPOLYLINE' and ('kolon' in layer or 'column' in layer):
                pts = ent.get('vertices', [])
                if len(pts) >= 3:
                    pts_list = [[p['x'], p['y']] for p in pts if 'x' in p]
                    if pts_list:
                        bim_elements.append({
                            "category": "COLUMN",
                            "layer": ent.get('layer', 'Kolon'),
                            "block_name": bname,
                            "points": pts_list,
                            "closed": True
                        })
                    
            # Match doors
            elif etype == 'LINE' and ('kap' in layer or 'door' in layer):
                bim_elements.append({
                    "category": "DOOR",
                    "layer": ent.get('layer', 'Kapı'),
                    "block_name": bname,
                    "points": [[ent['start']['x'], ent['start']['y']], [ent['end']['x'], ent['end']['y']]],
                    "width": self._distance((ent['start']['x'], ent['start']['y']), (ent['end']['x'], ent['end']['y']))
                })
                
            # Match windows
            elif etype in ['LWPOLYLINE', 'LINE'] and ('pencere' in layer or 'window' in layer):
                pts = ent.get('vertices', []) if etype == 'LWPOLYLINE' else [ent['start'], ent['end']]
                pts_list = [[p['x'], p['y']] for p in pts if 'x' in p]
                if len(pts_list) >= 2:
                    bim_elements.append({
                        "category": "WINDOW",
                        "layer": ent.get('layer', 'Pencere'),
                        "block_name": bname,
                        "points": pts_list
                    })

        # Append structured walls
        for wall in walls:
            bim_elements.append({
                "category": "WALL",
                "wall_id": wall.get('wall_id'),
                "type": wall.get('wall_type', 'Partition Wall'),
                "block_name": wall.get('block_name', 'default'),
                "points": wall.get('points'),
                "thickness": wall.get('thickness'),
                "angle": wall.get('angle', 0.0)
            })''')
    with open('backend/semantic_engine.py', 'w') as f:
        f.write(content)

def patch_topology():
    with open('backend/topology_engine.py', 'r') as f:
        content = f.read()
    content = content.replace('''        # Build nodes from endpoints of walls
        for idx, wall in enumerate(walls):
            pts = wall.get('points', [])
            if len(pts) < 2:
                continue
            
            p0 = tuple(pts[0])
            p1 = tuple(pts[-1])''', '''        # Build nodes from endpoints of walls
        for idx, wall in enumerate(walls):
            pts = wall.get('points', [])
            bname = wall.get('block_name', 'default')
            if len(pts) < 2:
                continue
            
            # Combine block_name with coordinates so nodes in different blocks don't snap/merge together
            p0 = tuple(pts[0])
            p1 = tuple(pts[-1])
            # Actually, topology_engine just builds graphs. Since coordinates are exact snap-points now,
            # different blocks might share coordinates if they overlap. 
            # It's better to isolate graph building per block_name. But for now, we just pass block_name.''')
            
    content = content.replace('''            # Add edge
            wall_edges.append({
                "wall_id": idx,
                "node_a": node_map[p0],
                "node_b": node_map[p1],
                "points": [list(p0), list(p1)],
                "thickness": 150.0, # Default thickness
                "angle": angle_deg
            })''', '''            # Add edge
            wall_edges.append({
                "wall_id": idx,
                "node_a": node_map[p0],
                "node_b": node_map[p1],
                "block_name": bname,
                "points": [list(p0), list(p1)],
                "thickness": 150.0, # Default thickness
                "angle": angle_deg
            })''')
    with open('backend/topology_engine.py', 'w') as f:
        f.write(content)

patch_semantic()
patch_topology()
