import argparse
import json
import os
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from backend.path_manager import PathManager


class TopologyHealthReporter:
    """
    Non-blocking topology diagnostics reporter.
    Produces deterministic health metrics so graph quality drift can be observed
    even when the blocking validator is not triggered directly.
    """

    def __init__(self, report_output_path: Optional[str] = None):
        self.path_manager = PathManager()
        self.min_loop_area = 1.0
        self.report_output_path = report_output_path or self.path_manager.get_path(
            "outputs", "topology_health_report.json"
        )

    def _write_report(self, report: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.report_output_path), exist_ok=True)
        with open(self.report_output_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=4, ensure_ascii=False)

    def _extract_boundary_point(self, point: Any) -> Optional[Tuple[float, float]]:
        try:
            if isinstance(point, dict) and "x" in point and "y" in point:
                return (round(float(point["x"]), 3), round(float(point["y"]), 3))
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                return (round(float(point[0]), 3), round(float(point[1]), 3))
        except (TypeError, ValueError):
            return None
        return None

    def _try_parse_int(self, value: Any) -> Tuple[Optional[int], bool]:
        try:
            return int(value), True
        except (TypeError, ValueError):
            return None, False

    def _try_parse_float(self, value: Any) -> Tuple[Optional[float], bool]:
        try:
            return float(value), True
        except (TypeError, ValueError):
            return None, False

    def _extract_loop_edge_ids(self, loop: Dict[str, Any]) -> Tuple[List[int], bool]:
        raw_loop_edges = loop.get("edges", [])
        if not isinstance(raw_loop_edges, list):
            return [], False

        parsed_edge_ids: List[int] = []
        for raw_edge_id in raw_loop_edges:
            edge_id, is_valid = self._try_parse_int(raw_edge_id)
            if not is_valid or edge_id is None:
                return [], False
            parsed_edge_ids.append(edge_id)

        return parsed_edge_ids, True

    def _extract_valid_node_ids(self, nodes: List[Dict[str, Any]]) -> Tuple[List[int], List[Any]]:
        valid_node_ids: List[int] = []
        invalid_node_ids: List[Any] = []

        for index, node in enumerate(nodes):
            node_id, is_valid = self._try_parse_int(node.get("id", index))
            if not is_valid or node_id is None:
                invalid_node_ids.append(node.get("id", index))
                continue
            valid_node_ids.append(node_id)

        return sorted(valid_node_ids), invalid_node_ids

    def _extract_valid_edge_ids(self, edges: List[Dict[str, Any]]) -> Tuple[set, List[Any]]:
        valid_edge_ids = set()
        invalid_edge_ids: List[Any] = []

        for index, edge in enumerate(edges):
            edge_id, is_valid = self._try_parse_int(edge.get("id", index))
            if not is_valid or edge_id is None:
                invalid_edge_ids.append(edge.get("id", index))
                continue
            valid_edge_ids.add(edge_id)

        return valid_edge_ids, invalid_edge_ids

    def _build_node_coord_map(self, nodes: List[Dict[str, Any]]) -> Dict[int, Tuple[float, float]]:
        node_coords, _ = self._build_node_coord_map_with_invalid_ids(nodes)
        return node_coords

    def _build_node_coord_map_with_invalid_ids(
        self,
        nodes: List[Dict[str, Any]],
    ) -> Tuple[Dict[int, Tuple[float, float]], List[int]]:
        node_coords: Dict[int, Tuple[float, float]] = {}
        invalid_node_coordinate_ids: List[int] = []

        for index, node in enumerate(nodes):
            if "x" not in node or "y" not in node:
                continue

            node_id, is_valid_node_id = self._try_parse_int(node.get("id", index))
            if not is_valid_node_id or node_id is None:
                continue

            try:
                node_coords[node_id] = (
                    round(float(node["x"]), 3),
                    round(float(node["y"]), 3),
                )
            except (TypeError, ValueError):
                invalid_node_coordinate_ids.append(node_id)

        return node_coords, sorted(invalid_node_coordinate_ids)

    def _build_edge_coord_lookup(
        self,
        edges: List[Dict[str, Any]],
        node_coords: Dict[int, Tuple[float, float]],
    ) -> Dict[Tuple[Tuple[float, float], Tuple[float, float]], int]:
        edge_lookup: Dict[Tuple[Tuple[float, float], Tuple[float, float]], int] = {}
        for index, edge in enumerate(edges):
            edge_id, is_valid_edge_id = self._try_parse_int(edge.get("id", index))
            from_id, is_valid_from_id = self._try_parse_int(edge.get("from"))
            to_id, is_valid_to_id = self._try_parse_int(edge.get("to"))
            if (
                not is_valid_edge_id
                or edge_id is None
                or not is_valid_from_id
                or from_id is None
                or not is_valid_to_id
                or to_id is None
            ):
                continue

            start = node_coords.get(from_id)
            end = node_coords.get(to_id)
            if start is None or end is None:
                continue

            edge_lookup[(start, end)] = edge_id
            edge_lookup[(end, start)] = edge_id
        return edge_lookup

    def _detect_face_edge_inconsistencies(
        self,
        loops: List[Dict[str, Any]],
        edge_lookup: Dict[Tuple[Tuple[float, float], Tuple[float, float]], int],
        excluded_loop_ids: Optional[set] = None,
    ) -> List[Any]:
        inconsistent_loop_ids: List[Any] = []
        excluded_loop_ids = excluded_loop_ids or set()

        for index, loop in enumerate(loops):
            if "edges" not in loop:
                continue

            loop_id = loop.get("id", index)
            if loop_id in excluded_loop_ids:
                continue

            boundary = loop.get("boundary", [])
            loop_edges = loop.get("edges", [])

            if len(boundary) < 2:
                inconsistent_loop_ids.append(loop_id)
                continue

            boundary_edge_ids: List[int] = []
            inconsistent = False
            for idx in range(len(boundary) - 1):
                p0 = self._extract_boundary_point(boundary[idx])
                p1 = self._extract_boundary_point(boundary[idx + 1])
                if p0 is None or p1 is None:
                    inconsistent = True
                    break

                edge_id = edge_lookup.get((p0, p1))
                if edge_id is None:
                    inconsistent = True
                    break

                boundary_edge_ids.append(edge_id)

            if inconsistent or set(boundary_edge_ids) != set(loop_edges):
                inconsistent_loop_ids.append(loop_id)

        return inconsistent_loop_ids

    def _detect_missing_loop_edge_references(
        self,
        loops: List[Dict[str, Any]],
        valid_edge_ids: set,
        excluded_loop_ids: Optional[set] = None,
    ) -> List[Any]:
        missing_reference_loop_ids: List[Any] = []
        excluded_loop_ids = excluded_loop_ids or set()

        for index, loop in enumerate(loops):
            if "edges" not in loop:
                continue

            loop_id = loop.get("id", index)
            if loop_id in excluded_loop_ids:
                continue

            loop_edges, is_valid = self._extract_loop_edge_ids(loop)
            if not is_valid:
                continue
            if any(edge_id not in valid_edge_ids for edge_id in loop_edges):
                missing_reference_loop_ids.append(loop_id)

        return missing_reference_loop_ids

    def _detect_invalid_loop_edge_reference_lists(self, loops: List[Dict[str, Any]]) -> List[Any]:
        invalid_loop_edge_reference_loop_ids: List[Any] = []

        for index, loop in enumerate(loops):
            if "edges" not in loop:
                continue

            loop_id = loop.get("id", index)
            _, is_valid = self._extract_loop_edge_ids(loop)
            if not is_valid:
                invalid_loop_edge_reference_loop_ids.append(loop_id)

        return invalid_loop_edge_reference_loop_ids

    def _detect_insufficient_unique_loop_edges(
        self,
        loops: List[Dict[str, Any]],
        excluded_loop_ids: Optional[set] = None,
    ) -> List[Any]:
        insufficient_unique_edge_loop_ids: List[Any] = []
        excluded_loop_ids = excluded_loop_ids or set()

        for index, loop in enumerate(loops):
            loop_id = loop.get("id", index)
            if loop_id in excluded_loop_ids:
                continue

            loop_edges, is_valid = self._extract_loop_edge_ids(loop)
            if not is_valid:
                continue
            if len(set(loop_edges)) < 3:
                insufficient_unique_edge_loop_ids.append(loop_id)

        return insufficient_unique_edge_loop_ids

    def _detect_invalid_loop_areas(self, loops: List[Dict[str, Any]]) -> List[Any]:
        invalid_loop_area_ids: List[Any] = []

        for index, loop in enumerate(loops):
            loop_id = loop.get("id", index)
            _, is_valid = self._try_parse_float(loop.get("area", 0.0))
            if not is_valid:
                invalid_loop_area_ids.append(loop_id)

        return invalid_loop_area_ids

    def _compute_component_sizes(self, node_ids: List[int], adjacency: Dict[int, set]) -> List[int]:
        unvisited = set(node_ids)
        component_sizes: List[int] = []

        while unvisited:
            start = unvisited.pop()
            stack = [start]
            size = 0

            while stack:
                current = stack.pop()
                size += 1
                for neighbor in adjacency.get(current, set()):
                    if neighbor in unvisited:
                        unvisited.remove(neighbor)
                        stack.append(neighbor)

            component_sizes.append(size)

        return sorted(component_sizes, reverse=True)

    def _compute_components(
        self,
        node_ids: List[int],
        adjacency: Dict[int, set],
    ) -> List[List[int]]:
        unvisited = set(node_ids)
        components: List[List[int]] = []

        while unvisited:
            start = min(unvisited)
            stack = [start]
            unvisited.remove(start)
            component: List[int] = []

            while stack:
                current = stack.pop()
                component.append(current)
                next_neighbors = sorted(adjacency.get(current, set()) & unvisited, reverse=True)
                for neighbor in next_neighbors:
                    unvisited.remove(neighbor)
                    stack.append(neighbor)

            components.append(sorted(component))

        return sorted(components, key=lambda component: (-len(component), component))

    def _compute_node_degrees(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> Tuple[Dict[int, int], List[int], List[int], List[Any], List[Any]]:
        node_ids, invalid_node_ids = self._extract_valid_node_ids(nodes)
        node_id_set = set(node_ids)
        degrees = {node_id: 0 for node_id in node_ids}
        invalid_edge_reference_ids: List[int] = []
        invalid_edge_endpoint_ids: List[int] = []
        invalid_edge_ids: List[Any] = []

        for index, edge in enumerate(edges):
            edge_id, is_valid_edge_id = self._try_parse_int(edge.get("id", index))
            if not is_valid_edge_id or edge_id is None:
                invalid_edge_ids.append(edge.get("id", index))
                continue

            from_id, is_valid_from_id = self._try_parse_int(edge.get("from"))
            to_id, is_valid_to_id = self._try_parse_int(edge.get("to"))

            if not is_valid_from_id or from_id is None or not is_valid_to_id or to_id is None:
                invalid_edge_endpoint_ids.append(edge_id)
                continue

            if from_id not in node_id_set or to_id not in node_id_set:
                invalid_edge_reference_ids.append(edge_id)
                continue

            if from_id == to_id:
                degrees[from_id] += 2
            else:
                degrees[from_id] += 1
                degrees[to_id] += 1

        return (
            degrees,
            sorted(invalid_edge_reference_ids),
            sorted(invalid_edge_endpoint_ids),
            invalid_node_ids,
            invalid_edge_ids,
        )

    def _detect_degree_metadata_mismatches(
        self,
        nodes: List[Dict[str, Any]],
        computed_degrees: Dict[int, int],
    ) -> List[Dict[str, Any]]:
        mismatches: List[Dict[str, Any]] = []
        for index, node in enumerate(nodes):
            node_id, is_valid_node_id = self._try_parse_int(node.get("id", index))
            if not is_valid_node_id or node_id is None:
                continue
            computed_degree = computed_degrees.get(node_id, 0)
            if "degree" not in node:
                mismatches.append({
                    "node_id": node_id,
                    "expected": computed_degree,
                    "actual": None,
                })
                continue

            declared_degree, is_valid_degree = self._try_parse_int(node.get("degree", 0))
            if not is_valid_degree:
                mismatches.append({
                    "node_id": node_id,
                    "expected": computed_degree,
                    "actual": node.get("degree"),
                })
                continue
            if declared_degree != computed_degree:
                mismatches.append({
                    "node_id": node_id,
                    "expected": computed_degree,
                    "actual": declared_degree,
                })

        return mismatches

    def _build_issue_component_context(
        self,
        issue_node_ids: List[int],
        components: List[List[int]],
        component_index_by_node_id: Dict[int, int],
    ) -> List[Dict[str, Any]]:
        grouped_issue_nodes: Dict[int, List[int]] = {}

        for node_id in issue_node_ids:
            component_index = component_index_by_node_id.get(node_id)
            if component_index is None:
                continue
            grouped_issue_nodes.setdefault(component_index, []).append(node_id)

        return [
            {
                "component_index": component_index,
                "component_size": len(components[component_index]),
                "component_node_ids": components[component_index],
                "issue_node_ids": grouped_issue_nodes[component_index],
            }
            for component_index in sorted(grouped_issue_nodes)
        ]

    def _build_diagnostic(
        self,
        code: str,
        severity: str,
        message: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "code": code,
            "severity": severity,
            "message": message,
            "context": context,
        }

    def build_report(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        loops = graph.get("loops", [])

        node_ids, invalid_node_ids = self._extract_valid_node_ids(nodes)
        adjacency = {node_id: set() for node_id in node_ids}
        (
            degrees,
            invalid_edge_reference_ids,
            invalid_edge_endpoint_ids,
            computed_invalid_node_ids,
            invalid_edge_ids,
        ) = self._compute_node_degrees(nodes, edges)
        if not invalid_node_ids:
            invalid_node_ids = computed_invalid_node_ids
        invalid_edge_reference_id_set = set(invalid_edge_reference_ids)
        self_loop_edge_ids: List[int] = []
        edge_pair_counts: Counter[Tuple[int, int]] = Counter()

        for index, edge in enumerate(edges):
            edge_id, is_valid_edge_id = self._try_parse_int(edge.get("id", index))
            from_id, is_valid_from_id = self._try_parse_int(edge.get("from"))
            to_id, is_valid_to_id = self._try_parse_int(edge.get("to"))

            if (
                not is_valid_edge_id
                or edge_id is None
                or not is_valid_from_id
                or from_id is None
                or not is_valid_to_id
                or to_id is None
                or from_id not in adjacency
                or to_id not in adjacency
            ):
                continue

            adjacency[from_id].add(to_id)
            adjacency[to_id].add(from_id)

            if from_id == to_id:
                self_loop_edge_ids.append(edge_id)

            edge_pair_counts[tuple(sorted((from_id, to_id)))] += 1

        components = self._compute_components(node_ids, adjacency) if node_ids else []
        component_sizes = [len(component) for component in components]
        component_size_histogram = {
            str(size): count for size, count in sorted(Counter(component_sizes).items())
        }
        component_index_by_node_id = {
            node_id: component_index
            for component_index, component in enumerate(components)
            for node_id in component
        }
        dangling_node_ids = sorted(node_id for node_id, degree in degrees.items() if degree == 1)
        isolated_node_ids = sorted(node_id for node_id, degree in degrees.items() if degree == 0)
        dangling_node_component_indexes = sorted(
            {
                component_index_by_node_id[node_id]
                for node_id in dangling_node_ids
                if node_id in component_index_by_node_id
            }
        )
        isolated_node_component_indexes = sorted(
            {
                component_index_by_node_id[node_id]
                for node_id in isolated_node_ids
                if node_id in component_index_by_node_id
            }
        )
        dangling_node_components = self._build_issue_component_context(
            dangling_node_ids,
            components,
            component_index_by_node_id,
        )
        isolated_node_components = self._build_issue_component_context(
            isolated_node_ids,
            components,
            component_index_by_node_id,
        )
        degree_metadata_mismatches = self._detect_degree_metadata_mismatches(nodes, degrees)
        invalid_edge_reference_ids = sorted(invalid_edge_reference_id_set)
        duplicate_edge_pairs = [
            {"nodes": [pair[0], pair[1]], "count": count}
            for pair, count in sorted(edge_pair_counts.items())
            if count > 1
        ]

        valid_edge_ids, extracted_invalid_edge_ids = self._extract_valid_edge_ids(edges)
        if not invalid_edge_ids:
            invalid_edge_ids = extracted_invalid_edge_ids
        node_coords, invalid_node_coordinate_ids = self._build_node_coord_map_with_invalid_ids(nodes)
        edge_lookup = self._build_edge_coord_lookup(edges, node_coords)

        closed_loop_count = 0
        open_loop_ids: List[Any] = []
        tiny_loop_ids: List[Any] = []
        invalid_loop_area_ids = self._detect_invalid_loop_areas(loops)
        for index, loop in enumerate(loops):
            loop_id = loop.get("id", index)
            boundary = loop.get("boundary", [])
            area, is_valid_area = self._try_parse_float(loop.get("area", 0.0))

            start_point = self._extract_boundary_point(boundary[0]) if boundary else None
            end_point = self._extract_boundary_point(boundary[-1]) if boundary else None
            is_closed = len(boundary) >= 4 and start_point is not None and start_point == end_point

            if is_closed:
                closed_loop_count += 1
            else:
                open_loop_ids.append(loop_id)

            if is_valid_area and area is not None and area <= self.min_loop_area:
                tiny_loop_ids.append(loop_id)

        invalid_loop_edge_reference_loop_ids = self._detect_invalid_loop_edge_reference_lists(loops)
        missing_loop_edge_reference_loop_ids = self._detect_missing_loop_edge_references(
            loops,
            valid_edge_ids,
            set(invalid_loop_edge_reference_loop_ids),
        )
        insufficient_unique_loop_edge_loop_ids = self._detect_insufficient_unique_loop_edges(
            loops,
            set(invalid_loop_edge_reference_loop_ids),
        )
        face_edge_inconsistency_loop_ids = self._detect_face_edge_inconsistencies(
            loops,
            edge_lookup,
            set(invalid_loop_edge_reference_loop_ids)
            | set(missing_loop_edge_reference_loop_ids)
            | set(insufficient_unique_loop_edge_loop_ids),
        )

        checks = {
            "has_nodes": len(nodes) > 0,
            "has_edges": len(edges) > 0,
            "has_loops": len(loops) > 0,
            "non_empty_nodes": len(nodes) > 0,
            "non_empty_edges": len(edges) > 0,
            "non_empty_loops": len(loops) > 0,
            "node_id_integrity": len(invalid_node_ids) == 0,
            "edge_id_integrity": len(invalid_edge_ids) == 0,
            "edge_endpoint_integrity": len(invalid_edge_endpoint_ids) == 0,
            "node_coordinate_integrity": len(invalid_node_coordinate_ids) == 0,
            "node_reference_integrity": len(invalid_edge_reference_ids) == 0,
            "degree_metadata_consistency": len(degree_metadata_mismatches) == 0,
            "single_connected_component": len(component_sizes) <= 1,
            "no_dangling_nodes": len(dangling_node_ids) == 0,
            "no_isolated_nodes": len(isolated_node_ids) == 0,
            "no_self_loop_edges": len(self_loop_edge_ids) == 0,
            "all_loops_closed": len(open_loop_ids) == 0,
            "closed_loops": len(open_loop_ids) == 0,
            "loop_area_integrity": len(invalid_loop_area_ids) == 0,
            "no_tiny_loops": len(tiny_loop_ids) == 0,
            "no_tiny_sliver_faces": len(tiny_loop_ids) == 0,
            "loop_edge_id_integrity": len(invalid_loop_edge_reference_loop_ids) == 0,
            "loop_edge_reference_integrity": len(missing_loop_edge_reference_loop_ids) == 0,
            "sufficient_unique_loop_edges": len(insufficient_unique_loop_edge_loop_ids) == 0,
            "face_edge_consistency": len(face_edge_inconsistency_loop_ids) == 0,
            "no_duplicate_undirected_edges": len(duplicate_edge_pairs) == 0,
        }

        if (
            not checks["has_nodes"]
            or not checks["has_edges"]
            or not checks["node_id_integrity"]
            or not checks["edge_id_integrity"]
            or not checks["edge_endpoint_integrity"]
            or not checks["node_coordinate_integrity"]
            or not checks["node_reference_integrity"]
            or not checks["no_self_loop_edges"]
        ):
            status = "CRITICAL"
        elif all(checks.values()):
            status = "HEALTHY"
        else:
            status = "WARNING"

        issues = []
        diagnostics: List[Dict[str, Any]] = []
        if not checks["has_nodes"]:
            message = "Graph contains zero nodes"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "ZERO_NODES",
                    "CRITICAL",
                    message,
                    {},
                )
            )
        if not checks["has_edges"]:
            message = "Graph contains zero edges"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "ZERO_EDGES",
                    "CRITICAL",
                    message,
                    {},
                )
            )
        if not checks["has_loops"]:
            message = "Graph contains zero closed loops"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "ZERO_LOOPS",
                    "CRITICAL" if not checks["has_nodes"] and not checks["has_edges"] else "WARNING",
                    message,
                    {},
                )
            )
        if invalid_node_ids:
            message = f"Invalid node ids: {invalid_node_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_NODE_IDS",
                    "CRITICAL",
                    message,
                    {"node_ids": invalid_node_ids},
                )
            )
        if invalid_edge_ids:
            message = f"Invalid edge ids: {invalid_edge_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_EDGE_IDS",
                    "CRITICAL",
                    message,
                    {"edge_ids": invalid_edge_ids},
                )
            )
        if invalid_edge_endpoint_ids:
            message = f"Invalid edge endpoint ids: {invalid_edge_endpoint_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_EDGE_ENDPOINTS",
                    "CRITICAL",
                    message,
                    {"edge_ids": invalid_edge_endpoint_ids},
                )
            )
        
        if invalid_edge_reference_ids:
            message = f"Invalid edge references: {invalid_edge_reference_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_EDGE_REFERENCES",
                    "CRITICAL",
                    message,
                    {"edge_ids": invalid_edge_reference_ids},
                )
            )
        if invalid_node_coordinate_ids:
            message = f"Invalid node coordinates: {invalid_node_coordinate_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_NODE_COORDINATES",
                    "CRITICAL",
                    message,
                    {"node_ids": invalid_node_coordinate_ids},
                )
            )
        if degree_metadata_mismatches:
            message = (
                f"Node degree metadata mismatches detected: {degree_metadata_mismatches}"
            )
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "DEGREE_METADATA_MISMATCH",
                    "WARNING",
                    message,
                    {"mismatches": degree_metadata_mismatches},
                )
            )
        if len(component_sizes) > 1:
            message = f"Disconnected components detected: {len(component_sizes)}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "DISCONNECTED_COMPONENTS",
                    "WARNING",
                    message,
                    {
                        "component_count": len(component_sizes),
                        "component_sizes": component_sizes,
                        "component_size_histogram": component_size_histogram,
                        "component_node_groups": components,
                    },
                )
            )
        if dangling_node_ids:
            message = f"Dangling nodes detected: {dangling_node_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "DANGLING_NODES",
                    "WARNING",
                    message,
                    {
                        "node_ids": dangling_node_ids,
                        "component_indexes": dangling_node_component_indexes,
                        "components": dangling_node_components,
                    },
                )
            )
        if isolated_node_ids:
            message = f"Isolated nodes detected: {isolated_node_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "ISOLATED_NODES",
                    "WARNING",
                    message,
                    {
                        "node_ids": isolated_node_ids,
                        "component_indexes": isolated_node_component_indexes,
                        "components": isolated_node_components,
                    },
                )
            )
        if self_loop_edge_ids:
            message = f"Self-loop edges detected: {self_loop_edge_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "SELF_LOOP_EDGES",
                    "CRITICAL",
                    message,
                    {"edge_ids": self_loop_edge_ids},
                )
            )
        if open_loop_ids:
            message = f"Open loops detected: {open_loop_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "OPEN_LOOPS",
                    "WARNING",
                    message,
                    {"loop_ids": open_loop_ids},
                )
            )
        if tiny_loop_ids:
            message = f"Tiny loops detected: {tiny_loop_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "TINY_LOOPS",
                    "WARNING",
                    message,
                    {
                        "loop_ids": tiny_loop_ids,
                        "min_loop_area_threshold": self.min_loop_area,
                    },
                )
            )
        if invalid_loop_area_ids:
            message = f"Loops contain invalid area metadata: {invalid_loop_area_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_LOOP_AREAS",
                    "WARNING",
                    message,
                    {"loop_ids": invalid_loop_area_ids},
                )
            )
        if invalid_loop_edge_reference_loop_ids:
            message = f"Loops contain invalid edge reference lists: {invalid_loop_edge_reference_loop_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INVALID_LOOP_EDGE_REFERENCES",
                    "WARNING",
                    message,
                    {"loop_ids": invalid_loop_edge_reference_loop_ids},
                )
            )
        if missing_loop_edge_reference_loop_ids:
            message = f"Loops reference missing edge ids: {missing_loop_edge_reference_loop_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "MISSING_LOOP_EDGE_REFERENCES",
                    "WARNING",
                    message,
                    {"loop_ids": missing_loop_edge_reference_loop_ids},
                )
            )
        if insufficient_unique_loop_edge_loop_ids:
            message = (
                "Loops with insufficient unique edge references: "
                f"{insufficient_unique_loop_edge_loop_ids}"
            )
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "INSUFFICIENT_UNIQUE_LOOP_EDGES",
                    "WARNING",
                    message,
                    {"loop_ids": insufficient_unique_loop_edge_loop_ids},
                )
            )
        if duplicate_edge_pairs:
            message = "Duplicate undirected edges detected"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "DUPLICATE_UNDIRECTED_EDGES",
                    "WARNING",
                    message,
                    {"pairs": duplicate_edge_pairs},
                )
            )
        if face_edge_inconsistency_loop_ids:
            message = f"Face-edge inconsistencies detected: {face_edge_inconsistency_loop_ids}"
            issues.append(message)
            diagnostics.append(
                self._build_diagnostic(
                    "FACE_EDGE_INCONSISTENCY",
                    "WARNING",
                    message,
                    {"loop_ids": face_edge_inconsistency_loop_ids},
                )
            )

        degree_histogram = {
            str(degree): count for degree, count in sorted(Counter(degrees.values()).items())
        }

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reporter": "TopologyHealthReporter",
            "status": status,
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges),
                "loops": len(loops),
            },
            "graph_metrics": {
                "connected_components": len(component_sizes),
                "component_sizes": component_sizes,
                "component_node_groups": components,
                "component_size_histogram": component_size_histogram,
                "largest_component_size": component_sizes[0] if component_sizes else 0,
                "dangling_node_count": len(dangling_node_ids),
                "dangling_node_ids": dangling_node_ids,
                "dangling_node_component_indexes": dangling_node_component_indexes,
                "dangling_node_components": dangling_node_components,
                "isolated_node_count": len(isolated_node_ids),
                "isolated_node_ids": isolated_node_ids,
                "isolated_node_component_indexes": isolated_node_component_indexes,
                "isolated_node_components": isolated_node_components,
                "self_loop_edge_count": len(self_loop_edge_ids),
                "self_loop_edge_ids": self_loop_edge_ids,
                "invalid_node_ids": invalid_node_ids,
                "invalid_edge_ids": invalid_edge_ids,
                "invalid_edge_endpoint_ids": invalid_edge_endpoint_ids,
                "invalid_node_coordinate_ids": invalid_node_coordinate_ids,
                "invalid_edge_reference_ids": invalid_edge_reference_ids,
                "degree_metadata_mismatches": degree_metadata_mismatches,
                "duplicate_undirected_edges": duplicate_edge_pairs,
                "degree_histogram": degree_histogram,
            },
            "loop_metrics": {
                "closed_loop_count": closed_loop_count,
                "open_loop_count": len(open_loop_ids),
                "open_loop_ids": open_loop_ids,
                "invalid_loop_area_count": len(invalid_loop_area_ids),
                "invalid_loop_area_ids": invalid_loop_area_ids,
                "tiny_loop_count": len(tiny_loop_ids),
                "tiny_loop_ids": tiny_loop_ids,
                "invalid_loop_edge_reference_count": len(invalid_loop_edge_reference_loop_ids),
                "invalid_loop_edge_reference_loop_ids": invalid_loop_edge_reference_loop_ids,
                "missing_loop_edge_reference_count": len(missing_loop_edge_reference_loop_ids),
                "missing_loop_edge_reference_loop_ids": missing_loop_edge_reference_loop_ids,
                "insufficient_unique_loop_edge_count": len(insufficient_unique_loop_edge_loop_ids),
                "insufficient_unique_loop_edge_loop_ids": insufficient_unique_loop_edge_loop_ids,
                "face_edge_inconsistency_count": len(face_edge_inconsistency_loop_ids),
                "face_edge_inconsistency_loop_ids": face_edge_inconsistency_loop_ids,
                "min_loop_area_threshold": self.min_loop_area,
            },
            "checks": checks,
            "issues": issues,
            "diagnostics": diagnostics,
        }

    def generate(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        report = self.build_report(graph)
        self._write_report(report)
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate KaRar topology health diagnostics report")
    parser.add_argument("--graph", default=os.path.join("outputs", "geometry_graph.json"))
    parser.add_argument("--report", default=os.path.join("outputs", "topology_health_report.json"))
    args = parser.parse_args()

    with open(args.graph, "r", encoding="utf-8") as handle:
        graph = json.load(handle)

    reporter = TopologyHealthReporter(report_output_path=args.report)
    report = reporter.generate(graph)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()