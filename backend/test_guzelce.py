import os
import sys
import json
import logging

# Set up logging to terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] (%(name)s) - %(message)s')
logger = logging.getLogger("Test-Guzelce")

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from path_manager import PathManager
from dxf_parser import DXFParser
from geometry_engine import GeometryEngine
from topology_engine import TopologyEngine
from semantic_engine import SemanticEngine
from space_engine import SpaceEngine
from bim_core import BIMCoreEngine

def run_guzelce_pipeline():
    filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return

    logger.info("=== STARTING EXPERT BIM PIPELINE FOR GÜZELCE ===")
    
    # 1. PARSER
    parser = DXFParser()
    logger.info("Step 1: Parsing CAD DXF Entities...")
    raw_data = parser.parse(filepath)
    logger.info(f"  Successfully parsed {len(raw_data.get('entities', []))} entities.")
    logger.info(f"  Bounding Box: {raw_data.get('bounding_box')}")

    # 2. GEOMETRY
    geom_engine = GeometryEngine()
    logger.info("Step 2: Processing Geometry Clean-up (Collinear & Overlapping Wall Merging)...")
    walls_clean = geom_engine.run()
    logger.info(f"  Geometry complete. Cleaned walls count: {len(walls_clean)}")

    # 3. TOPOLOGY
    top_engine = TopologyEngine()
    logger.info("Step 3: Building Topological Connectivity Graph...")
    graph = top_engine.run()
    logger.info(f"  Topology graph complete. Nodes: {len(graph.get('nodes', []))}, Edges: {len(graph.get('edges', []))}")

    # 4. SEMANTIC
    sem_engine = SemanticEngine()
    logger.info("Step 4: Classifying Architectural Semantics (Wall, Column, Door, Window, Spaces)...")
    semantics = sem_engine.run()
    logger.info(f"  Semantic Classification complete. Generated {len(semantics.get('elements', []))} elements.")

    # 5. SPACE
    space_engine = SpaceEngine()
    logger.info("Step 5: Extracting Closed Spaces & Rooms...")
    spaces = space_engine.run()
    logger.info(f"  Space Extraction complete. Spaces found: {len(spaces.get('spaces', []))}")

    # 6. BIM CORE
    bim_core = BIMCoreEngine()
    logger.info("Step 6: Assembling Canonical BIM Model and exporting outputs...")
    bim_model = bim_core.run()
    logger.info("=== GÜZELCE PIPELINE VERIFICATION COMPLETED ===")
    
    # Save a verification report for UI or user output
    verification_path = "outputs/guzelce_verification_report.json"
    report = {
        "project": "GÜZELCE 467 ADA 3 PARSEL",
        "status": "SUCCESS",
        "parsed_entities": len(raw_data.get('entities', [])),
        "clean_walls": len(walls_clean),
        "topological_nodes": len(graph.get('nodes', [])),
        "topological_edges": len(graph.get('edges', [])),
        "semantic_elements": len(semantics.get('elements', [])),
        "extracted_spaces": len(spaces.get('spaces', [])),
        "bim_model": {
            "walls": len(bim_model.get("walls", [])),
            "spaces": len(bim_model.get("spaces", []))
        }
    }
    with open(verification_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Verification report successfully exported to {verification_path}")

if __name__ == "__main__":
    run_guzelce_pipeline()
