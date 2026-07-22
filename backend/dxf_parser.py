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

    def _update_bounds(self, x: float, y: float):
        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)

    def _process_entity(self, entity, block_name="default"):
        """Recursively process entities, including nested block references (INSERT)"""
        dxftype = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0"

        if dxftype == 'INSERT':
            # ezdxf allows iterating through virtual entities with transformations applied
            try:
                for v_entity in entity.virtual_entities():
                    self._process_entity(v_entity, block_name=entity.dxf.name)
            except Exception as e:
                self.logger.warning(f"Error expanding block reference {entity.dxf.name}: {e}")

        elif dxftype == 'LINE':
            try:
                start = entity.dxf.start
                end = entity.dxf.end
                
                self._update_bounds(start.x, start.y)
                self._update_bounds(end.x, end.y)
                
                self.entities.append({
                    "type": "LINE",
                    "layer": layer,
                    "block_name": block_name,
                    "start": {"x": start.x, "y": start.y, "z": start.z},
                    "end": {"x": end.x, "y": end.y, "z": end.z}
                })
            except Exception as e:
                self.logger.warning(f"Error processing LINE: {e}")

        elif dxftype in ['LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'SPLINE']:
            try:
                # `make_path` extracts the geometric path for the entity.
                path = make_path(entity)
                
                # flattening() returns an iterator of Vec3
                vertices = list(path.flattening(distance=self.sagitta))
                
                if len(vertices) >= 2:
                    out_verts = []
                    for v in vertices:
                        self._update_bounds(v.x, v.y)
                        out_verts.append({"x": v.x, "y": v.y, "z": v.z})
                        
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
                
        elif dxftype in ['TEXT', 'MTEXT']:
            try:
                insert = entity.dxf.insert
                text_content = entity.plain_text() if hasattr(entity, 'plain_text') else entity.dxf.text
                height = getattr(entity.dxf, 'height', 2.5)
                
                self._update_bounds(insert.x, insert.y)
                
                self.entities.append({
                    "type": dxftype,
                    "layer": layer,
                    "block_name": block_name,
                    "position": {"x": insert.x, "y": insert.y, "z": insert.z},
                    "height": height,
                    "text": text_content
                })
            except Exception as e:
                pass

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
        
        self.entities = []
        self.min_x = float('inf')
        self.min_y = float('inf')
        self.max_x = float('-inf')
        self.max_y = float('-inf')

        for entity in msp:
            self._process_entity(entity)

        # Handle block filter or smart block promotion
        if len(self.entities) == 0 and hasattr(doc, 'blocks'):
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
                        self._process_entity(entity, block_name=target_block.name)
                    promoted = True
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
                        self._process_entity(entity, block_name=best_block.name)

        self.logger.info(f"Extracted {len(self.entities)} flat entities from DXF.")

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
            "entities": self.entities
        }

        output_path = self.path_manager.get_path('outputs', 'dxf_raw.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)

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
