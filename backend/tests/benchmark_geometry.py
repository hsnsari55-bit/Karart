import os
import json
import time
import random
import sys

# Ensure backend imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.geometry_engine import GeometryEngine
from backend.path_manager import PathManager

def generate_synthetic_data(num_walls: int) -> dict:
    entities = []
    # Create a grid of lines, many overlapping and self-intersecting
    for i in range(num_walls):
        # Base coordinate
        x = float(random.randint(0, 10000))
        y = float(random.randint(0, 10000))
        
        # Decide entity type
        t = random.random()
        if t < 0.6:
            # Simple line
            entities.append({
                "type": "LINE",
                "layer": "Duvar",
                "block_name": "default",
                "start": {"x": x, "y": y, "z": 0.0},
                "end": {"x": x + 100.0, "y": y, "z": 0.0} # Collinear potentials
            })
        elif t < 0.8:
            # Overlapping / zero length
            entities.append({
                "type": "LINE",
                "layer": "Duvar",
                "block_name": "default",
                "start": {"x": x, "y": y, "z": 0.0},
                "end": {"x": x + 0.1, "y": y + 0.1, "z": 0.0} # Zero length after snapping
            })
        else:
            # Closed polyline (some valid, some self-intersecting)
            entities.append({
                "type": "LWPOLYLINE",
                "layer": "Duvar",
                "block_name": "default",
                "closed": True,
                "vertices": [
                    {"x": x, "y": y},
                    {"x": x + 100, "y": y + 100},
                    {"x": x, "y": y + 100},
                    {"x": x + 100, "y": y} # Self-intersecting bowtie
                ]
            })
            
    return {"entities": entities, "bounding_box": {"min_x": 0, "min_y": 0, "max_x": 10000, "max_y": 10000}}

def run_benchmark():
    pm = PathManager()
    output_path = pm.get_path('outputs', 'dxf_raw.json')
    
    scales = {
        "Small": 100,
        "Medium": 2000,
        "Large": 10000
    }
    
    print("========================================")
    print(" GEOMETRY ENGINE BENCHMARK (O(N log N)) ")
    print("========================================")
    
    for scale_name, num_entities in scales.items():
        print(f"\nRunning {scale_name} benchmark with {num_entities} synthetic entities...")
        
        data = generate_synthetic_data(num_entities)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        engine = GeometryEngine()
        
        start_mem = 0
        try:
            import resource
            start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except:
            pass
            
        t0 = time.time()
        engine.run()
        t1 = time.time()
        
        end_mem = 0
        try:
            import resource
            end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except:
            pass
            
        mem_used_mb = (end_mem - start_mem) / 1024.0 if start_mem > 0 else 0
        
        print(f"Time Taken: {(t1 - t0)*1000:.2f} ms")
        if mem_used_mb > 0:
            print(f"Peak Memory Added: {mem_used_mb:.2f} MB")
            
        print("Stats:", json.dumps(engine.stats, indent=2))
        
    print("\nBenchmark completed. Check outputs/geometry_qa_report.md for final QA state.")

if __name__ == '__main__':
    run_benchmark()
