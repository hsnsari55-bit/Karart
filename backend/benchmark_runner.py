import os
import time
import json
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List

try:
    from backend.dxf_parser import DXFParser
    from backend.geometry_engine import GeometryEngine
    from backend.topology_engine import TopologyEngine
    from backend.semantic_engine import SemanticEngine
    from backend.space_engine import SpaceEngine
    from backend.bim_core import BIMCoreEngine
    from backend.path_manager import PathManager
except ImportError:
    from dxf_parser import DXFParser
    from geometry_engine import GeometryEngine
    from topology_engine import TopologyEngine
    from semantic_engine import SemanticEngine
    from space_engine import SpaceEngine
    from bim_core import BIMCoreEngine
    from path_manager import PathManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('KaRar-Benchmark')

def run_benchmark(dxf_path: str) -> Dict[str, Any]:
    filename = Path(dxf_path).name
    logger.info(f"--- Starting benchmark for {filename} ({dxf_path}) ---")
    
    metrics = {
        "file": filename,
        "path": str(dxf_path),
        "stages": {},
        "total_time_ms": 0,
        "peak_memory_kb": 0,
        "elements_detected": {},
        "status": "success",
        "error_message": None
    }
    
    start_time = time.time()
    tracemalloc.start()
    
    try:
        # 1. Parsing
        t0 = time.time()
        parser = DXFParser()
        parser.parse(dxf_path)
        metrics["stages"]["parsing_ms"] = (time.time() - t0) * 1000
        
        # 2. Geometry
        t0 = time.time()
        geo = GeometryEngine()
        geo.run()
        metrics["stages"]["geometry_ms"] = (time.time() - t0) * 1000
        
        # 3. Topology
        t0 = time.time()
        topo = TopologyEngine()
        topo.run()
        metrics["stages"]["topology_ms"] = (time.time() - t0) * 1000
        
        # 4. Semantic
        t0 = time.time()
        semantic = SemanticEngine()
        semantic.run()
        metrics["stages"]["semantic_ms"] = (time.time() - t0) * 1000
        
        # 5. Space
        t0 = time.time()
        space = SpaceEngine()
        space.run()
        metrics["stages"]["space_ms"] = (time.time() - t0) * 1000
        
        # 6. BIM Core
        t0 = time.time()
        bim = BIMCoreEngine()
        model = bim.run()
        metrics["stages"]["bim_core_ms"] = (time.time() - t0) * 1000
        
        # Extract counts
        if model:
            metrics["elements_detected"] = {
                "walls": len(model.get("walls", [])),
                "windows": len(model.get("windows", [])),
                "columns": len(model.get("columns", [])),
                "doors": len(model.get("doors", [])),
                "spaces": len(model.get("spaces", []))
            }
            
    except Exception as e:
        logger.error(f"Benchmark failed for {filename}: {str(e)}")
        metrics["status"] = "failed"
        metrics["error_message"] = str(e)
        
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    metrics["peak_memory_kb"] = peak / 1024
    metrics["total_time_ms"] = (time.time() - start_time) * 1000
    
    return metrics

if __name__ == "__main__":
    search_dirs = [Path("data"), Path("data/reference_set"), Path("datasets")]
    dxf_files = []
    seen = set()
    
    for sdir in search_dirs:
        if sdir.exists():
            for f in sdir.glob("**/*.dxf"):
                if f.name.endswith(".repaired.dxf"):
                    continue
                if f.name not in seen:
                    seen.add(f.name)
                    dxf_files.append(f)
                    
    dxf_files.sort(key=lambda x: x.name)
    
    if not dxf_files:
        logger.warning("No DXF files found for benchmarking.")
        exit(1)
        
    logger.info(f"Discovered {len(dxf_files)} real DXF dataset files for execution.")
    results = []
    for dxf in dxf_files:
        res = run_benchmark(str(dxf))
        results.append(res)
        
    pm = PathManager()
    report_path = pm.get_path("outputs", "benchmark_report.json")
    
    summary = {
        "total_datasets_evaluated": len(results),
        "successful_executions": sum(1 for r in results if r["status"] == "success"),
        "failed_executions": sum(1 for r in results if r["status"] == "failed"),
        "average_total_time_ms": round(sum(r["total_time_ms"] for r in results) / max(1, len(results)), 2),
        "peak_memory_kb": max((r["peak_memory_kb"] for r in results), default=0),
        "datasets": results
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
        
    logger.info(f"Benchmark completed across {len(results)} real dataset files. Verification report saved to {report_path}.")
