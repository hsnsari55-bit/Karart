import json
import logging
import os
import time
from collections import Counter, defaultdict
from typing import Dict, Any, List, Tuple, Optional

from backend.path_manager import PathManager

class TopologyValidationError(Exception):
    pass

class TopologyValidator:
    """
    Topology Validator (Mandatory Blocking Gate before Canonical Validator / Export)
    Ensures topological graph integrity, manifold compliance, and absence of severe defects.
    """
    def __init__(self, report_output_path: Optional[str] = None):
        self.logger = logging.getLogger('KaRar-TopologyValidator')
        self.path_manager = PathManager()
        self.min_loop_area = 1.0
        self.report_output_path = report_output_path or self.path_manager.get_path(
            'outputs', 'topology_validation_report.json'
        )

    def _write_report(self, report: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.report_output_path), exist_ok=True)
        with open(self.report_output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

    def _parse_node_id(self, node: Dict[str, Any], *, index: int) -> int:
        raw_node_id = node.get("id", index)
        try:
            return int(raw_node_id)
        except (TypeError, ValueError):
            raise TopologyValidationError(
                "Topology validation failed: "
                f"Node at index {index} contains invalid node id {raw_node_id!r}."
            )

    def _parse_edge_id(self, edge: Dict[str, Any], *, index: int) -> int:
        raw_edge_id = edge.get("id", index)
        try:
            return int(raw_edge_id)
        except (TypeError, ValueError):
            raise TopologyValidationError(
                "Topology validation failed: "
                f"Edge at index {index} contains invalid edge id {raw_edge_id!r}."
            )

    def _parse_edge_endpoints(
        self,
        edge: Dict[str, Any],
        *,
        edge_label: Any,
    ) -> Tuple[int, int]:
        try:
            return int(edge["from"]), int(edge["to"])
        except (KeyError, TypeError, ValueError):
            raise TopologyValidationError(
                "Topology validation failed: "
                f"Edge {edge_label} contains invalid endpoint node ids."
            )

    def _build_report(
        self,
        *,
        status: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        loops: List[Dict[str, Any]],
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        report = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "validator": "TopologyValidator",
            "status": status,
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges),
                "loops": len(loops),
            },
            "thresholds": {
                "min_loop_area": self.min_loop_area,
            },
            "checks": {
                "non_empty_nodes": len(nodes) > 0,
                "non_empty_edges": len(edges) > 0,
                "non_empty_loops": len(loops) > 0,
            },
        }
        if error is not None:
            report["error"] = error
        return report

    def _build_node_coord_map(self, nodes: List[Dict[str, Any]]) -> Dict[int, Tuple[float, float]]:
        node_coords: Dict[int, Tuple[float, float]] = {}
        for index, node in enumerate(nodes):
            node_id = self._parse_node_id(node, index=index)
            try:
                node_coords[node_id] = (
                    round(float(node["x"]), 3),
                    round(float(node["y"]), 3),
                )
            except (KeyError, TypeError, ValueError):
                raise TopologyValidationError(
                    "Topology validation failed: "
                    f"Node {node_id} contains invalid node coordinates."
                )
        return node_coords

    def _parse_boundary_point(
        self,
        point: Dict[str, Any],
        *,
        loop_id: Any,
        point_index: int,
    ) -> Tuple[float, float]:
        try:
            return (
                round(float(point["x"]), 3),
                round(float(point["y"]), 3),
            )
        except (KeyError, TypeError, ValueError):
            raise TopologyValidationError(
                "Topology validation failed: "
                f"Loop {loop_id} contains invalid boundary coordinates at point index {point_index}."
            )

    def _parse_loop_area(self, loop: Dict[str, Any], *, loop_id: Any) -> float:
        try:
            return float(loop.get("area", 0.0))
        except (TypeError, ValueError):
            raise TopologyValidationError(
                "Topology validation failed: "
                f"Loop {loop_id} contains invalid area metadata."
            )

    def _parse_loop_edge_ids(self, loop: Dict[str, Any], *, loop_id: Any) -> List[int]:
        raw_loop_edges = loop.get("edges", [])
        if not isinstance(raw_loop_edges, list):
            raise TopologyValidationError(
                "Topology validation failed: "
                f"Loop {loop_id} contains invalid edge references."
            )

        parsed_edge_ids: List[int] = []
        for edge_index, raw_edge_id in enumerate(raw_loop_edges):
            try:
                parsed_edge_ids.append(int(raw_edge_id))
            except (TypeError, ValueError):
                raise TopologyValidationError(
                    "Topology validation failed: "
                    f"Loop {loop_id} contains invalid edge reference {raw_edge_id!r} at index {edge_index}."
                )

        return parsed_edge_ids

    def _build_edge_coord_lookup(
        self,
        edges: List[Dict[str, Any]],
        node_coords: Dict[int, Tuple[float, float]],
    ) -> Dict[Tuple[Tuple[float, float], Tuple[float, float]], int]:
        edge_lookup = {}
        for index, edge in enumerate(edges):
            edge_id = self._parse_edge_id(edge, index=index)
            from_id, to_id = self._parse_edge_endpoints(edge, edge_label=edge_id)
            start = node_coords.get(from_id)
            end = node_coords.get(to_id)
            if start is None or end is None:
                raise TopologyValidationError(
                    f"Topology validation failed: Edge {edge_id} references missing node ids."
                )
            edge_lookup[(start, end)] = edge_id
            edge_lookup[(end, start)] = edge_id
        return edge_lookup

    def _compute_node_degrees(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[int, int]:
        degrees: Dict[int, int] = defaultdict(int)
        node_ids = {self._parse_node_id(node, index=index) for index, node in enumerate(nodes)}

        for index, edge in enumerate(edges):
            edge_id = self._parse_edge_id(edge, index=index)
            from_id, to_id = self._parse_edge_endpoints(edge, edge_label=edge_id)

            if from_id not in node_ids or to_id not in node_ids:
                raise TopologyValidationError(
                    f"Topology validation failed: Edge {edge_id} references missing node ids."
                )

            if from_id == to_id:
                degrees[from_id] += 2
            else:
                degrees[from_id] += 1
                degrees[to_id] += 1

        return {node_id: degrees.get(node_id, 0) for node_id in node_ids}

    def _validate_node_degree_metadata(
        self,
        nodes: List[Dict[str, Any]],
        computed_degrees: Dict[int, int],
    ):
        mismatches = []
        for index, node in enumerate(nodes):
            node_id = self._parse_node_id(node, index=index)
            if "degree" not in node:
                mismatches.append({
                    "node_id": node_id,
                    "expected": computed_degrees.get(node_id, 0),
                    "actual": None,
                })
                continue

            try:
                declared_degree = int(node.get("degree", 0))
            except (TypeError, ValueError):
                raise TopologyValidationError(
                    "Topology validation failed: "
                    f"Node {node_id} contains invalid degree metadata."
                )
            computed_degree = computed_degrees.get(node_id, 0)
            if declared_degree != computed_degree:
                mismatches.append({
                    "node_id": node_id,
                    "expected": computed_degree,
                    "actual": declared_degree,
                })

        if mismatches:
            raise TopologyValidationError(
                "Topology validation failed: Node degree metadata is inconsistent with edge connectivity "
                f"for nodes {mismatches}."
            )

    def _validate_no_dangling_nodes(self, computed_degrees: Dict[int, int]):
        dangling = [node_id for node_id, degree in sorted(computed_degrees.items()) if degree == 1]
        if dangling:
            raise TopologyValidationError(
                f"Topology validation failed: Dangling/open topology detected at node ids {dangling}."
            )

    def _validate_no_self_loop_or_duplicate_edges(self, edges: List[Dict[str, Any]]):
        self_loop_edge_ids = []
        undirected_edge_pairs = Counter()

        for index, edge in enumerate(edges):
            edge_id = self._parse_edge_id(edge, index=index)
            from_id, to_id = self._parse_edge_endpoints(edge, edge_label=edge_id)

            if from_id == to_id:
                self_loop_edge_ids.append(edge_id)

            undirected_edge_pairs[tuple(sorted((from_id, to_id)))] += 1

        if self_loop_edge_ids:
            raise TopologyValidationError(
                "Topology validation failed: Self-loop edges detected at edge ids "
                f"{sorted(self_loop_edge_ids)}."
            )

        duplicate_pairs = [
            {"nodes": [pair[0], pair[1]], "count": count}
            for pair, count in sorted(undirected_edge_pairs.items())
            if count > 1
        ]
        if duplicate_pairs:
            raise TopologyValidationError(
                "Topology validation failed: Duplicate undirected edges detected for node pairs "
                f"{duplicate_pairs}."
            )

    def _validate_single_connected_component(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ):
        node_ids = [self._parse_node_id(node, index=index) for index, node in enumerate(nodes)]
        if not node_ids:
            return

        adjacency: Dict[int, set] = {node_id: set() for node_id in node_ids}
        for index, edge in enumerate(edges):
            edge_id = self._parse_edge_id(edge, index=index)
            from_id, to_id = self._parse_edge_endpoints(edge, edge_label=edge_id)
            if from_id not in adjacency or to_id not in adjacency:
                raise TopologyValidationError(
                    f"Topology validation failed: Edge {edge_id} references missing node ids."
                )
            adjacency[from_id].add(to_id)
            adjacency[to_id].add(from_id)

        unvisited = set(node_ids)
        component_sizes: List[int] = []

        while unvisited:
            start = unvisited.pop()
            stack = [start]
            component_size = 0

            while stack:
                current = stack.pop()
                component_size += 1
                for neighbor in adjacency.get(current, set()):
                    if neighbor in unvisited:
                        unvisited.remove(neighbor)
                        stack.append(neighbor)

            component_sizes.append(component_size)

        if len(component_sizes) > 1:
            raise TopologyValidationError(
                "Topology validation failed: Disconnected components detected "
                f"({len(component_sizes)} components, sizes={sorted(component_sizes, reverse=True)})."
            )

    def _validate_loops(
        self,
        loops: List[Dict[str, Any]],
        edge_ids: set,
        edge_lookup: Dict[Tuple[Tuple[float, float], Tuple[float, float]], int],
    ):
        for loop in loops:
            loop_id = loop.get("id", "unknown")
            boundary = loop.get("boundary", [])
            loop_edges = self._parse_loop_edge_ids(loop, loop_id=loop_id)
            area = self._parse_loop_area(loop, loop_id=loop_id)

            if len(boundary) < 4:
                raise TopologyValidationError(
                    f"Topology validation failed: Loop {loop_id} boundary has insufficient points."
                )

            start_pt = self._parse_boundary_point(boundary[0], loop_id=loop_id, point_index=0)
            end_pt = self._parse_boundary_point(boundary[-1], loop_id=loop_id, point_index=len(boundary) - 1)
            if start_pt != end_pt:
                raise TopologyValidationError(
                    f"Topology validation failed: Loop {loop_id} boundary is open (not closed)."
                )

            if area <= self.min_loop_area:
                raise TopologyValidationError(
                    f"Topology validation failed: Loop {loop_id} is a tiny/sliver face (area={area})."
                )

            if len(set(loop_edges)) < 3:
                raise TopologyValidationError(
                    f"Topology validation failed: Loop {loop_id} has insufficient unique edge references."
                )

            missing_edge_ids = sorted(edge_id for edge_id in set(loop_edges) if edge_id not in edge_ids)
            if missing_edge_ids:
                raise TopologyValidationError(
                    f"Topology validation failed: Loop {loop_id} references missing edge ids {missing_edge_ids}."
                )

            boundary_edge_ids = []
            for idx in range(len(boundary) - 1):
                p0 = self._parse_boundary_point(boundary[idx], loop_id=loop_id, point_index=idx)
                p1 = self._parse_boundary_point(boundary[idx + 1], loop_id=loop_id, point_index=idx + 1)
                edge_id = edge_lookup.get((p0, p1))
                if edge_id is None:
                    raise TopologyValidationError(
                        f"Topology validation failed: Loop {loop_id} boundary segment {p0}->{p1} does not map to a graph edge."
                    )
                boundary_edge_ids.append(edge_id)

            if set(boundary_edge_ids) != set(loop_edges):
                raise TopologyValidationError(
                    f"Topology validation failed: Loop {loop_id} face-edge mapping is inconsistent with graph edges."
                )

    def validate(self, graph: Dict[str, Any]) -> bool:
        self.logger.info("Executing Topology Validator blocking check...")
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        loops = graph.get("loops", [])

        try:
            if not nodes:
                raise TopologyValidationError("Topology validation failed: Graph contains zero nodes.")
            if not edges:
                raise TopologyValidationError("Topology validation failed: Graph contains zero edges.")
            if not loops:
                raise TopologyValidationError("Topology validation failed: Graph contains zero closed loops.")

            node_coords = self._build_node_coord_map(nodes)
            computed_degrees = self._compute_node_degrees(nodes, edges)
            edge_lookup = self._build_edge_coord_lookup(edges, node_coords)

            self._validate_node_degree_metadata(nodes, computed_degrees)
            self._validate_no_dangling_nodes(computed_degrees)
            self._validate_no_self_loop_or_duplicate_edges(edges)
            self._validate_single_connected_component(nodes, edges)
            self._validate_loops(
                loops,
                {self._parse_edge_id(edge, index=index) for index, edge in enumerate(edges)},
                edge_lookup,
            )

            report = self._build_report(
                status="PASS",
                nodes=nodes,
                edges=edges,
                loops=loops,
            )
            report["checks"].update({
                "node_reference_integrity": True,
                "no_dangling_nodes": True,
                "degree_metadata_consistency": True,
                "no_self_loop_edges": True,
                "no_duplicate_undirected_edges": True,
                "single_connected_component": True,
                "all_loops_closed": True,
                "loop_area_integrity": True,
                "loop_edge_id_integrity": True,
                "loop_edge_reference_integrity": True,
                "sufficient_unique_loop_edges": True,
                "closed_loops": True,
                "no_tiny_sliver_faces": True,
                "face_edge_consistency": True,
            })
            self._write_report(report)

            self.logger.info(
                f"Topology Validator passed successfully ({len(nodes)} nodes, {len(edges)} edges, {len(loops)} loops)."
            )
            return True
        except TopologyValidationError as exc:
            report = self._build_report(
                status="FAIL",
                nodes=nodes,
                edges=edges,
                loops=loops,
                error=str(exc),
            )
            self._write_report(report)
            self.logger.error(str(exc))
            raise
