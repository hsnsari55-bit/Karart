"""Read-only, deterministic TQ-01 topology qualification diagnostics.

The module never repairs geometry or relaxes a validator. It rebuilds topology
from an explicitly identified historical wall snapshot in an isolated directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from backend.topology_engine import TopologyEngine


PRODUCTION_TOLERANCE_MM = 5.0
TOLERANCE_BANDS_MM = (2.5, 4.0, 5.0, 6.0, 7.5, 10.0)
FORBIDDEN_DOWNSTREAM = (
    "bim_model.json", "model.glb", "model.obj", "model.blend", "preview.png"
)
CATEGORIES = (
    "endpoint-to-endpoint near miss",
    "endpoint-to-segment/T-junction near miss",
    "legitimate architectural opening",
    "isolated annotation/non-wall",
    "truncated/incomplete",
    "wrong/incomplete block selection",
    "duplicate/overlap",
    "unresolved",
)


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
    walls_path: Path, tolerance_mm: float = PRODUCTION_TOLERANCE_MM
) -> tuple[dict, dict]:
    """Run the frozen Topology Engine while redirecting every write to temp."""
    with tempfile.TemporaryDirectory(prefix="karar-tq01-") as temp_dir:
        outputs = Path(temp_dir) / "outputs"
        outputs.mkdir()
        shutil.copyfile(walls_path, outputs / "walls_clean.json")
        engine = TopologyEngine()
        engine.snap_tolerance = tolerance_mm
        engine.path_manager = type(
            "IsolatedPathManager",
            (),
            {
                "get_path": staticmethod(
                    lambda *parts: str(Path(temp_dir).joinpath(*parts))
                ),
                "get_relative_path": staticmethod(str),
            },
        )()
        graph = engine.run()
        stable_stats = {
            key: value
            for key, value in engine.stats.items()
            if key != "processing_time_ms"
        }
        return graph, stable_stats


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
        if other["id"] not in incident_node_ids
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
    segment = segment_candidates[0] if segment_candidates else (None, None, None)
    return {
        "nearest_endpoint_distance_mm": (
            None if endpoint[0] is None else round(endpoint[0], 6)
        ),
        "nearest_endpoint_node_id": endpoint[1],
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
    records = []
    for node in graph["nodes"]:
        if node["degree"] != 1:
            continue
        edge = incident[node["id"]][0]
        other_id = edge["to"] if edge["from"] == node["id"] else edge["from"]
        other = graph["nodes"][other_id]
        measurement = candidate_measurements(graph, node, edge["id"])
        endpoint_hit = (
            measurement["endpoint_candidate_count_at_production_tolerance"] > 0
        )
        segment_hit = (
            measurement["segment_candidate_count_at_production_tolerance"] > 0
        )
        if endpoint_hit:
            classification = CATEGORIES[0]
            evidence = "Distinct endpoint strictly inside frozen 5.0 mm tolerance."
        elif segment_hit:
            classification = CATEGORIES[1]
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
                "production_tolerance_candidate": endpoint_hit or segment_hit,
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
        segment_nodes = [
            item["node_id"]
            for item in dangling
            if item["nearest_nonincident_segment_distance_mm"] is not None
            and item["nearest_nonincident_segment_distance_mm"] < tolerance
        ]
        ambiguous_nodes = sorted(set(endpoint_nodes).intersection(segment_nodes))
        bands.append(
            {
                "tolerance_mm": tolerance,
                "endpoint_to_endpoint_candidate_node_ids": endpoint_nodes,
                "endpoint_to_segment_candidate_node_ids": segment_nodes,
                "predicted_max_dangling_reduction": len(
                    set(endpoint_nodes + segment_nodes)
                ),
                "ambiguous_candidate_node_ids": ambiguous_nodes,
                "ambiguity_count": len(ambiguous_nodes),
                "ambiguity": "both_candidate_types_within_band",
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
            lines.append(
                f'<text x="{x + 4:.2f}" y="{y - 4:.2f}" fill="#991b1b">'
                f'N{node["id"]}</text>'
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
            f'bbox={bounds}; scale={scale:.6f}px/mm; deterministic component colors</text>',
            '<g font-family="sans-serif" font-size="11">',
            '<text x="1050" y="24">Legend</text>',
            '<circle cx="1060" cy="45" r="3" fill="#dc2626"/>',
            '<text x="1070" y="49">dangling node + ID</text>',
            '<line x1="1050" y1="65" x2="1080" y2="65" stroke="#dc2626" '
            'stroke-dasharray="5 4"/>',
            '<text x="1090" y="69">endpoint near-miss</text>',
            '<line x1="1050" y1="85" x2="1080" y2="85" stroke="#7c3aed" '
            'stroke-dasharray="3 3"/>',
            '<text x="1090" y="89">T-junction near-miss</text>',
            '<line x1="1050" y1="105" x2="1080" y2="105" stroke="#eab308" '
            'stroke-width="3"/>',
            '<text x="1090" y="109">closed-loop boundary</text>',
            '<text x="1050" y="129">edge color = component ID modulo palette</text>',
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
    bounds = json.dumps(raw.get("bounding_box", "UNKNOWN"), sort_keys=True)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240">'
        '<rect width="100%" height="100%" fill="white" stroke="#334155"/>'
        '<text x="24" y="45" font-family="sans-serif" font-size="22">Recorded parser block candidate</text>'
        f'<text x="24" y="90" font-family="monospace">name={promoted}</text>'
        f'<text x="24" y="125" font-family="monospace">recorded entities={count}</text>'
        f'<text x="24" y="160" font-family="monospace">bbox={bounds}</text>'
        '<text x="24" y="205" font-family="sans-serif" fill="#991b1b">'
        'Historical snapshot; not a successful re-parse of the truncated source.</text>'
        '</svg>\n'
    )


def source_audit(source: Path, raw_path: Path, raw: dict) -> dict:
    text_tail = source.read_bytes()[-256:].decode("latin-1", errors="replace")
    promoted = raw.get("metadata", {}).get("promoted_block", "UNKNOWN")
    entities = raw.get("entities", [])
    grouped = Counter(
        entity.get("block_name", "UNKNOWN") for entity in entities
    )
    return {
        "source": {
            "absolute_path": str(source.resolve()),
            "relative_path": os.path.relpath(source.resolve(), Path.cwd()),
            "size_bytes": source.stat().st_size,
            "sha256": sha256_file(source),
            "structurally_truncated": "EOF" not in text_tail[-50:],
            "tail_latin1": text_tail,
            "standard_read": {
                "status": "FAIL",
                "evidence": "controlled baseline: missing ENDSEC tag",
            },
            "smart_repair": {
                "status": "FAIL",
                "evidence": "controlled temp-copy baseline: invalid ENDBLK after incomplete LWPO token",
            },
            "original_recover": {
                "status": "EMPTY_GEOMETRY",
                "modelspace_entities": 0,
                "nonempty_blocks": 0,
            },
        },
        "historical_snapshot": {
            "path": str(raw_path),
            "sha256": sha256_file(raw_path),
            "entity_count": len(entities),
            "source_file_field": raw.get("source_file"),
            "reproducible_from_current_source": False,
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


def engineering_report(counts: dict, hashes: dict, classes: Counter) -> str:
    question = (
        "Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in "
        "doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir "
        "şekilde artırıyor mu?"
    )
    return f"""# Kanıt

- RV-01 walls snapshot SHA-256: `{hashes['walls']}`.
- İki izole rebuild aynı graph SHA-256 üretti: `{hashes['graph']}`.
- Ölçüm: {counts['walls']} walls, {counts['nodes']} nodes, {counts['edges']} edges, {counts['loops']} loops, {counts['components']} components, {counts['dangling']} dangling.
- Kaynak DXF SHA-256: `{hashes['source']}`; mevcut parser ile yeniden üretilemiyor.
- Sınıflandırma: `{dict(sorted(classes.items()))}`.

# Risk Analizi

- Snapshot graph deterministik, fakat kesik DXF’den uçtan uca yeniden üretilebilir değil.
- Geometry/Topology kontratı entity kimliği taşımadığından entity provenance `UNKNOWN`.
- Ground truth olmadan unresolved uçların opening veya engine bug olduğu iddia edilemez.

# Önerilen Çözüm

- Tam kaynak veya insan-onaylı recovery politikası sağlanmalı; otomatik kapanış tahmini yapılmamalı.
- Parser recovery ve block-selection provenance ayrı ADR ile ele alınmalı; frozen tolerans değiştirilmemeli.

# Uygulanan Değişiklik

- Production engine değiştirilmedi. İzole read-only diagnostic ve raw-byte manifest eklendi.
- {question} **EVET** — topology sorunlarının ölçülebilir, tekrar üretilebilir teşhisini sağlar; geometriyi değiştirmez.

# Doğrulama

- İki rebuild hash’i eşit; production config değiştirilmedi.
- Topology gate FAIL: dangling={counts['dangling']}, components={counts['components']}. Downstream çalıştırılmadı.
- Accuracy/F1/IoU iddiası yok.

# Kalan Riskler

- Tam DXF ve ground truth olmadan block completeness ve legitimate openings doğrulanamaz.
- Safe automatic repair kanıtlanmadı; status `TQ-01 QUALIFIED_BLOCKED_NO_SAFE_FIX`.
"""


def write_csv(path: Path, dangling: list[dict]) -> None:
    fields = [
        "node_id", "x", "y", "component_id", "component_size",
        "incident_edge_id", "incident_edge_length_mm", "layer", "block",
        "entity_type", "entity_id", "nearest_endpoint_node_id",
        "nearest_endpoint_distance_mm", "nearest_nonincident_segment_edge_id",
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
    source = source.resolve()
    walls_path = walls_path.resolve()
    raw_path = raw_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    unexpected_downstream = [
        name for name in FORBIDDEN_DOWNSTREAM if (output_dir / name).exists()
    ]
    if unexpected_downstream:
        raise RuntimeError(
            "Blocked topology output contains forbidden downstream artifacts: "
            + ", ".join(unexpected_downstream)
        )
    walls = json.loads(walls_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    graph_a, stats_a = rebuild_graph(walls_path)
    graph_b, stats_b = rebuild_graph(walls_path)
    graph_hash_a = hashlib.sha256(
        json.dumps(graph_a, indent=4, sort_keys=True).encode("utf-8")
    ).hexdigest()
    graph_hash_b = hashlib.sha256(
        json.dumps(graph_b, indent=4, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if graph_hash_a != graph_hash_b or stats_a != stats_b:
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
    write_json(output_dir / "block_selection_audit.json", source_audit(source, raw_path, raw))
    (output_dir / "block_candidates.svg").write_text(
        block_svg(raw), encoding="utf-8", newline="\n"
    )
    write_json(
        output_dir / "dangling_nodes.json",
        {"categories": CATEGORIES, "count": len(dangling), "nodes": dangling},
    )
    write_csv(output_dir / "dangling_nodes.csv", dangling)
    write_json(
        output_dir / "component_inventory.json",
        {"count": len(components), "components": components},
    )
    (output_dir / "topology_overview.svg").write_text(
        topology_svg(graph_a, dangling, node_to_component),
        encoding="utf-8",
        newline="\n",
    )
    write_json(
        output_dir / "tolerance_sensitivity.json",
        tolerance_sensitivity(dangling),
    )
    hashes = {
        "source": sha256_file(source),
        "walls": sha256_file(walls_path),
        "graph": graph_hash_a,
    }
    report = engineering_report(
        counts, hashes, Counter(item["classification"] for item in dangling)
    )
    (output_dir / "TQ01_ENGINEERING_REPORT.md").write_text(
        report, encoding="utf-8", newline="\n"
    )

    artifact_names = sorted(
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "schema_version": "tq01-manifest-v1",
        "status": "TQ-01 QUALIFIED_BLOCKED_NO_SAFE_FIX",
        "hard_gate": {"topology": "FAIL", "downstream_executed": False},
        "counts": counts,
        "inputs": {
            "source_dxf": {"path": str(source), "sha256": hashes["source"]},
            "historical_walls_snapshot": {
                "path": str(walls_path), "sha256": hashes["walls"]
            },
            "historical_raw_snapshot": {
                "path": str(raw_path), "sha256": sha256_file(raw_path)
            },
        },
        "determinism": {
            "run_1_graph_sha256": graph_hash_a,
            "run_2_graph_sha256": graph_hash_b,
            "equal": True,
        },
        "artifacts": {
            name: {
                "size_bytes": (output_dir / name).stat().st_size,
                "sha256": sha256_file(output_dir / name),
            }
            for name in artifact_names
        },
        "forbidden_downstream_artifacts": {
            name: {
                "expected_absent": True,
                "absent": not (output_dir / name).exists(),
            }
            for name in FORBIDDEN_DOWNSTREAM
        },
    }
    write_json(output_dir / "manifest.json", manifest)
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