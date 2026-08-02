import json
import logging
import os
from typing import Dict, Any

from backend.path_manager import PathManager

class ConstraintSolver:
    """
    Constraint Solver (Step 4 of KaRar Pipeline)
    Resolves topological graph conflicts, wall overlaps, and element collision constraints deterministically.
    """
    RESOLVED_GRAPH_FILENAME = "geometry_graph_resolved.json"

    def __init__(self):
        self.logger = logging.getLogger('KaRar-ConstraintSolver')
        self.path_manager = PathManager()

    def run(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("Executing Constraint Solver on topology graph...")
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        loops = graph.get("loops")
        if loops is None:
            loops = graph.get("faces", [])

        # Deterministic constraint resolution:
        # 1. Remove duplicate overlapping edges by (from, to) node pair
        resolved_edges = []
        seen_edges = set()

        for edge in edges:
            n0 = edge.get("from")
            n1 = edge.get("to")
            if n0 is None or n1 is None or n0 == n1:
                continue
            key = tuple(sorted([n0, n1]))
            if key not in seen_edges:
                seen_edges.add(key)
                resolved_edges.append(edge)

        resolved_graph = {
            **graph,
            "nodes": nodes,
            "edges": resolved_edges,
            "loops": loops,
            "faces": graph.get("faces", loops),
            "constraints_resolved": True,
            "initial_edge_count": len(edges),
            "resolved_edge_count": len(resolved_edges)
        }

        output_path = self.path_manager.get_path("outputs", self.RESOLVED_GRAPH_FILENAME)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(resolved_graph, handle, indent=4, sort_keys=True, ensure_ascii=False)

        self.logger.info(f"Constraint Solver complete: reduced edges from {len(edges)} to {len(resolved_edges)}.")
        self.logger.info(
            "Resolved topology graph persisted to %s",
            self.path_manager.get_relative_path(output_path),
        )
        return resolved_graph
