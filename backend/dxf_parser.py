import os
import json
import logging
from typing import List, Dict, Any

from backend.path_manager import PathManager
from backend.config import ConfigManager

try:
    import ezdxf
    from ezdxf.path import make_path
except ImportError:
    ezdxf = None

class DXFParser:
    """
    Production-Ready DXF Parser using ezdxf.
    Supports LINE, LWPOLYLINE, POLYLINE, ARC, CIRCLE, ELLIPSE, SPLINE, INSERT, BLOCK.
    Flattens block references (INSERT) into world coordinates.
    Discretizes non-linear entities into LWPOLYLINE vertices.
    """
    
    def __init__(self):
        self.path_manager = PathManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger('KaRar-DXFParser')
        self.entities: List[Dict[str, Any]] = []
        self.min_x = float('inf')
        self.min_y = float('inf')
        self.max_x = float('-inf')
        self.max_y = float('-inf')
        self.sagitta = self.config.get("dxf.sagitta", 0.05) # discretization precision
        self.skipped_entities = 0

    def _update_bounds(self, x: float, y: float):
        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)

    def _process_entity(self, entity, block_name="default", scale_factor=1.0):
        """Recursively process entities, including nested block references (INSERT)"""
        dxftype = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0"

        if dxftype == 'INSERT':
            # ezdxf allows iterating through virtual entities with transformations applied
            try:
                for v_entity in entity.virtual_entities():
                    self._process_entity(v_entity, block_name=entity.dxf.name, scale_factor=scale_factor)
            except Exception as e:
                self.logger.warning(f"Error expanding block reference {entity.dxf.name}: {e}")
                self.skipped_entities += 1

        elif dxftype == 'LINE':
            try:
                sx, sy, sz = entity.dxf.start.x * scale_factor, entity.dxf.start.y * scale_factor, entity.dxf.start.z * scale_factor
                ex, ey, ez = entity.dxf.end.x * scale_factor, entity.dxf.end.y * scale_factor, entity.dxf.end.z * scale_factor
                
                self._update_bounds(sx, sy)
                self._update_bounds(ex, ey)
                
                self.entities.append({
                    "type": "LINE",
                    "layer": layer,
                    "block_name": block_name,
                    "start": {"x": sx, "y": sy, "z": sz},
                    "end": {"x": ex, "y": ey, "z": ez}
                })
            except Exception as e:
                self.logger.warning(f"Error processing LINE: {e}")
                self.skipped_entities += 1

        elif dxftype in ['LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'SPLINE']:
            try:
                # `make_path` extracts the geometric path for the entity.
                path = make_path(entity)
                
                # flattening() returns an iterator of Vec3
                vertices = list(path.flattening(distance=self.sagitta))
                
                if len(vertices) >= 2:
                    out_verts = []
                    for v in vertices:
                        vx, vy, vz = v.x * scale_factor, v.y * scale_factor, v.z * scale_factor
                        self._update_bounds(vx, vy)
                        out_verts.append({"x": vx, "y": vy, "z": vz})
                        
                    is_closed = False
                    if hasattr(entity, 'is_closed'):
                        is_closed = entity.is_closed
                    elif hasattr(entity, 'closed'):
                        is_closed = entity.closed
                    
                    self.entities.append({
                        "type": "LWPOLYLINE",
                        "layer": layer,
                        "block_name": block_name,
                        "vertices": out_verts,
                        "closed": is_closed
                    })
            except Exception as e:
                self.logger.warning(f"Error processing {dxftype}: {e}")
                self.skipped_entities += 1
                
        elif dxftype in ['TEXT', 'MTEXT']:
            try:
                ix, iy, iz = entity.dxf.insert.x * scale_factor, entity.dxf.insert.y * scale_factor, entity.dxf.insert.z * scale_factor
                text_content = entity.plain_text() if hasattr(entity, 'plain_text') else entity.dxf.text
                height = getattr(entity.dxf, 'height', 2.5) * scale_factor
                
                self._update_bounds(ix, iy)
                
                self.entities.append({
                    "type": dxftype,
                    "layer": layer,
                    "block_name": block_name,
                    "position": {"x": ix, "y": iy, "z": iz},
                    "height": height,
                    "text": text_content
                })
            except Exception as e:
                self.logger.warning(f"Error processing {dxftype} handle {getattr(entity.dxf, 'handle', '?')}: {e}")
                self.skipped_entities += 1
                
        elif dxftype == 'HATCH':
            try:
                paths = []
                try:
                    from ezdxf.path import make_paths
                    paths = list(make_paths(entity))
                except ImportError:
                    from ezdxf.path import make_path
                    paths = [make_path(entity)]
                
                for p in paths:
                    vertices = list(p.flattening(distance=self.sagitta))
                    if len(vertices) >= 2:
                        out_verts = []
                        for v in vertices:
                            vx, vy, vz = v.x * scale_factor, v.y * scale_factor, v.z * scale_factor
                            self._update_bounds(vx, vy)
                            out_verts.append({"x": vx, "y": vy, "z": vz})
                        
                        self.entities.append({
                            "type": "LWPOLYLINE",
                            "layer": layer,
                            "block_name": block_name,
                            "vertices": out_verts,
                            "closed": True
                        })
            except Exception as e:
                self.logger.warning(f"Unsupported or failed HATCH entity handle {getattr(entity.dxf, 'handle', '?')}: {e}")
                self.skipped_entities += 1

    def parse(self, filename: str, block_filter: Any = None) -> Dict[str, Any]:
        """
        Parses the DXF file using ezdxf and writes to outputs/dxf_raw.json.
        """
        if ezdxf is None:
            self.logger.error("ezdxf is not installed. DXFParser cannot run.")
            raise ImportError("ezdxf is required")

        if filename.startswith("/"):
            filepath = filename
        else:
            filepath = os.path.join(self.path_manager.workspace_root, filename)
            
        self.logger.info(f"DXFParser reading (ezdxf): {filepath}")

        doc = None
        try:
            # First try standard read
            doc = ezdxf.readfile(filepath)
        except Exception as e:
            self.logger.warning(f"Standard DXF read failed: {e}. Attempting smart repair on truncated file...")
            try:
                # Read original content as latin-1 to avoid decoding errors
                with open(filepath, "r", encoding="latin-1") as f:
                    content = f.read()
                
                # Check if it lacks EOF and add necessary tags
                if "EOF" not in content[-50:]:
                    lines = content.splitlines()
                    if lines and len(lines[-1].strip()) < 2:
                        lines = lines[:-1]
                    rebuilt_content = "\n".join(lines) + "\n"
                    # Safely terminate active blocks and sections
                    rebuilt_content += "  0\nENDBLK\n  0\nENDSEC\n  0\nSECTION\n  2\nENTITIES\n  0\nENDSEC\n  0\nEOF\n"
                    
                    repaired_filepath = filepath + ".repaired.dxf"
                    with open(repaired_filepath, "w", encoding="latin-1") as f:
                        f.write(rebuilt_content)
                    
                    self.logger.info(f"Temporary repaired DXF written to {repaired_filepath}")
                    try:
                        doc = ezdxf.readfile(repaired_filepath)
                        self.logger.info("Successfully loaded repaired file!")
                    except Exception as e_rep:
                        self.logger.warning(f"Failed to load repaired file directly: {e_rep}. Trying recover mode on repaired file...")
                        from ezdxf import recover
                        doc, auditor = recover.readfile(repaired_filepath)
                else:
                    raise e
            except Exception as e2:
                self.logger.warning(f"Smart repair failed: {e2}. Trying fallback recover mode on original...")
                try:
                    from ezdxf import recover
                    doc, auditor = recover.readfile(filepath)
                except Exception as e3:
                    self.logger.error(f"Failed to read DXF file even with recover: {e3}")
                    return {"error": str(e3), "entities": []}

        msp = doc.modelspace()
        
        # Determine unit scale factor from $INSUNITS header variable
        insunits = 0
        try:
            if doc and hasattr(doc, 'header') and '$INSUNITS' in doc.header:
                insunits = doc.header['$INSUNITS']
        except Exception:
            pass

        unit_scale_map = {
            1: 25.4,   # Inches to mm
            2: 304.8,  # Feet to mm
            4: 1.0,    # Millimeters
            5: 10.0,   # Centimeters to mm
            6: 1000.0  # Meters to mm
        }
        scale_factor = unit_scale_map.get(insunits, 1.0)
        self.logger.info(f"Detected DXF $INSUNITS={insunits}, unit scale factor to mm: {scale_factor}")

        self.entities = []
        self.min_x = float('inf')
        self.min_y = float('inf')
        self.max_x = float('-inf')
        self.max_y = float('-inf')

        for entity in msp:
            self._process_entity(entity, scale_factor=scale_factor)

        self.logger.info(f"Applied unit scale factor {scale_factor} during processing.")

        metadata = {
            "promoted_block": None,
            "promotion_reason": None,
        }
        
        # Handle block filter or smart block promotion
        enable_promotion = self.config.get("parser.block_promotion", True)
        if len(self.entities) == 0 and hasattr(doc, 'blocks') and enable_promotion:
            promoted = False
            if block_filter:
                self.logger.info(f"Block filter '{block_filter}' specified. Attempting to promote this block...")
                target_block = None
                for block in doc.blocks:
                    if block.name == block_filter or block.name.upper() == str(block_filter).upper():
                        target_block = block
                        break
                if not target_block:
                    for block in doc.blocks:
                        if str(block_filter).upper() in block.name.upper():
                            target_block = block
                            break
                if target_block:
                    self.logger.info(f"Promoting entities from filtered block '{target_block.name}' ({len(target_block)} entities) to modelspace.")
                    for entity in target_block:
                        self._process_entity(entity, block_name=target_block.name, scale_factor=scale_factor)
                    promoted = True
                    metadata["promoted_block"] = target_block.name
                    metadata["promotion_reason"] = "filter_match"
                else:
                    self.logger.warning(f"Specified block_filter '{block_filter}' not found in blocks.")

            if not promoted:
                self.logger.info("Modelspace is empty. Attempting smart block promotion...")
                candidate_blocks = []
                for block in doc.blocks:
                    name_upper = block.name.upper()
                    if "MODEL_SPACE" not in name_upper and "PAPER_SPACE" not in name_upper and not name_upper.startswith("_"):
                        if len(block) > 0:
                            candidate_blocks.append(block)
                
                if candidate_blocks:
                    # Weighted score: count + 100000 if it contains architectural keywords
                    def get_block_score(b):
                        name_upper = b.name.upper()
                        score = len(b)
                        arch_keywords = ["BLOK", "KAT", "PLAN", "MIMARI", "PROJE", "A-A", "B-B"]
                        if any(kw in name_upper for kw in arch_keywords):
                            score += 100000
                        return score

                    # Sort by score descending
                    candidate_blocks.sort(key=get_block_score, reverse=True)
                    best_block = candidate_blocks[0]
                    self.logger.info(f"Promoting entities from selected block '{best_block.name}' (score={get_block_score(best_block)}, count={len(best_block)}) to modelspace.")
                    for entity in best_block:
                        self._process_entity(entity, block_name=best_block.name, scale_factor=scale_factor)
                    metadata["promoted_block"] = best_block.name
                    metadata["promotion_reason"] = "heuristic_score"

        self.logger.info(f"Extracted {len(self.entities)} flat entities from DXF.")

        # Deterministic sorting of entities
        def get_entity_sort_key(e):
            geom = ""
            if e['type'] == 'LINE':
                geom = f"{e['start']['x']:.4f},{e['start']['y']:.4f},{e['end']['x']:.4f},{e['end']['y']:.4f}"
            elif e['type'] == 'LWPOLYLINE':
                verts = e.get('vertices', [])
                if verts:
                    geom = f"{verts[0]['x']:.4f},{verts[0]['y']:.4f},{len(verts)}"
            elif e['type'] in ['TEXT', 'MTEXT']:
                pos = e.get('position', {})
                geom = f"{pos.get('x', 0):.4f},{pos.get('y', 0):.4f},{e.get('text', '')}"
            return (e['type'], e['layer'], e['block_name'], geom)
            
        self.entities.sort(key=get_entity_sort_key)
        metadata["skipped_entities"] = self.skipped_entities

        output_payload = {
            "project": self.config.get("project.name", "KaRar Project"),
            "source_file": filename,
            "encoding": doc.encoding if hasattr(doc, 'encoding') else "utf-8",
            "bounding_box": {
                "min_x": self.min_x if self.min_x != float('inf') else 0.0,
                "min_y": self.min_y if self.min_y != float('inf') else 0.0,
                "max_x": self.max_x if self.max_x != float('-inf') else 0.0,
                "max_y": self.max_y if self.max_y != float('-inf') else 0.0
            },
            "metadata": metadata,
            "entities": self.entities
        }

        output_path = self.path_manager.get_path('outputs', 'dxf_raw.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False, sort_keys=True)

        self.logger.info(f"Raw DXF payloads exported successfully to {self.path_manager.get_relative_path(output_path)}")
        return output_payload

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    parser = DXFParser()
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_plan.dxf"
    block_filter = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        res = parser.parse(filename, block_filter)
        print(f"Parsed {len(res['entities'])} entities successfully!")
        print(f"Bounds: {res['bounding_box']}")
    except Exception as e:
        logging.error(f"Parse failed: {e}")
