import json
import logging
import os
from typing import Dict, Any

from backend.path_manager import PathManager
from backend.transient_boundary_connectors import validate_logical_connectors

class ConstraintSolver:
    """
    Constraint Solver (Step 4 of KaRar Pipeline)
    Deterministically filters and deduplicates topology graph edges, passes graph structure
    through with resolved-artifact metadata, and persists the resolved graph output.
    """
    RESOLVED_GRAPH_FILENAME = "geometry_graph_resolved.json"

    def __init__(self):
        self.logger = logging.getLogger('KaRar-ConstraintSolver')
        self.path_manager = PathManager()

    @staticmethod
    def _stable_serialize(value: Any) -> str:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)

    def _edge_pair_key(self, edge: Dict[str, Any]):
        return tuple(
            sorted(
                (
                    self._stable_serialize(edge.get("from")),
                    self._stable_serialize(edge.get("to")),
                )
            )
        )

    def _edge_rank(self, edge: Dict[str, Any]) -> str:
        normalized_edge = {
            **edge,
            "from": self._edge_pair_key(edge)[0],
            "to": self._edge_pair_key(edge)[1],
        }
        return self._stable_serialize(normalized_edge)

    def run(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("Executing Constraint Solver on topology graph...")
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        loops = graph.get("loops")
        if loops is None:
            loops = graph.get("faces", [])

        # Deterministic constraint resolution:
        # 1. Remove duplicate overlapping edges by (from, to) node pair
        best_edges_by_pair = {}

        for edge in edges:
            n0 = edge.get("from")
            n1 = edge.get("to")
            if n0 is None or n1 is None or n0 == n1:
                continue
            key = self._edge_pair_key(edge)
            rank = self._edge_rank(edge)
            current = best_edges_by_pair.get(key)
            if current is None or rank < current[0]:
                best_edges_by_pair[key] = (rank, edge)

        resolved_edges = []
        emitted_pairs = set()
        for edge in edges:
            n0 = edge.get("from")
            n1 = edge.get("to")
            if n0 is None or n1 is None or n0 == n1:
                continue
            key = self._edge_pair_key(edge)
            if key in emitted_pairs:
                continue
            emitted_pairs.add(key)
            resolved_edges.append(best_edges_by_pair[key][1])

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

        if "logical_connectors" in graph:
            logical_connectors = graph.get("logical_connectors") or []
            resolved_connectors, connector_rejections = validate_logical_connectors(
                nodes,
                resolved_edges,
                logical_connectors,
            )
            resolved_graph.update(
                {
                    "logical_connectors": resolved_connectors,
                    "logical_connector_rejections": connector_rejections,
                    "initial_logical_connector_count": len(logical_connectors),
                    "resolved_logical_connector_count": len(resolved_connectors),
                }
            )

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
