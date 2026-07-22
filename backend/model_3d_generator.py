import json
import math
import logging
import numpy as np
import trimesh
from shapely.geometry import Polygon
import uuid

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('KaRar-3D-Generator')

class Model3DGenerator:
    def __init__(self, bim_model_path: str, output_path: str):
        self.bim_model_path = bim_model_path
        self.output_path = output_path
        self.scene = trimesh.Scene()
        
        with open(self.bim_model_path, 'r', encoding='utf-8') as f:
            self.bim_data = json.load(f)
            
        self.walls_by_uuid = {w.get('uuid'): w for w in self.bim_data.get('walls', [])}
        
    def _create_wall_mesh(self, wall, windows, doors):
        p0 = np.array(wall["points"][0])
        p1 = np.array(wall["points"][1])
        thickness = wall.get("thickness", 20.0) / 10.0 # mm to cm usually, but let's assume it's correctly mapped or 20cm
        # In bim_model.json thickness is usually in mm, let's use / 10.0
        thickness = wall.get("thickness", 200.0) / 10.0
        height = 280.0
        
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        length = math.hypot(dx, dy)
        wall_dir = np.array([dx, dy]) / length if length > 0 else np.array([1, 0])
        
        # 2D Elevation Polygon: x is along wall, y is Z (height)
        wall_poly = Polygon([(0, 0), (length, 0), (length, height), (0, height)])
        
        holes = []
        
        def add_hole(elem, o_height, o_sill):
            wp0 = np.array(elem["points"][0])
            wp1 = np.array(elem["points"][1])
            
            t0 = np.dot(wp0 - p0, wall_dir)
            t1 = np.dot(wp1 - p0, wall_dir)
            
            min_t, max_t = min(t0, t1), max(t0, t1)
            
            # Slightly expand hole to avoid floating point issues during extrusion?
            # actually boolean on 2D is robust.
            min_t = max(0.0, min_t)
            max_t = min(length, max_t)
            
            if max_t > min_t + 0.1: # min 1mm hole
                hole = Polygon([
                    (min_t, o_sill),
                    (max_t, o_sill),
                    (max_t, o_sill + o_height),
                    (min_t, o_sill + o_height)
                ])
                holes.append(hole)

        for w in windows:
            add_hole(w, o_height=140.0, o_sill=90.0)
            
        for d in doors:
            add_hole(d, o_height=210.0, o_sill=0.0)
            
        result_poly = wall_poly
        for h in holes:
            result_poly = result_poly.difference(h)
            
        if result_poly.is_empty:
            return None
            
        polys = [result_poly] if result_poly.geom_type == 'Polygon' else list(result_poly.geoms)
        
        meshes = []
        for poly in polys:
            try:
                mesh = trimesh.creation.extrude_polygon(poly, height=thickness)
                meshes.append(mesh)
            except Exception as e:
                logger.error(f"Error extruding wall {wall.get('uuid')}: {e}")
            
        if not meshes:
            return None
            
        final_mesh = trimesh.util.concatenate(meshes)
        
        # Current: X=length, Y=height, Z=thickness
        # We need: X=length, Y=thickness, Z=height
        rot_x = trimesh.transformations.rotation_matrix(math.pi/2, [1,0,0])
        final_mesh.apply_transform(rot_x)
        
        # Center Y to 0
        final_mesh.apply_translation([0, thickness/2.0, 0])
        
        # Rotate Z to match wall direction
        angle = math.atan2(dy, dx)
        rot_z = trimesh.transformations.rotation_matrix(angle, [0,0,1])
        final_mesh.apply_transform(rot_z)
        
        # Translate to p0
        final_mesh.apply_translation([p0[0], p0[1], 0])
        
        return final_mesh

    def _create_column_mesh(self, col):
        pts = col["points"]
        height = 280.0

        if len(pts) >= 3:
            try:
                poly = Polygon(pts)
                if not poly.is_valid:
                    logger.warning(f"Self-intersecting geometry detected in column {col.get('uuid')}. Auto-repairing...")
                    poly = poly.buffer(0)
                
                polys = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
                meshes = []
                for p in polys:
                    if p.is_valid and not p.is_empty:
                        try:
                            meshes.append(trimesh.creation.extrude_polygon(p, height=height))
                        except Exception as e:
                            pass
                if meshes:
                    return trimesh.util.concatenate(meshes)
                else:
                    logger.error(f"Could not generate mesh for column {col.get('uuid')} after repair.")
                    return None
            except Exception as e:
                logger.error(f"Error extruding column: {e}")

        elif len(pts) == 1:
            box = trimesh.creation.box(extents=(30, 30, height))
            box.apply_translation([pts[0][0], pts[0][1], height/2])
            return box
        return None

    def _create_slab_mesh(self, space, height_z):
        poly_pts = space.get("polygon", [])

        if len(poly_pts) >= 3:
            try:
                p = Polygon(poly_pts)
                if not p.is_valid:
                    logger.warning(f"Self-intersecting geometry detected in space {space.get('uuid')}. Auto-repairing...")
                    p = p.buffer(0)
                
                polys = [p] if p.geom_type == 'Polygon' else list(p.geoms)
                meshes = []
                for poly_geom in polys:
                    if poly_geom.is_valid and not poly_geom.is_empty:
                        try:
                            meshes.append(trimesh.creation.extrude_polygon(poly_geom, height=20.0))
                        except Exception as e:
                            pass
                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
                    if height_z != 0:
                        mesh.apply_translation([0, 0, height_z])
                    else:
                        mesh.apply_translation([0, 0, -20.0])
                    return mesh
                else:
                    logger.error(f"Could not generate mesh for space slab {space.get('uuid')} after repair.")
                    return None
            except Exception as e:
                logger.error(f"Error extruding slab: {e}")

        return None
        
    def _create_window_mesh(self, win):
        wp0 = np.array(win["points"][0])
        wp1 = np.array(win["points"][1])
        dx = wp1[0] - wp0[0]
        dy = wp1[1] - wp0[1]
        length = math.hypot(dx, dy)
        thickness = 5.0
        height = 140.0
        sill = 90.0
        
        box = trimesh.creation.box(extents=(length, thickness, height))
        box.apply_translation([length/2, 0, height/2 + sill])
        
        angle = math.atan2(dy, dx)
        rot_z = trimesh.transformations.rotation_matrix(angle, [0,0,1])
        box.apply_transform(rot_z)
        
        box.apply_translation([wp0[0], wp0[1], 0])
        
        # Let's add a slight color to window glass
        box.visual.face_colors = [100, 200, 255, 150]
        return box
        
    def run(self):
        logger.info("Generating 3D model...")
        
        windows_by_wall = {}
        doors_by_wall = {}
        
        for w in self.bim_data.get("windows", []):
            pw = w.get("parent_wall")
            if pw: windows_by_wall.setdefault(pw, []).append(w)
                
        for d in self.bim_data.get("doors", []):
            pw = d.get("parent_wall")
            if pw: doors_by_wall.setdefault(pw, []).append(d)
                
        report = []
        
        for w in self.bim_data.get("walls", []):
            uuid_val = w.get("uuid")
            wins = windows_by_wall.get(uuid_val, [])
            doors = doors_by_wall.get(uuid_val, [])
            mesh = self._create_wall_mesh(w, wins, doors)
            if mesh:
                self.scene.add_geometry(mesh, node_name=uuid_val, geom_name=uuid_val)
                report.append({"type": "Wall", "uuid": uuid_val, "status": "Success"})
                
        for c in self.bim_data.get("columns", []):
            uuid_val = c.get("uuid")
            mesh = self._create_column_mesh(c)
            if mesh:
                self.scene.add_geometry(mesh, node_name=uuid_val, geom_name=uuid_val)
                report.append({"type": "Column", "uuid": uuid_val, "status": "Success"})
                
        for s in self.bim_data.get("spaces", []):
            uuid_val = s.get("uuid")
            floor = self._create_slab_mesh(s, 0.0)
            if floor:
                self.scene.add_geometry(floor, node_name=f"Floor_{uuid_val}", geom_name=f"Floor_{uuid_val}")
            ceil = self._create_slab_mesh(s, 280.0)
            if ceil:
                self.scene.add_geometry(ceil, node_name=f"Ceil_{uuid_val}", geom_name=f"Ceil_{uuid_val}")
                
            if floor or ceil:
                report.append({"type": "Space", "uuid": uuid_val, "status": "Success"})
                
        for w in self.bim_data.get("windows", []):
            uuid_val = w.get("uuid")
            mesh = self._create_window_mesh(w)
            if mesh:
                self.scene.add_geometry(mesh, node_name=uuid_val, geom_name=uuid_val)
                report.append({"type": "Window", "uuid": uuid_val, "status": "Success"})

        logger.info(f"Exporting to {self.output_path}")
        
        # We can export as OBJ or GLTF. Both are great. Let's do OBJ to see object groups clearly as well.
        # OBJ groups geometries.
        self.scene.export(self.output_path)
        obj_path = self.output_path.replace('.glb', '.obj')
        self.scene.export(obj_path)
        logger.info(f"Also exported OBJ to {obj_path}")
        
        return report

if __name__ == '__main__':
    gen = Model3DGenerator('outputs/bim_model.json', 'outputs/model.glb')
    report = gen.run()
    with open('outputs/3d_generation_report.json', 'w') as f:
        json.dump(report, f, indent=4)
