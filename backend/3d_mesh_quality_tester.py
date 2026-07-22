import json
import trimesh
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('KaRar-Mesh-QA')

def run_qa():
    logger.info("Loading BIM Model...")
    with open("outputs/bim_model.json", "r") as f:
        bim_data = json.load(f)

    logger.info("Loading Generated GLB Model...")
    # Load the GLB to check node names and meshes
    scene = trimesh.load("outputs/model.glb", force="scene")
    
    geometries = scene.geometry
    logger.info(f"Total Geometries in GLB: {len(geometries)}")
    
    qa_results = {
        "watertight_meshes": 0,
        "non_watertight_meshes": 0,
        "degenerate_faces": 0,
        "inverted_normals": 0,
        "uuid_matches": 0,
        "uuid_misses": 0
    }
    
    # Collect all UUIDs from BIM
    bim_uuids = set()
    for cat in ["walls", "columns", "windows", "spaces", "doors"]:
        for item in bim_data.get(cat, []):
            if "uuid" in item:
                bim_uuids.add(item["uuid"])

    wall_volumes = {}
    
    for name, geom in geometries.items():
        # Check UUID
        # Spaces create Floor_<uuid> and Ceil_<uuid>
        base_name = name.replace("Floor_", "").replace("Ceil_", "")
        if base_name in bim_uuids:
            qa_results["uuid_matches"] += 1
        else:
            qa_results["uuid_misses"] += 1
            
        # Mesh Quality
        if geom.is_watertight:
            qa_results["watertight_meshes"] += 1
        else:
            qa_results["non_watertight_meshes"] += 1
            
        if not geom.is_winding_consistent:
            qa_results["inverted_normals"] += 1
            
        # Volume / Faces check
        if geom.faces.shape[0] == 0:
            qa_results["degenerate_faces"] += 1

        if name in bim_uuids:
            wall_volumes[name] = geom.volume
            
    logger.info("--- QUALITY REPORT ---")
    logger.info(f"Watertight Meshes: {qa_results['watertight_meshes']}")
    logger.info(f"Non-watertight Meshes: {qa_results['non_watertight_meshes']}")
    logger.info(f"Inverted Normals: {qa_results['inverted_normals']}")
    logger.info(f"Degenerate Faces: {qa_results['degenerate_faces']}")
    logger.info(f"UUID Matches: {qa_results['uuid_matches']}")
    logger.info(f"UUID Misses: {qa_results['uuid_misses']}")

    # Large Project Scalability Simulation
    logger.info("Running Scalability Test (1000 Walls)...")
    from model_3d_generator import Model3DGenerator
    import copy
    
    large_bim = copy.deepcopy(bim_data)
    large_bim["walls"] = large_bim.get("walls", []) * 10
    large_bim["windows"] = large_bim.get("windows", []) * 10
    large_bim["columns"] = large_bim.get("columns", []) * 10
    
    with open("outputs/large_bim_model.json", "w") as f:
        json.dump(large_bim, f)
        
    start_time = time.time()
    gen = Model3DGenerator('outputs/large_bim_model.json', 'outputs/large_model.glb')
    gen.run()
    elapsed = time.time() - start_time
    logger.info(f"Scalability Test Completed in {elapsed:.2f} seconds.")

if __name__ == '__main__':
    run_qa()
