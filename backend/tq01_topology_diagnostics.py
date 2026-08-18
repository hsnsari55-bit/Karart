"""Read-only, deterministic TQ-01 topology qualification diagnostics.

The module never repairs geometry or relaxes a validator. It rebuilds topology
from an explicitly identified historical wall snapshot in an isolated directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import shutil
import tempfile
import uuid
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf import recover

from backend.dxf_parser import DXFParser
from backend.topology_engine import TopologyEngine
from backend.topology_validator import TopologyValidationError, TopologyValidator


PRODUCTION_TOLERANCE_MM = 5.0
TOLERANCE_BANDS_MM = (2.5, 4.0, 5.0, 6.0, 7.5, 10.0)
FORBIDDEN_DOWNSTREAM = (
    "bim_model.json", "model.glb", "model.obj", "model.blend", "preview.png"
)
CATEGORIES = (
    "endpoint-to-endpoint near miss",
    "endpoint-to-junction near miss",
    "endpoint-to-segment near miss",
    "legitimate architectural opening",
    "isolated annotation/non-wall",
    "truncated/incomplete",
    "wrong/incomplete block selection",
    "duplicate/overlap",
    "unresolved",
)
MANAGED_ARTIFACTS = (
    "TQ01_ENGINEERING_REPORT.md",
    "block_candidates.svg",
    "block_selection_audit.json",
    "component_inventory.json",
    "dangling_nodes.csv",
    "dangling_nodes.json",
    "manifest.json",
    "tolerance_sensitivity.json",
    "topology_overview.svg",
)


def validate_output_dir(output_dir: Path) -> Path:
    """Resolve a dedicated TQ-01 target without traversing directory symlinks."""
    lexical = Path(output_dir).absolute()
    for candidate in (lexical, *lexical.parents):
        if candidate.is_symlink():
            raise ValueError(f"Unsafe TQ-01 output symlink: {candidate}")

    resolved = lexical.resolve()
    repo_root = Path(__file__).resolve().parents[1]
    forbidden = {Path(resolved.anchor), repo_root, Path.cwd().resolve(), Path.home().resolve()}
    if resolved in forbidden:
        raise ValueError(f"Unsafe broad TQ-01 output target: {resolved}")

    destination_name = resolved.name.lower()
    dedicated = (
        destination_name == "tq01"
        or destination_name.startswith("tq01-")
        or destination_name.startswith("tq01_")
        or any(part.lower() == "tq01" for part in resolved.parts[:-1])
    )
    if not dedicated:
        raise ValueError(f"Output must be inside a dedicated TQ-01 directory: {resolved}")
    return resolved


def remove_tree_without_following_symlinks(path: Path) -> None:
    """Remove a package tree while unlinking, never traversing, symlinks."""
    if path.is_symlink() or not path.is_dir():
        path.unlink()
        return
    for child in path.iterdir():
        if child.is_symlink() or not child.is_dir():
            child.unlink()
        else:
            remove_tree_without_following_symlinks(child)
    path.rmdir()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(
        (
            json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    )


def isolated_path_manager(root: Path):
    """Minimal PathManager contract that keeps production writes under root."""
    return type(
        "IsolatedPathManager",
        (),
        {
            "workspace_root": str(root),
            "get_path": staticmethod(lambda *parts: str(root.joinpath(*parts))),
            "get_relative_path": staticmethod(lambda path: Path(path).name),
        },
    )()


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def projection(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> tuple[float, float]:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared < 1e-12:
        return distance(point, start), 0.0
    parameter = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dy
    ) / length_squared
    projected = (start[0] + parameter * dx, start[1] + parameter * dy)
    return distance(point, projected), parameter


def rebuild_graph(
    walls_path: Path, simulation_tolerance_mm: float | None = None
) -> tuple[dict, dict, float]:
    """Run the frozen Topology Engine while redirecting every write to temp."""
    with tempfile.TemporaryDirectory(prefix="karar-tq01-") as temp_dir:
        outputs = Path(temp_dir) / "outputs"
        outputs.mkdir()
        shutil.copyfile(walls_path, outputs / "walls_clean.json")
        engine = TopologyEngine()
        configured_tolerance = float(engine.snap_tolerance)
        if simulation_tolerance_mm is None:
            if configured_tolerance != PRODUCTION_TOLERANCE_MM:
                raise RuntimeError(
                    "configuration-drift: production snap_tolerance is "
                    f"{configured_tolerance} mm; expected {PRODUCTION_TOLERANCE_MM} mm"
                )
        else:
            engine.snap_tolerance = float(simulation_tolerance_mm)
        engine.path_manager = isolated_path_manager(Path(temp_dir))
        graph = engine.run()
        stable_stats = {
            key: value
            for key, value in engine.stats.items()
            if key != "processing_time_ms"
        }
        return graph, stable_stats, configured_tolerance


def component_inventory(graph: dict) -> tuple[list[dict], dict[int, int]]:
    adjacency: dict[int, set[int]] = defaultdict(set)
    for node in graph["nodes"]:
        adjacency[node["id"]]
    for edge in graph["edges"]:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])

    groups = []
    unseen = set(adjacency)
    while unseen:
        seed = min(unseen)
        queue = deque([seed])
        group = []
        unseen.remove(seed)
        while queue:
            current = queue.popleft()
            group.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        groups.append(sorted(group))
    groups.sort(key=lambda node_ids: (-len(node_ids), node_ids))

    node_to_component = {
        node_id: component_id
        for component_id, node_ids in enumerate(groups)
        for node_id in node_ids
    }
    edges_by_component: dict[int, list[int]] = defaultdict(list)
    for edge in graph["edges"]:
        edges_by_component[node_to_component[edge["from"]]].append(edge["id"])
    dangling = {node["id"] for node in graph["nodes"] if node["degree"] == 1}
    inventory = [
        {
            "component_id": component_id,
            "node_count": len(node_ids),
            "edge_count": len(edges_by_component[component_id]),
            "node_ids": node_ids,
            "edge_ids": sorted(edges_by_component[component_id]),
            "dangling_node_ids": sorted(dangling.intersection(node_ids)),
        }
        for component_id, node_ids in enumerate(groups)
    ]
    return inventory, node_to_component


def wall_provenance(
    point: tuple[float, float], other: tuple[float, float], walls: list[dict]
) -> dict:
    matches = []
    for wall in walls:
        points = wall.get("points", [])
        if len(points) < 2:
            continue
        start, end = tuple(points[0][:2]), tuple(points[1][:2])
        first_distance, first_parameter = projection(point, start, end)
        second_distance, second_parameter = projection(other, start, end)
        if (
            first_distance <= 0.01
            and second_distance <= 0.01
            and -1e-9 <= first_parameter <= 1.0 + 1e-9
            and -1e-9 <= second_parameter <= 1.0 + 1e-9
        ):
            matches.append(
                (
                    wall.get("layer", "UNKNOWN"),
                    wall.get("block_name", "UNKNOWN"),
                    wall.get("type", "UNKNOWN"),
                )
            )
    unique = sorted(set(matches))
    if len(unique) == 1:
        layer, block, entity_type = unique[0]
        return {
            "layer": layer,
            "block": block,
            "entity_type": entity_type,
            "entity_id": "UNKNOWN",
        }
    return {
        "layer": "UNKNOWN",
        "block": "UNKNOWN",
        "entity_type": "UNKNOWN",
        "entity_id": "UNKNOWN",
    }


def candidate_measurements(graph: dict, node: dict, incident_edge_id: int) -> dict:
    point = (node["x"], node["y"])
    nodes_by_id = {item["id"]: item for item in graph["nodes"]}
    incident_edge = next(
        edge for edge in graph["edges"] if edge["id"] == incident_edge_id
    )
    incident_node_ids = {incident_edge["from"], incident_edge["to"]}
    endpoint_candidates = sorted(
        (distance(point, (other["x"], other["y"])), other["id"])
        for other in graph["nodes"]
        if other["id"] not in incident_node_ids and other.get("degree") == 1
    )
    junction_candidates = sorted(
        (distance(point, (other["x"], other["y"])), other["id"])
        for other in graph["nodes"]
        if other["id"] not in incident_node_ids and other.get("degree", 0) > 2
    )
    segment_candidates = []
    for edge in graph["edges"]:
        if edge["id"] == incident_edge_id or node["id"] in (
            edge["from"], edge["to"]
        ):
            continue
        start = nodes_by_id[edge["from"]]
        end = nodes_by_id[edge["to"]]
        segment_distance, parameter = projection(
            point,
            (start["x"], start["y"]),
            (end["x"], end["y"]),
        )
        if 0.0 < parameter < 1.0:
            segment_candidates.append((segment_distance, edge["id"], parameter))
    segment_candidates.sort()
    endpoint = endpoint_candidates[0] if endpoint_candidates else (None, None)
    junction = junction_candidates[0] if junction_candidates else (None, None)
    segment = segment_candidates[0] if segment_candidates else (None, None, None)
    return {
        "nearest_endpoint_distance_mm": (
            None if endpoint[0] is None else round(endpoint[0], 6)
        ),
        "nearest_endpoint_node_id": endpoint[1],
        "nearest_junction_distance_mm": (
            None if junction[0] is None else round(junction[0], 6)
        ),
        "nearest_junction_node_id": junction[1],
        "nearest_nonincident_segment_distance_mm": (
            None if segment[0] is None else round(segment[0], 6)
        ),
        "nearest_nonincident_segment_edge_id": segment[1],
        "projection_parameter": (
            None if segment[2] is None else round(segment[2], 9)
        ),
        "endpoint_candidate_count_at_production_tolerance": sum(
            value < PRODUCTION_TOLERANCE_MM for value, _ in endpoint_candidates
        ),
        "junction_candidate_count_at_production_tolerance": sum(
            value < PRODUCTION_TOLERANCE_MM for value, _ in junction_candidates
        ),
        "segment_candidate_count_at_production_tolerance": sum(
            value < PRODUCTION_TOLERANCE_MM
            for value, _, _ in segment_candidates
        ),
    }


def dangling_inventory(
    graph: dict, walls: list[dict], node_to_component: dict[int, int]
) -> list[dict]:
    incident: dict[int, list[dict]] = defaultdict(list)
    for edge in graph["edges"]:
        incident[edge["from"]].append(edge)
        incident[edge["to"]].append(edge)
    component_sizes = Counter(node_to_component.values())
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    records = []
    for node in graph["nodes"]:
        if node["degree"] != 1:
            continue
        edge = incident[node["id"]][0]
        other_id = edge["to"] if edge["from"] == node["id"] else edge["from"]
        other = nodes_by_id[other_id]
        measurement = candidate_measurements(graph, node, edge["id"])
        endpoint_hit = (
            measurement["endpoint_candidate_count_at_production_tolerance"] > 0
        )
        junction_hit = (
            measurement["junction_candidate_count_at_production_tolerance"] > 0
        )
        segment_hit = (
            measurement["segment_candidate_count_at_production_tolerance"] > 0
        )
        if endpoint_hit:
            classification = CATEGORIES[0]
            evidence = "Distinct endpoint strictly inside frozen 5.0 mm tolerance."
        elif junction_hit:
            classification = CATEGORIES[1]
            evidence = "Nonincident junction strictly inside frozen 5.0 mm tolerance."
        elif segment_hit:
            classification = CATEGORIES[2]
            evidence = "Nonincident segment interior strictly inside frozen 5.0 mm tolerance."
        else:
            classification = CATEGORIES[-1]
            evidence = (
                "No geometric candidate inside production tolerance; "
                "architectural intent unavailable."
            )
        component_id = node_to_component[node["id"]]
        records.append(
            {
                "node_id": node["id"],
                "x": node["x"],
                "y": node["y"],
                "component_id": component_id,
                "component_size": component_sizes[component_id],
                "incident_edge_id": edge["id"],
                "incident_edge_length_mm": edge["length"],
                "provenance": wall_provenance(
                    (node["x"], node["y"]),
                    (other["x"], other["y"]),
                    walls,
                ),
                **measurement,
                "production_tolerance_candidate": (
                    endpoint_hit or junction_hit or segment_hit
                ),
                "classification": classification,
                "evidence": evidence,
            }
        )
    return records


def tolerance_sensitivity(dangling: list[dict]) -> dict:
    bands = []
    for tolerance in TOLERANCE_BANDS_MM:
        endpoint_nodes = [
            item["node_id"]
            for item in dangling
            if item["nearest_endpoint_distance_mm"] is not None
            and item["nearest_endpoint_distance_mm"] < tolerance
        ]
        junction_nodes = [
            item["node_id"]
            for item in dangling
            if item["nearest_junction_distance_mm"] is not None
            and item["nearest_junction_distance_mm"] < tolerance
        ]
        segment_nodes = [
            item["node_id"]
            for item in dangling
            if item["nearest_nonincident_segment_distance_mm"] is not None
            and item["nearest_nonincident_segment_distance_mm"] < tolerance
        ]
        candidate_sets = [set(endpoint_nodes), set(junction_nodes), set(segment_nodes)]
        ambiguous_nodes = sorted(
            set().union(
                *(left.intersection(right)
                  for index, left in enumerate(candidate_sets)
                  for right in candidate_sets[index + 1:])
            )
        )
        bands.append(
            {
                "tolerance_mm": tolerance,
                "endpoint_to_endpoint_candidate_node_ids": endpoint_nodes,
                "endpoint_to_junction_candidate_node_ids": junction_nodes,
                "endpoint_to_segment_candidate_node_ids": segment_nodes,
                "predicted_max_dangling_reduction": len(
                    set(endpoint_nodes + junction_nodes + segment_nodes)
                ),
                "ambiguous_candidate_node_ids": ambiguous_nodes,
                "ambiguity_count": len(ambiguous_nodes),
                "ambiguity": "multiple_candidate_types_within_band",
                "false_link_risk": "unquantified_without_architectural_ground_truth",
            }
        )
    return {
        "production_tolerance_mm": PRODUCTION_TOLERANCE_MM,
        "production_config_modified": False,
        "comparison_rule": (
            "strict distance less than band; segment projection strictly interior"
        ),
        "method": "in-memory measurement only; no candidate applied to geometry",
        "determinism": "candidate ordering is (distance, target id)",
        "accuracy_claim": "none_without_ground_truth",
        "bands": bands,
    }


def svg_transform(graph: dict, width: int = 1400, height: int = 900):
    xs = [node["x"] for node in graph["nodes"]] or [0.0, 1.0]
    ys = [node["y"] for node in graph["nodes"]] or [0.0, 1.0]
    bounds = min(xs), min(ys), max(xs), max(ys)
    scale = min(
        (width - 160) / max(bounds[2] - bounds[0], 1.0),
        (height - 120) / max(bounds[3] - bounds[1], 1.0),
    )

    def transform(x: float, y: float) -> tuple[float, float]:
        return (
            80 + (x - bounds[0]) * scale,
            height - 60 - (y - bounds[1]) * scale,
        )

    return transform, bounds, scale


def topology_svg(
    graph: dict, dangling: list[dict], node_to_component: dict[int, int]
) -> str:
    transform, bounds, scale = svg_transform(graph)
    palette = ("#2563eb", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#64748b")
    dangling_ids = {item["node_id"] for item in dangling}
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g stroke-width="1.5" fill="none">',
    ]
    for edge in graph["edges"]:
        start = nodes_by_id[edge["from"]]
        end = nodes_by_id[edge["to"]]
        x1, y1 = transform(start["x"], start["y"])
        x2, y2 = transform(end["x"], end["y"])
        color = palette[node_to_component[edge["from"]] % len(palette)]
        lines.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
            f'y2="{y2:.2f}" stroke="{color}"/>'
        )
    lines.append('</g><g fill="none" stroke="#eab308" stroke-width="3">')
    for loop in graph["loops"]:
        points = " ".join(
            f'{transform(point["x"], point["y"])[0]:.2f},'
            f'{transform(point["x"], point["y"])[1]:.2f}'
            for point in loop["boundary"]
        )
        lines.append(f'<polyline points="{points}" opacity="0.65"/>')
    lines.append('</g><g font-family="monospace" font-size="8">')
    for node in graph["nodes"]:
        x, y = transform(node["x"], node["y"])
        is_dangling = node["id"] in dangling_ids
        fill = "#dc2626" if is_dangling else "#111827"
        radius = 3 if is_dangling else 1.5
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{fill}"/>')
        if is_dangling:
            label = html.escape(f'N{node["id"]}')
            lines.append(
                f'<text x="{x + 4:.2f}" y="{y - 4:.2f}" fill="#991b1b">'
                f'{label}</text>'
            )
    lines.append('</g>')
    for item in dangling:
        target_id = item["nearest_endpoint_node_id"]
        if (
            target_id is not None
            and item["nearest_endpoint_distance_mm"] is not None
            and item["nearest_endpoint_distance_mm"] < PRODUCTION_TOLERANCE_MM
        ):
            node = nodes_by_id[item["node_id"]]
            target = nodes_by_id[target_id]
            x1, y1 = transform(node["x"], node["y"])
            x2, y2 = transform(target["x"], target["y"])
            lines.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
                f'y2="{y2:.2f}" stroke="#dc2626" stroke-dasharray="5 4"/>'
            )
        junction_id = item["nearest_junction_node_id"]
        if (
            junction_id is not None
            and item["nearest_junction_distance_mm"] is not None
            and item["nearest_junction_distance_mm"] < PRODUCTION_TOLERANCE_MM
        ):
            node = nodes_by_id[item["node_id"]]
            junction = nodes_by_id[junction_id]
            x1, y1 = transform(node["x"], node["y"])
            x2, y2 = transform(junction["x"], junction["y"])
            lines.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
                f'y2="{y2:.2f}" stroke="#059669" stroke-dasharray="2 3"/>'
            )
        segment_id = item["nearest_nonincident_segment_edge_id"]
        parameter = item["projection_parameter"]
        if (
            segment_id is not None
            and parameter is not None
            and item["nearest_nonincident_segment_distance_mm"] is not None
            and item["nearest_nonincident_segment_distance_mm"]
            < PRODUCTION_TOLERANCE_MM
        ):
            node = nodes_by_id[item["node_id"]]
            segment = next(edge for edge in graph["edges"] if edge["id"] == segment_id)
            start = nodes_by_id[segment["from"]]
            end = nodes_by_id[segment["to"]]
            projected_x = start["x"] + parameter * (end["x"] - start["x"])
            projected_y = start["y"] + parameter * (end["y"] - start["y"])
            x1, y1 = transform(node["x"], node["y"])
            x2, y2 = transform(projected_x, projected_y)
            lines.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
                f'y2="{y2:.2f}" stroke="#7c3aed" stroke-dasharray="3 3"/>'
            )
    lines.extend(
        [
            '<text x="20" y="24" font-family="sans-serif" font-size="16">'
            'TQ-01 topology overview</text>',
            f'<text x="20" y="48" font-family="monospace" font-size="11">'
            f'bbox={html.escape(str(bounds))}; scale={scale:.6f}px/mm; deterministic component colors</text>',
            '<g font-family="sans-serif" font-size="11">',
            '<text x="1050" y="24">Legend</text>',
            '<circle cx="1060" cy="45" r="3" fill="#dc2626"/>',
            '<text x="1070" y="49">dangling node + ID</text>',
            '<line x1="1050" y1="65" x2="1080" y2="65" stroke="#dc2626" '
            'stroke-dasharray="5 4"/>',
            '<text x="1090" y="69">endpoint near-miss</text>',
            '<line x1="1050" y1="85" x2="1080" y2="85" stroke="#059669" '
            'stroke-dasharray="2 3"/>',
            '<text x="1090" y="89">endpoint-to-junction near-miss</text>',
            '<line x1="1050" y1="105" x2="1080" y2="105" stroke="#7c3aed" '
            'stroke-dasharray="3 3"/>',
            '<text x="1090" y="109">endpoint-to-segment near-miss</text>',
            '<line x1="1050" y1="125" x2="1080" y2="125" stroke="#eab308" '
            'stroke-width="3"/>',
            '<text x="1090" y="129">closed-loop boundary</text>',
            '<text x="1050" y="149">edge color = component ID modulo palette</text>',
            '</g>',
            '</svg>\n',
        ]
    )
    return "".join(lines)


def block_svg(raw: dict) -> str:
    promoted = raw.get("metadata", {}).get("promoted_block", "UNKNOWN")
    count = sum(
        entity.get("block_name") == promoted for entity in raw.get("entities", [])
    )
    promoted_label = html.escape(str(promoted), quote=True)
    bounds = html.escape(
        json.dumps(raw.get("bounding_box", "UNKNOWN"), sort_keys=True),
        quote=True,
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240">'
        '<rect width="100%" height="100%" fill="white" stroke="#334155"/>'
        '<text x="24" y="45" font-family="sans-serif" font-size="22">Recorded parser block candidate</text>'
        f'<text x="24" y="90" font-family="monospace">name={promoted_label}</text>'
        f'<text x="24" y="125" font-family="monospace">recorded entities={count}</text>'
        f'<text x="24" y="160" font-family="monospace">bbox={bounds}</text>'
        '<text x="24" y="205" font-family="sans-serif" fill="#991b1b">'
        'Historical snapshot; not a successful re-parse of the truncated source.</text>'
        '</svg>\n'
    )


def normalize_exception(exc: BaseException, private_paths: list[Path]) -> dict:
    evidence = " ".join(str(exc).split())
    for private_path in private_paths:
        for candidate in {str(private_path), private_path.as_posix()}:
            evidence = evidence.replace(candidate, "<isolated-path>")
    evidence = re.sub(r"<isolated-path>(?:[\\/][^\s:'\"]+)*", "<isolated-path>", evidence)
    return {"type": type(exc).__name__, "evidence": evidence}


def document_counts(doc: Any) -> dict:
    user_blocks = [
        block
        for block in doc.blocks
        if "MODEL_SPACE" not in block.name.upper()
        and "PAPER_SPACE" not in block.name.upper()
    ]
    return {
        "modelspace_entities": sum(1 for _ in doc.modelspace()),
        "block_count": len(user_blocks),
        "nonempty_blocks": sum(len(block) > 0 for block in user_blocks),
        "block_entities": sum(len(block) for block in user_blocks),
    }


def probe_standard_read(source: Path) -> dict:
    result = {"status": "NOT_EXECUTED"}
    with tempfile.TemporaryDirectory(prefix="karar-tq01-standard-") as temp_dir:
        root = Path(temp_dir)
        copy = root / "source.dxf"
        shutil.copyfile(source, copy)
        try:
            result = {"status": "PASS", **document_counts(ezdxf.readfile(copy))}
        except Exception as exc:  # Evidence must preserve the production library result.
            result = {
                "status": "FAIL",
                "exception": normalize_exception(exc, [root, copy]),
            }
    return result


def probe_production_parser(source: Path) -> dict:
    result = {"status": "NOT_EXECUTED"}
    with tempfile.TemporaryDirectory(prefix="karar-tq01-parser-") as temp_dir:
        root = Path(temp_dir)
        copy = root / "source.dxf"
        shutil.copyfile(source, copy)
        try:
            parser = DXFParser()
            parser.path_manager = isolated_path_manager(root)
            payload = parser.parse(str(copy))
            entities = payload.get("entities", [])
            block_entity_counts = dict(
                sorted(
                    Counter(
                        entity.get("block_name", "UNKNOWN")
                        for entity in entities
                    ).items()
                )
            )
            repaired_copy_created = Path(f"{copy}.repaired.dxf").exists()
            if payload.get("error"):
                result = {
                    "status": "FAIL",
                    "entity_count": len(entities),
                    "block_count": len(block_entity_counts),
                    "block_entity_counts": block_entity_counts,
                    "repaired_copy_created": repaired_copy_created,
                    "exception": {
                        "type": "ParserReturnedError",
                        "evidence": normalize_exception(
                            RuntimeError(payload["error"]), [root, copy]
                        )["evidence"],
                    },
                }
            else:
                result = {
                    "status": "PASS",
                    "entity_count": len(entities),
                    "block_count": len(block_entity_counts),
                    "block_entity_counts": block_entity_counts,
                    "repaired_copy_created": repaired_copy_created,
                    "promoted_block": payload.get("metadata", {}).get(
                        "promoted_block"
                    ),
                    "skipped_entities": payload.get("metadata", {}).get(
                        "skipped_entities", 0
                    ),
                }
        except Exception as exc:
            result = {
                "status": "FAIL",
                "exception": normalize_exception(exc, [root, copy]),
            }
    return result


def probe_original_recover(source: Path) -> dict:
    result = {"status": "NOT_EXECUTED"}
    with tempfile.TemporaryDirectory(prefix="karar-tq01-recover-") as temp_dir:
        root = Path(temp_dir)
        copy = root / "source.dxf"
        shutil.copyfile(source, copy)
        try:
            doc, _auditor = recover.readfile(copy)
            counts = document_counts(doc)
            status = (
                "PASS"
                if counts["modelspace_entities"] + counts["block_entities"] > 0
                else "EMPTY_GEOMETRY"
            )
            result = {"status": status, **counts}
        except Exception as exc:
            result = {
                "status": "FAIL",
                "exception": normalize_exception(exc, [root, copy]),
            }
    return result


def source_audit(source: Path, raw_path: Path, raw: dict) -> dict:
    text_tail = source.read_bytes()[-256:].decode("latin-1", errors="replace")
    promoted = raw.get("metadata", {}).get("promoted_block", "UNKNOWN")
    entities = raw.get("entities", [])
    grouped = Counter(
        entity.get("block_name", "UNKNOWN") for entity in entities
    )
    return {
        "source": {
            "name": source.name,
            "size_bytes": source.stat().st_size,
            "sha256": sha256_file(source),
            "structurally_truncated": "EOF" not in text_tail[-50:],
            "tail_latin1": text_tail,
            "standard_read": probe_standard_read(source),
            "production_smart_repair": probe_production_parser(source),
            "original_recover": probe_original_recover(source),
        },
        "historical_snapshot": {
            "name": raw_path.name,
            "sha256": sha256_file(raw_path),
            "entity_count": len(entities),
            "source_file_field": raw.get("source_file"),
            "reproduction_equivalence": "NOT_EVALUATED",
        },
        "block_candidates": [
            {
                "name": name,
                "recorded_entity_count": count,
                "nested_insert_count": "UNKNOWN",
                "bbox": raw.get("bounding_box") if name == promoted else "UNKNOWN",
            }
            for name, count in sorted(grouped.items())
        ],
        "selection": {
            "promoted_block": promoted,
            "reason": raw.get("metadata", {}).get(
                "promotion_reason", "UNKNOWN"
            ),
            "deterministic_score": "UNKNOWN",
            "plan_plausibility": "UNVERIFIED_NO_GROUND_TRUTH",
            "selection_changed": False,
        },
    }


def failed_validator_check(error: str) -> str:
    mappings = (
        ("zero nodes", "non_empty_nodes"),
        ("zero edges", "non_empty_edges"),
        ("zero closed loops", "non_empty_loops"),
        ("degree metadata", "degree_metadata_consistency"),
        ("Dangling/open topology", "no_dangling_nodes"),
        ("Self-loop edges", "no_self_loop_edges"),
        ("Duplicate undirected edges", "no_duplicate_undirected_edges"),
        ("Disconnected components", "single_connected_component"),
        ("boundary is open", "all_loops_closed"),
        ("tiny/sliver face", "loop_area_integrity"),
        ("insufficient unique edge", "sufficient_unique_loop_edges"),
        ("references missing edge", "loop_edge_reference_integrity"),
        ("does not map to a graph edge", "face_edge_consistency"),
        ("face-edge mapping is inconsistent", "face_edge_consistency"),
        ("references missing node", "node_reference_integrity"),
        ("invalid endpoint node ids", "node_reference_integrity"),
    )
    return next((check for phrase, check in mappings if phrase in error), "validator_exception")


def validate_topology_graph(graph: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="karar-tq01-validator-") as temp_dir:
        report_path = Path(temp_dir) / "topology_validation_report.json"
        validator = TopologyValidator(report_output_path=str(report_path))
        try:
            validator.validate(graph)
        except TopologyValidationError as exc:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            error = str(exc)
            return {
                "topology": "FAIL",
                "validator_error": error,
                "failed_check": failed_validator_check(error),
                "validator_report_status": report["status"],
                "no_safe_repair_proven": True,
                "safe_repair_evidence": (
                    "No repair was executed; candidate measurements do not prove "
                    "architectural intent or a safe automatic repair."
                ),
                "downstream_executed": False,
            }
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return {
            "topology": "PASS",
            "validator_error": None,
            "failed_check": None,
            "validator_report_status": report["status"],
            "no_safe_repair_proven": False,
            "safe_repair_evidence": "Not applicable because frozen validation passed.",
            "downstream_executed": False,
        }


def engineering_report(
    counts: dict, hashes: dict, classes: Counter, audit: dict, gate: dict
) -> str:
    question = (
        "Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in "
        "doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir "
        "şekilde artırıyor mu?"
    )
    source_statuses = {
        name: audit["source"][name]["status"]
        for name in ("standard_read", "production_smart_repair", "original_recover")
    }
    status = (
        "TQ-01 QUALIFIED_BLOCKED_NO_SAFE_FIX"
        if gate["topology"] == "FAIL" and gate["no_safe_repair_proven"]
        else "TQ-01 QUALIFIED"
    )
    return f"""# Kanıt

- RV-01 walls snapshot SHA-256: `{hashes['walls']}`.
- İki izole rebuild aynı graph SHA-256 üretti: `{hashes['graph']}`.
- Ölçüm: {counts['walls']} walls, {counts['nodes']} nodes, {counts['edges']} edges, {counts['loops']} loops, {counts['components']} components, {counts['dangling']} dangling.
- Kaynak DXF SHA-256: `{hashes['source']}`; execution-derived probe statüleri: `{source_statuses}`.
- Sınıflandırma: `{dict(sorted(classes.items()))}`.

# Risk Analizi

- Snapshot graph deterministik; source-to-snapshot eşitliği probe sonuçlarından ayrıca kanıtlanmış değildir.
- Geometry/Topology kontratı entity kimliği taşımadığından entity provenance `UNKNOWN`.
- Ground truth olmadan unresolved uçların opening veya engine bug olduğu iddia edilemez.

# Önerilen Çözüm

- Tam kaynak veya insan-onaylı recovery politikası sağlanmalı; otomatik kapanış tahmini yapılmamalı.
- Parser recovery ve block-selection provenance ayrı ADR ile ele alınmalı; frozen tolerans değiştirilmemeli.

# Uygulanan Değişiklik

- Production engine değiştirilmedi. İzole read-only diagnostic ve raw-byte manifest eklendi.
- {question} **HAYIR.** Production core değişmedi; yalnız observability ve reproducibility iyileştirildi.

# Doğrulama

- İki rebuild hash’i eşit; production config değiştirilmedi.
- Frozen TopologyValidator gate: `{gate['topology']}`; failed_check=`{gate['failed_check']}`; downstream çalıştırılmadı.
- Accuracy/F1/IoU iddiası yok.

# Kalan Riskler

- Tam DXF ve ground truth olmadan block completeness ve legitimate openings doğrulanamaz.
- Safe automatic repair uygulanmadı; status `{status}`.
"""


def write_csv(path: Path, dangling: list[dict]) -> None:
    fields = [
        "node_id", "x", "y", "component_id", "component_size",
        "incident_edge_id", "incident_edge_length_mm", "layer", "block",
        "entity_type", "entity_id", "nearest_endpoint_node_id",
        "nearest_endpoint_distance_mm", "nearest_junction_node_id",
        "nearest_junction_distance_mm", "nearest_nonincident_segment_edge_id",
        "nearest_nonincident_segment_distance_mm", "projection_parameter",
        "production_tolerance_candidate", "classification", "evidence",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in dangling:
            row = {key: item.get(key) for key in fields}
            row.update(item["provenance"])
            writer.writerow(row)


def run_diagnostics(
    source: Path, walls_path: Path, raw_path: Path, output_dir: Path
) -> dict:
    output_dir = validate_output_dir(output_dir)
    source = source.resolve()
    walls_path = walls_path.resolve()
    raw_path = raw_path.resolve()
    walls = json.loads(walls_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    graph_a, stats_a, configured_tolerance_a = rebuild_graph(walls_path)
    graph_b, stats_b, configured_tolerance_b = rebuild_graph(walls_path)
    graph_hash_a = hashlib.sha256(
        json.dumps(graph_a, indent=4, sort_keys=True).encode("utf-8")
    ).hexdigest()
    graph_hash_b = hashlib.sha256(
        json.dumps(graph_b, indent=4, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if (
        graph_hash_a != graph_hash_b
        or stats_a != stats_b
        or configured_tolerance_a != configured_tolerance_b
    ):
        raise RuntimeError("Topology rebuild is not deterministic")

    components, node_to_component = component_inventory(graph_a)
    dangling = dangling_inventory(graph_a, walls, node_to_component)
    counts = {
        "walls": len(walls),
        "nodes": len(graph_a["nodes"]),
        "edges": len(graph_a["edges"]),
        "loops": len(graph_a["loops"]),
        "components": len(components),
        "dangling": len(dangling),
    }
    hashes = {
        "source": sha256_file(source),
        "walls": sha256_file(walls_path),
        "graph": graph_hash_a,
    }
    audit = source_audit(source, raw_path, raw)
    gate = validate_topology_graph(graph_a)
    status = (
        "TQ-01 QUALIFIED_BLOCKED_NO_SAFE_FIX"
        if gate["topology"] == "FAIL" and gate["no_safe_repair_proven"]
        else "TQ-01 QUALIFIED"
    )

    with tempfile.TemporaryDirectory(prefix="karar-tq01-package-") as temp_dir:
        staging = Path(temp_dir)
        write_json(staging / "block_selection_audit.json", audit)
        (staging / "block_candidates.svg").write_text(
            block_svg(raw), encoding="utf-8", newline="\n"
        )
        write_json(
            staging / "dangling_nodes.json",
            {"categories": CATEGORIES, "count": len(dangling), "nodes": dangling},
        )
        write_csv(staging / "dangling_nodes.csv", dangling)
        write_json(
            staging / "component_inventory.json",
            {"count": len(components), "components": components},
        )
        (staging / "topology_overview.svg").write_text(
            topology_svg(graph_a, dangling, node_to_component),
            encoding="utf-8",
            newline="\n",
        )
        sensitivity = tolerance_sensitivity(dangling)
        sensitivity["configured_snap_tolerance_mm"] = configured_tolerance_a
        write_json(staging / "tolerance_sensitivity.json", sensitivity)
        report = engineering_report(
            counts,
            hashes,
            Counter(item["classification"] for item in dangling),
            audit,
            gate,
        )
        (staging / "TQ01_ENGINEERING_REPORT.md").write_text(
            report, encoding="utf-8", newline="\n"
        )

        artifact_names = sorted(set(MANAGED_ARTIFACTS) - {"manifest.json"})
        manifest = {
            "schema_version": "tq01-manifest-v1",
            "status": status,
            "hard_gate": gate,
            "counts": counts,
            "configuration": {
                "configured_snap_tolerance_mm": configured_tolerance_a,
                "expected_snap_tolerance_mm": PRODUCTION_TOLERANCE_MM,
                "production_config_modified": False,
            },
            "inputs": {
                "source_dxf": {"name": source.name, "sha256": hashes["source"]},
                "historical_walls_snapshot": {
                    "name": walls_path.name,
                    "sha256": hashes["walls"],
                },
                "historical_raw_snapshot": {
                    "name": raw_path.name,
                    "sha256": sha256_file(raw_path),
                },
            },
            "determinism": {
                "run_1_graph_sha256": graph_hash_a,
                "run_2_graph_sha256": graph_hash_b,
                "equal": True,
            },
            "artifacts": {
                name: {
                    "size_bytes": (staging / name).stat().st_size,
                    "sha256": sha256_file(staging / name),
                }
                for name in artifact_names
            },
            "forbidden_downstream_artifacts": {
                name: {"expected_absent": True, "absent": True}
                for name in FORBIDDEN_DOWNSTREAM
            },
        }
        write_json(staging / "manifest.json", manifest)
        staged_names = {path.name for path in staging.iterdir()}
        if staged_names != set(MANAGED_ARTIFACTS):
            raise RuntimeError(
                "Staged artifact set mismatch: "
                f"expected={sorted(MANAGED_ARTIFACTS)}, actual={sorted(staged_names)}"
            )

        output_dir.parent.mkdir(parents=True, exist_ok=True)
        publish_staging = Path(
            tempfile.mkdtemp(
                prefix=f".{output_dir.name}.staging-", dir=output_dir.parent
            )
        )
        backup = output_dir.parent / f".{output_dir.name}.backup-{uuid.uuid4().hex}"
        try:
            for name in MANAGED_ARTIFACTS:
                shutil.copyfile(staging / name, publish_staging / name)
            published_names = {path.name for path in publish_staging.iterdir()}
            if published_names != set(MANAGED_ARTIFACTS):
                raise RuntimeError("Published staging artifact set mismatch")
            for name in MANAGED_ARTIFACTS:
                if sha256_file(staging / name) != sha256_file(publish_staging / name):
                    raise RuntimeError(f"Published staging hash mismatch: {name}")

            had_previous = output_dir.exists()
            if had_previous:
                output_dir.replace(backup)
            try:
                publish_staging.replace(output_dir)
            except Exception:
                if had_previous:
                    backup.replace(output_dir)
                raise
            if had_previous:
                remove_tree_without_following_symlinks(backup)
        finally:
            if publish_staging.exists() or publish_staging.is_symlink():
                remove_tree_without_following_symlinks(publish_staging)

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic TQ-01 topology diagnostics"
    )
    parser.add_argument(
        "--source", type=Path,
        default=Path("datasets/twin_villa/dxf/kaRar.dxf")
    )
    parser.add_argument(
        "--walls", type=Path,
        default=Path("outputs/rv01/twin_villa/run_1_snapshot/walls_clean.json")
    )
    parser.add_argument(
        "--raw", type=Path,
        default=Path("outputs/rv01/twin_villa/run_1_snapshot/dxf_raw.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/tq01/twin_villa")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_diagnostics(args.source, args.walls, args.raw, args.output)
    print(
        json.dumps(
            {"status": manifest["status"], "counts": manifest["counts"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()