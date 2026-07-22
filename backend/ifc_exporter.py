import os
import json
import uuid
import math
import logging
import numpy as np
from typing import Dict, Any

try:
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.util
    import ifcopenshell.util.placement
except ImportError:
    logging.error("IfcOpenShell is not installed. Please install it with 'pip install ifcopenshell'")
    raise

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('KaRar-IFC-Exporter')

class IFCExporter:
    def __init__(self, bim_model_path: str, output_ifc_path: str):
        self.bim_model_path = bim_model_path
        self.output_ifc_path = output_ifc_path
        self.ifc_file = None
        self.storey = None
        self.model_context = None
        self.body_context = None

        self.stats = {
            "walls": 0,
            "windows": 0,
            "columns": 0,
            "spaces": 0,
            "doors": 0,
            "errors": 0
        }

    def run(self):
        logger.info(f"Loading Canonical BIM Model from {self.bim_model_path}")
        with open(self.bim_model_path, 'r', encoding='utf-8') as f:
            bim_data = json.load(f)

        logger.info("Initializing IfcOpenShell IFC4 model...")
        self.ifc_file = ifcopenshell.api.run("project.create_file", version="IFC4")
        
        project = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcProject", name="KaRar Project")
        ifcopenshell.api.run("project.assign_declaration", self.ifc_file, definitions=[project], relating_context=project)
        ifcopenshell.api.run("unit.assign_unit", self.ifc_file, length={"is_metric": True, "raw": "CENTIMETERS"})
        
        self.model_context = ifcopenshell.api.run("context.add_context", self.ifc_file, context_type="Model")
        self.body_context = ifcopenshell.api.run("context.add_context", self.ifc_file, 
            context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=self.model_context)

        site = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcSite", name="Default Site")
        ifcopenshell.api.run("aggregate.assign_object", self.ifc_file, relating_object=project, products=[site])
        
        building = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcBuilding", name="Default Building")
        ifcopenshell.api.run("aggregate.assign_object", self.ifc_file, relating_object=site, products=[building])
        
        self.storey = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcBuildingStorey", name="Ground Floor")
        ifcopenshell.api.run("aggregate.assign_object", self.ifc_file, relating_object=building, products=[self.storey])

        self._export_walls(bim_data.get("walls", []))
        self._export_columns(bim_data.get("columns", []))
        self._export_windows(bim_data.get("windows", []))
        self._export_doors(bim_data.get("doors", []))
        self._export_spaces(bim_data.get("spaces", []))

        self.ifc_file.write(self.output_ifc_path)
        logger.info(f"IFC Model successfully exported to {self.output_ifc_path}")
        return self.stats

    def _get_matrix(self, loc, angle=0.0):
        mat = np.eye(4)
        c = math.cos(angle)
        s = math.sin(angle)
        mat[0, 0] = c
        mat[0, 1] = -s
        mat[1, 0] = s
        mat[1, 1] = c
        mat[0, 3] = loc[0]
        mat[1, 3] = loc[1]
        mat[2, 3] = loc[2]
        return mat

    def _export_walls(self, walls):
        logger.info(f"Exporting {len(walls)} walls...")
        for w in walls:
            try:
                p0 = w["points"][0]
                p1 = w["points"][1]
                dx = p1[0] - p0[0]
                dy = p1[1] - p0[1]
                length = math.hypot(dx, dy)
                thickness = w["thickness"] / 10.0 # mm to cm
                height = 280.0
                
                wall_ent = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcWall", name=f"Wall_{w.get('wall_id', 'X')}")
                wall_ent.GlobalId = self._format_uuid(w.get("uuid"))
                ifcopenshell.api.run("spatial.assign_container", self.ifc_file, relating_structure=self.storey, products=[wall_ent])
                
                representation = ifcopenshell.api.run("geometry.add_wall_representation", self.ifc_file, 
                    context=self.body_context, length=length, height=height, thickness=thickness)
                ifcopenshell.api.run("geometry.assign_representation", self.ifc_file, product=wall_ent, representation=representation)
                
                angle = math.atan2(dy, dx)
                matrix = self._get_matrix((p0[0], p0[1], 0.0), angle)
                ifcopenshell.api.run("geometry.edit_object_placement", self.ifc_file, product=wall_ent, matrix=matrix)
                self.stats["walls"] += 1
            except Exception as e:
                logger.error(f"Failed to export wall {w.get('uuid')}: {e}")
                self.stats["errors"] += 1

    def _export_columns(self, columns):
        logger.info(f"Exporting {len(columns)} columns...")
        for col in columns:
            try:
                col_ent = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcColumn", name="Column")
                col_ent.GlobalId = self._format_uuid(col.get("uuid"))
                ifcopenshell.api.run("spatial.assign_container", self.ifc_file, relating_structure=self.storey, products=[col_ent])
                
                pts = col["points"]
                if len(pts) >= 4:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    width = max(xs) - min(xs)
                    depth = max(ys) - min(ys)
                    loc = (min(xs), min(ys), 0.0)
                else:
                    width = 30.0; depth = 30.0
                    loc = (pts[0][0], pts[0][1], 0.0) if pts else (0,0,0)
                
                profile = self.ifc_file.createIfcRectangleProfileDef("AREA", "ColumnProfile", None, width, depth)
                extrusion_dir = self.ifc_file.createIfcDirection((0.0, 0.0, 1.0))
                solid = self.ifc_file.createIfcExtrudedAreaSolid(profile, None, extrusion_dir, 280.0)
                shape_rep = self.ifc_file.createIfcShapeRepresentation(self.body_context, "Body", "SweptSolid", [solid])
                col_ent.Representation = self.ifc_file.createIfcProductDefinitionShape(None, None, [shape_rep])
                
                matrix = self._get_matrix(loc, 0.0)
                ifcopenshell.api.run("geometry.edit_object_placement", self.ifc_file, product=col_ent, matrix=matrix)
                self.stats["columns"] += 1
            except Exception as e:
                logger.error(f"Failed to export column {col.get('uuid')}: {e}")
                self.stats["errors"] += 1

    def _export_windows(self, windows):
        logger.info(f"Exporting {len(windows)} windows...")
        for w in windows:
            try:
                win_ent = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcWindow", name="Window")
                win_ent.GlobalId = self._format_uuid(w.get("uuid"))
                ifcopenshell.api.run("spatial.assign_container", self.ifc_file, relating_structure=self.storey, products=[win_ent])
                
                p0 = w["points"][0]
                p1 = w["points"][1]
                dx = p1[0] - p0[0]
                dy = p1[1] - p0[1]
                width = math.hypot(dx, dy)
                
                profile = self.ifc_file.createIfcRectangleProfileDef("AREA", "WindowProfile", None, width, 20.0)
                extrusion_dir = self.ifc_file.createIfcDirection((0.0, 0.0, 1.0))
                solid = self.ifc_file.createIfcExtrudedAreaSolid(profile, None, extrusion_dir, 140.0)
                shape_rep = self.ifc_file.createIfcShapeRepresentation(self.body_context, "Body", "SweptSolid", [solid])
                win_ent.Representation = self.ifc_file.createIfcProductDefinitionShape(None, None, [shape_rep])
                
                matrix = self._get_matrix((p0[0], p0[1], 90.0), math.atan2(dy, dx))
                ifcopenshell.api.run("geometry.edit_object_placement", self.ifc_file, product=win_ent, matrix=matrix)
                self.stats["windows"] += 1
            except Exception as e:
                logger.error(f"Failed to export window {w.get('uuid')}: {e}")
                self.stats["errors"] += 1

    def _export_doors(self, doors):
        logger.info(f"Exporting {len(doors)} doors...")
        for d in doors:
            try:
                door_ent = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcDoor", name="Door")
                door_ent.GlobalId = self._format_uuid(d.get("uuid"))
                ifcopenshell.api.run("spatial.assign_container", self.ifc_file, relating_structure=self.storey, products=[door_ent])
                self.stats["doors"] += 1
            except Exception as e:
                logger.error(f"Failed to export door {d.get('uuid')}: {e}")
                self.stats["errors"] += 1

    def _export_spaces(self, spaces):
        logger.info(f"Exporting {len(spaces)} spaces...")
        for s in spaces:
            try:
                space_ent = ifcopenshell.api.run("root.create_entity", self.ifc_file, ifc_class="IfcSpace", name=f"Space_{s.get('id', '')}")
                space_ent.GlobalId = self._format_uuid(s.get("uuid"))
                ifcopenshell.api.run("aggregate.assign_object", self.ifc_file, relating_object=self.storey, products=[space_ent])
                
                poly = s["polygon"]
                if len(poly) > 2:
                    pts = [self.ifc_file.createIfcCartesianPoint((float(p[0]), float(p[1]))) for p in poly]
                    polyline = self.ifc_file.createIfcPolyline(pts)
                    profile = self.ifc_file.createIfcArbitraryClosedProfileDef("AREA", "SpaceProfile", polyline)
                    extrusion_dir = self.ifc_file.createIfcDirection((0.0, 0.0, 1.0))
                    solid = self.ifc_file.createIfcExtrudedAreaSolid(profile, None, extrusion_dir, 280.0)
                    
                    shape_rep = self.ifc_file.createIfcShapeRepresentation(self.body_context, "Body", "SweptSolid", [solid])
                    space_ent.Representation = self.ifc_file.createIfcProductDefinitionShape(None, None, [shape_rep])
                
                    matrix = self._get_matrix((0.0, 0.0, 0.0))
                    ifcopenshell.api.run("geometry.edit_object_placement", self.ifc_file, product=space_ent, matrix=matrix)
                
                self.stats["spaces"] += 1
            except Exception as e:
                logger.error(f"Failed to export space {s.get('uuid')}: {e}")
                self.stats["errors"] += 1

    def _format_uuid(self, u):
        if not u: return ifcopenshell.guid.new()
        try: return ifcopenshell.guid.compress(u.replace('-', ''))
        except: return ifcopenshell.guid.new()

if __name__ == '__main__':
    exporter = IFCExporter('outputs/bim_model.json', 'outputs/model.ifc')
    stats = exporter.run()
    with open('outputs/ifc_export_stats.json', 'w') as f:
        json.dump(stats, f)
