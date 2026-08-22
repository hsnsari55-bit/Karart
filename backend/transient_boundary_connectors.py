"""Deterministic transient door/window connectors for effective topology only.

The records produced here are deliberately separate from physical ``edges``.
They describe source-backed connectivity evidence and must not be promoted to
walls, loops, faces, meshes, or the Canonical BIM Model.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


DEFAULT_TOLERANCE_MM = 0.01
ANGULAR_EPSILON = 1e-6
SUPPORTED_ENTITY_TYPES = frozenset({"LINE", "LWPOLYLINE", "POLYLINE"})
ROLE_BY_NORMALIZED_LAYER = {
    "kapi": "DOOR_PORTAL",
    "pencere": "WINDOW_OPENING",
}
SUPPORTED_ROLES = frozenset(ROLE_BY_NORMALIZED_LAYER.values())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _stable_value(value: Any) -> str:
    return _stable_json(value)


def normalize_layer(value: Any) -> str:
    """Return the locale-independent layer key used by the narrow classifier."""
    return str(value or "").casefold().translate(
        str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "�": "i"})
    ).strip()


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _point(value: Any) -> Tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    if not _finite_number(value[0]) or not _finite_number(value[1]):
        return None
    return float(value[0]), float(value[1])


def _source_value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _source_points(source: Any) -> List[Tuple[float, float]]:
    raw = _source_value(source, "points")
    if raw is None:
        raw = _source_value(source, "render_points", ())
    points = [_point(item) for item in (raw or ())]
    return [item for item in points if item is not None]


def _segments(points: Sequence[Tuple[float, float]], closed: bool) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    result = [(start, end) for start, end in zip(points, points[1:]) if start != end]
    if closed and len(points) > 2 and points[0] != points[-1]:
        result.append((points[-1], points[0]))
    return result


def _distance_to_finite_segment(
    point: Tuple[float, float], start: Tuple[float, float], end: Tuple[float, float]
) -> Tuple[float, float]:
    dx, dy = end[0] - start[0], end[1] - start[1]
    denominator = dx * dx + dy * dy
    if denominator <= 0.0:
        return math.dist(point, start), 0.0
    parameter = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / denominator
    bounded = min(1.0, max(0.0, parameter))
    projected = (start[0] + bounded * dx, start[1] + bounded * dy)
    return math.dist(point, projected), parameter


def _supporting_segment(
    first: Tuple[float, float],
    second: Tuple[float, float],
    segments: Sequence[Tuple[Tuple[float, float], Tuple[float, float]]],
    tolerance_mm: float,
) -> Tuple[Tuple[float, float], Tuple[float, float]] | None:
    for start, end in segments:
        first_distance, first_parameter = _distance_to_finite_segment(first, start, end)
        second_distance, second_parameter = _distance_to_finite_segment(second, start, end)
        segment_length = math.dist(start, end)
        parameter_tolerance = tolerance_mm / segment_length if segment_length > 0.0 else 0.0
        if (
            first_distance <= tolerance_mm
            and second_distance <= tolerance_mm
            and -parameter_tolerance - ANGULAR_EPSILON <= first_parameter <= 1.0 + parameter_tolerance + ANGULAR_EPSILON
            and -parameter_tolerance - ANGULAR_EPSILON <= second_parameter <= 1.0 + parameter_tolerance + ANGULAR_EPSILON
        ):
            return start, end
    return None


def _parallel_and_perpendicular(
    first: Tuple[float, float],
    second: Tuple[float, float],
    host_segments: Sequence[Tuple[Tuple[float, float], Tuple[float, float]]],
) -> bool:
    connector = (second[0] - first[0], second[1] - first[1])
    hosts = [(end[0] - start[0], end[1] - start[1]) for start, end in host_segments]
    lengths = [math.hypot(*connector), *(math.hypot(*host) for host in hosts)]
    if len(hosts) != 2 or min(lengths, default=0.0) <= 1e-9:
        return False
    cross = abs(hosts[0][0] * hosts[1][1] - hosts[0][1] * hosts[1][0]) / (lengths[1] * lengths[2])
    dots = [
        abs(connector[0] * host[0] + connector[1] * host[1]) / (lengths[0] * lengths[index + 1])
        for index, host in enumerate(hosts)
    ]
    return cross <= ANGULAR_EPSILON and max(dots) <= ANGULAR_EPSILON


def _primitive_signature(segments: Sequence[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[List[float]]:
    """Build an orientation- and translation-invariant finite geometry signature."""
    signature = []
    for start, end in segments:
        dx, dy = end[0] - start[0], end[1] - start[1]
        if dx < 0.0 or (abs(dx) <= 1e-12 and dy < 0.0):
            dx, dy = -dx, -dy
        signature.append([round(dx, 6), round(dy, 6), round(math.hypot(dx, dy), 6)])
    return sorted(signature)


def _rejection(source_id: Any, reason: str, detail: str = "") -> Dict[str, Any]:
    result = {"source_primitive_id": source_id, "reason": reason}
    if detail:
        result["detail"] = detail
    return result


def _graph_index(graph: Mapping[str, Any]) -> Tuple[Dict[Any, Tuple[float, float]], Dict[Any, Mapping[str, Any]], Dict[Any, List[Any]]]:
    nodes: Dict[Any, Tuple[float, float]] = {}
    for node in graph.get("nodes", ()) or ():
        if not isinstance(node, Mapping) or node.get("id") is None:
            continue
        coordinate = _point((node.get("x"), node.get("y")))
        if coordinate is not None:
            nodes[node["id"]] = coordinate

    edges: Dict[Any, Mapping[str, Any]] = {}
    incident: Dict[Any, List[Any]] = defaultdict(list)
    for edge in graph.get("edges", ()) or ():
        if not isinstance(edge, Mapping) or edge.get("id") is None:
            continue
        start, end = edge.get("from"), edge.get("to")
        if start not in nodes or end not in nodes or start == end:
            continue
        edges[edge["id"]] = edge
        incident[start].append(edge["id"])
        incident[end].append(edge["id"])
    for values in incident.values():
        values.sort(key=_stable_value)
    return nodes, edges, incident


def _host_segment(
    edge: Mapping[str, Any], nodes: Mapping[Any, Tuple[float, float]]
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    return nodes[edge["from"]], nodes[edge["to"]]


def _candidate_for_segment(
    source: Any,
    source_segments: Sequence[Tuple[Tuple[float, float], Tuple[float, float]]],
    support: Tuple[Tuple[float, float], Tuple[float, float]],
    role: str,
    raw_layer: Any,
    normalized_layer: str,
    nodes: Mapping[Any, Tuple[float, float]],
    edges: Mapping[Any, Mapping[str, Any]],
    incident: Mapping[Any, Sequence[Any]],
    tolerance_mm: float,
) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
    source_id = _source_value(source, "source_id")
    contacts = []
    for node_id, coordinate in nodes.items():
        if _supporting_segment(coordinate, coordinate, [support], tolerance_mm) is not None:
            contacts.append((node_id, coordinate))
    contacts.sort(key=lambda item: _stable_value(item[0]))
    if len(contacts) != 2:
        return None, None

    host_ids = []
    for node_id, _ in contacts:
        node_hosts = list(incident.get(node_id, ()))
        if len(node_hosts) != 1:
            return None, _rejection(source_id, "CONTACT_HAS_NON_UNIQUE_PHYSICAL_HOST", f"{node_id}:{len(node_hosts)}")
        host_ids.append(node_hosts[0])
    if host_ids[0] == host_ids[1]:
        return None, _rejection(source_id, "CONTACTS_SHARE_PHYSICAL_HOST")

    endpoints = [item[1] for item in contacts]
    host_segments = [_host_segment(edges[host_id], nodes) for host_id in host_ids]
    if not _parallel_and_perpendicular(endpoints[0], endpoints[1], host_segments):
        return None, _rejection(source_id, "HOSTS_NOT_PARALLEL_OR_CONNECTOR_NOT_PERPENDICULAR")

    source_handle = _source_value(source, "source_handle", _source_value(source, "root_source_id", source_id))
    root_source_id = _source_value(source, "root_source_id", source_handle)
    ancestry = list(_source_value(source, "insert_ancestry", ()) or ())
    stable_basis = {
        "role": role,
        "source_primitive_id": source_id,
        "source_handle": source_handle,
        "root_source_id": root_source_id,
        "insert_ancestry": ancestry,
        "primitive_signature": _primitive_signature(source_segments),
        "finite_segment_signature": _primitive_signature([support])[0],
    }
    stable_id = "ag04-" + hashlib.sha256(_stable_json(stable_basis).encode("utf-8")).hexdigest()[:16]
    ordered_contact_indices = sorted(range(2), key=lambda index: _stable_value(contacts[index][0]))
    endpoint_ids = [contacts[index][0] for index in ordered_contact_indices]
    endpoint_points = [contacts[index][1] for index in ordered_contact_indices]
    ordered_hosts = [host_ids[index] for index in ordered_contact_indices]
    length_mm = round(math.dist(endpoint_points[0], endpoint_points[1]), 6)
    return {
        "id": stable_id,
        "role": role,
        "physical": False,
        "from": endpoint_ids[0],
        "to": endpoint_ids[1],
        "endpoint_node_ids": endpoint_ids,
        "endpoints_mm": [[round(value, 6) for value in point] for point in endpoint_points],
        "host_edge_ids": ordered_hosts,
        "source_primitive_id": source_id,
        "source_handle": source_handle,
        "source_layer_raw": str(raw_layer),
        "source_layer_normalized": normalized_layer,
        "lineage": {"root_source_id": root_source_id, "insert_ancestry": ancestry},
        "finite_span_mm": [[round(value, 6) for value in point] for point in support],
        "length_mm": length_mm,
        "evidence_class": "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS",
        "reason": "TRANSIENT_TYPED_BOUNDARY_CONTINUITY",
    }, None


def _candidates_for_source(
    source: Any,
    nodes: Mapping[Any, Tuple[float, float]],
    edges: Mapping[Any, Mapping[str, Any]],
    incident: Mapping[Any, Sequence[Any]],
    tolerance_mm: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    source_id = _source_value(source, "source_id")
    if source_id in (None, ""):
        return [], [_rejection(source_id, "MISSING_SOURCE_PRIMITIVE_ID")]

    raw_layer = _source_value(source, "layer", "")
    normalized_layer = normalize_layer(raw_layer)
    role = ROLE_BY_NORMALIZED_LAYER.get(normalized_layer)
    if role is None:
        return [], [_rejection(source_id, "UNSUPPORTED_SOURCE_LAYER", normalized_layer)]

    entity_type = str(_source_value(source, "entity_type", _source_value(source, "type", ""))).upper()
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        return [], [_rejection(source_id, "UNSUPPORTED_SOURCE_ENTITY_TYPE", entity_type)]

    points = _source_points(source)
    closed = bool(_source_value(source, "closed", _source_value(source, "is_closed", False)))
    source_segments = _segments(points, closed)
    if not source_segments:
        return [], [_rejection(source_id, "SOURCE_HAS_NO_FINITE_SEGMENT")]

    candidates: List[Dict[str, Any]] = []
    rejections: List[Dict[str, Any]] = []
    for support in source_segments:
        candidate, rejection = _candidate_for_segment(
            source, source_segments, support, role, raw_layer, normalized_layer,
            nodes, edges, incident, tolerance_mm,
        )
        if candidate is not None:
            candidates.append(candidate)
        if rejection is not None:
            rejections.append(rejection)

    if candidates or rejections:
        return candidates, rejections

    primitive_contacts = [
        node_id for node_id, coordinate in nodes.items()
        if _supporting_segment(coordinate, coordinate, source_segments, tolerance_mm) is not None
    ]
    if len(primitive_contacts) == 2:
        return [], [_rejection(source_id, "CONTACTS_NOT_ON_ONE_FINITE_SOURCE_SPAN")]
    return [], [_rejection(source_id, "CONTACT_COUNT_NOT_TWO", str(len(primitive_contacts)))]


def generate_logical_connectors(
    graph: Mapping[str, Any], sources: Iterable[Any], tolerance_mm: float = DEFAULT_TOLERANCE_MM
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate only uniquely proven door/window connectors and explicit rejections."""
    if not _finite_number(tolerance_mm) or float(tolerance_mm) <= 0.0:
        raise ValueError("tolerance_mm must be a finite positive number")
    nodes, edges, incident = _graph_index(graph)
    candidates: List[Dict[str, Any]] = []
    rejections: List[Dict[str, Any]] = []
    ordered_sources = sorted(list(sources or ()), key=lambda item: _stable_value(_source_value(item, "source_id")))
    for source in ordered_sources:
        source_candidates, source_rejections = _candidates_for_source(source, nodes, edges, incident, float(tolerance_mm))
        candidates.extend(source_candidates)
        rejections.extend(source_rejections)

    by_id: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_id[candidate["id"]].append(candidate)
    unambiguous_candidates = []
    for group in by_id.values():
        if len(group) == 1:
            unambiguous_candidates.append(group[0])
            continue
        for candidate in group:
            rejections.append(_rejection(candidate["source_primitive_id"], "AMBIGUOUS_FINITE_SEGMENT_IDENTITY"))

    by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for candidate in unambiguous_candidates:
        by_pair[tuple(sorted((_stable_value(candidate["from"]), _stable_value(candidate["to"]))))].append(candidate)

    connectors = []
    for group in by_pair.values():
        if len(group) == 1:
            connectors.append(group[0])
            continue
        for candidate in group:
            rejections.append(_rejection(candidate["source_primitive_id"], "AMBIGUOUS_DUPLICATE_ENDPOINT_ASSIGNMENT"))

    connectors.sort(key=lambda item: item["id"])
    rejections.sort(key=lambda item: (_stable_value(item.get("source_primitive_id")), item["reason"], item.get("detail", "")))
    return {"logical_connectors": connectors, "rejections": rejections}


def validate_logical_connectors(
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    connectors: Iterable[Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate/deduplicate transient records without mutating physical topology."""
    graph_nodes, graph_edges, _ = _graph_index({"nodes": nodes, "edges": edges})
    valid: List[Dict[str, Any]] = []
    rejections: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_pairs = set()
    ordered = sorted(list(connectors or ()), key=lambda item: _stable_value(item.get("id") if isinstance(item, Mapping) else item))
    for connector in ordered:
        connector_id = connector.get("id") if isinstance(connector, Mapping) else None
        reason = None
        if not isinstance(connector, Mapping):
            reason = "CONNECTOR_NOT_OBJECT"
        elif not isinstance(connector_id, str) or not connector_id.startswith("ag04-"):
            reason = "INVALID_CONNECTOR_ID"
        elif connector.get("physical") is not False:
            reason = "CONNECTOR_MUST_BE_NON_PHYSICAL"
        elif connector.get("role") not in SUPPORTED_ROLES:
            reason = "INVALID_CONNECTOR_ROLE"
        elif connector.get("from") not in graph_nodes or connector.get("to") not in graph_nodes:
            reason = "CONNECTOR_NODE_REFERENCE_MISSING"
        elif connector.get("from") == connector.get("to"):
            reason = "CONNECTOR_SELF_LOOP"
        elif not isinstance(connector.get("host_edge_ids"), list) or len(connector["host_edge_ids"]) != 2:
            reason = "CONNECTOR_HOST_COUNT_NOT_TWO"
        elif len(set(_stable_value(item) for item in connector["host_edge_ids"])) != 2:
            reason = "CONNECTOR_HOSTS_NOT_DISTINCT"
        elif any(item not in graph_edges for item in connector["host_edge_ids"]):
            reason = "CONNECTOR_HOST_REFERENCE_MISSING"
        elif connector.get("source_primitive_id") in (None, ""):
            reason = "CONNECTOR_SOURCE_PROVENANCE_MISSING"
        elif connector.get("source_layer_normalized") not in ROLE_BY_NORMALIZED_LAYER:
            reason = "CONNECTOR_NORMALIZED_LAYER_INVALID"
        elif connector.get("evidence_class") != "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS":
            reason = "CONNECTOR_EVIDENCE_INVALID"
        elif not _finite_number(connector.get("length_mm")) or float(connector["length_mm"]) <= 0.0:
            reason = "CONNECTOR_LENGTH_INVALID"

        pair = None
        if isinstance(connector, Mapping):
            pair = tuple(sorted((_stable_value(connector.get("from")), _stable_value(connector.get("to")))))
        if reason is None and connector_id in seen_ids:
            reason = "DUPLICATE_CONNECTOR_ID"
        elif reason is None and pair in seen_pairs:
            reason = "DUPLICATE_CONNECTOR_ENDPOINT_PAIR"

        if reason is not None:
            rejections.append({"connector_id": connector_id, "reason": reason})
            continue
        seen_ids.add(connector_id)
        seen_pairs.add(pair)
        valid.append(dict(connector))

    return valid, rejections


def effective_edge_pairs(
    nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]], connectors: Iterable[Any]
) -> Tuple[List[Tuple[Any, Any]], List[Dict[str, Any]]]:
    """Project valid connectors to endpoint pairs for connectivity calculations."""
    valid, rejections = validate_logical_connectors(nodes, edges, connectors)
    return [(item["from"], item["to"]) for item in valid], rejections
