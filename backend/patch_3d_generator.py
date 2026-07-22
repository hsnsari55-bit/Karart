import re

with open("backend/model_3d_generator.py", "r") as f:
    content = f.read()

column_patch = """
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
"""

content = re.sub(r'        if len\(pts\) >= 3:\n            try:\n                poly = Polygon\(pts\)\n                mesh = trimesh\.creation\.extrude_polygon\(poly, height=height\)\n                return mesh\n            except Exception as e:\n                logger\.error\(f"Error extruding column: \{e\}"\)', column_patch, content)

slab_patch = """
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
"""

content = re.sub(r'        if len\(poly_pts\) >= 3:\n            try:\n                p = Polygon\(poly_pts\)\n                mesh = trimesh\.creation\.extrude_polygon\(p, height=20\.0\)\n                if height_z != 0:\n                    mesh\.apply_translation\(\[0, 0, height_z\]\)\n                else:\n                    mesh\.apply_translation\(\[0, 0, -20\.0\]\)\n                return mesh\n            except Exception as e:\n                logger\.error\(f"Error extruding slab: \{e\}"\)', slab_patch, content)


with open("backend/model_3d_generator.py", "w") as f:
    f.write(content)
