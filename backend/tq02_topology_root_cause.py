"""TQ-02 exact-source, read-only topology root-cause qualification.

Only Parser -> Geometry -> Topology -> Constraint -> Validator is executed.  The
module deliberately does not import any downstream consumer.  All production
inputs are copied to an isolated workspace and production configuration remains
unchanged; tolerance runs are explicitly labelled topology-only ablations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import tempfile
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import ezdxf

from backend.constraint_solver import ConstraintSolver
from backend.dxf_parser import DXFParser
from backend.geometry_engine import GeometryEngine
from backend.topology_engine import TopologyEngine
from backend.tq01_topology_diagnostics import (
    candidate_measurements,
    component_inventory,
    isolated_path_manager,
    remove_tree_without_following_symlinks,
    sha256_file,
    svg_transform,
    topology_svg,
    validate_topology_graph,
    wall_provenance,
    write_json,
)


EXPECTED_SOURCE_SHA256 = "289b586570f0d915cae1707ccb234b84bd0527bd1412189b5b238811aa9a721c"
EXPECTED_GEOMETRY_SHA256 = "d3153dc7f613c5d58e4bbda82fb2c3056f01c806eb76a7d696e24e89568bf9c3"
EXPECTED_TOPOLOGY_SHA256 = "3f09f1892886a43f94c17cc325142b8b6c2918a11fa7804ebc84fde3e7187aba"
EXPECTED_GRAPH_CORE_SHA256 = "836256393b529d0ef27a48750adbe9dc0308f2caed138e1e3080cb2dc37cf6ac"
PRODUCTION_TOLERANCE_MM = 5.0
TOLERANCE_BANDS_MM = (2.5, 4.0, 5.0, 6.0, 7.5, 10.0)
EXPECTED_COUNTS = {
    "modelspace_entities": 13665,
    "parser_entities": 39202,
    "walls": 2088,
    "nodes": 2782,
    "edges": 2602,
    "loops": 298,
    "components": 478,
    "dangling": 1090,
    "tiny_loops": 3,
}
FORBIDDEN_DOWNSTREAM = (
    "bim_model.json", "bim_semantics.json", "model.glb", "model.obj",
    "model.blend", "model.ifc", "preview.png",
)
MANAGED_ARTIFACTS = (
    "TQ02_ENGINEERING_REPORT.md",
    "baseline_comparison.json",
    "component_inventory.json",
    "component_layer_matrix.csv",
    "dangling_candidates.svg",
    "dangling_nodes.csv",
    "dangling_nodes.json",
    "evidence_matrix.json",
    "ground_truth_review.csv",
    "largest_component.svg",
    "manifest.json",
    "provenance_inventory.json",
    "root_cause_summary.json",
    "selection_experiments.json",
    "tolerance_sensitivity.json",
    "topology_overview.svg",
)


def stable_hash(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        payload = json.dumps(value, indent=4, sort_keys=True).encode("utf-8")
    else:
        payload = json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":")
        ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def graph_core(graph: dict) -> dict:
    return {key: graph.get(key, []) for key in ("nodes", "edges", "loops")}


def compare_constraint_graphs(before: dict, after: dict) -> dict:
    before_core, after_core = graph_core(before), graph_core(after)
    return {
        "initial_edge_count": len(before_core["edges"]),
        "resolved_edge_count": len(after_core["edges"]),
        "graph_core_equal": before_core == after_core,
        "pre_core_sha256": stable_hash(before_core),
        "post_core_sha256": stable_hash(after_core),
        "contribution": (
            "none_observed" if before_core == after_core else "graph_changed"
        ),
    }


def validate_output_dir(output_dir: Path) -> Path:
    lexical = Path(output_dir).absolute()
    for candidate in (lexical, *lexical.parents):
        if candidate.is_symlink():
            raise ValueError(f"Unsafe TQ-02 output symlink: {candidate}")
    resolved = lexical.resolve()
    repo_root = Path(__file__).resolve().parents[1]
    if resolved in {Path(resolved.anchor), repo_root, Path.cwd().resolve(), Path.home().resolve()}:
        raise ValueError(f"Unsafe broad TQ-02 output target: {resolved}")
    parts = [part.lower() for part in resolved.parts]
    if "tq02" not in parts[:-1] and resolved.name.lower() != "tq02":
        raise ValueError(f"Output must be inside a dedicated TQ-02 directory: {resolved}")
    return resolved


def _stable_stats(stats: dict) -> dict:
    return {key: value for key, value in stats.items() if key != "processing_time_ms"}


def _run_topology(walls: list[dict], tolerance: float) -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="karar-tq02-topology-") as temp_dir:
        root = Path(temp_dir)
        (root / "outputs").mkdir()
        write_json(root / "outputs" / "walls_clean.json", walls)
        engine = TopologyEngine()
        engine.path_manager = isolated_path_manager(root)
        engine.snap_tolerance = float(tolerance)
        graph = engine.run()
        return graph, _stable_stats(engine.stats)


def run_exact_pipeline(source: Path) -> dict:
    """Run the permitted core stages in a fresh workspace from an immutable copy."""
    source = source.resolve()
    source_hash = sha256_file(source)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"source-hash-drift: expected={EXPECTED_SOURCE_SHA256}, actual={source_hash}"
        )
    with tempfile.TemporaryDirectory(prefix="karar-tq02-pipeline-") as temp_dir:
        root = Path(temp_dir)
        (root / "outputs").mkdir()
        copied_source = root / "proje.dxf"
        shutil.copyfile(source, copied_source)
        copy_hash_before = sha256_file(copied_source)

        doc = ezdxf.readfile(copied_source)
        auditor = doc.audit()
        intake = {
            "dxfversion": doc.dxfversion,
            "insunits": int(doc.header.get("$INSUNITS", 0)),
            "audit_errors": len(auditor.errors),
            "audit_fixes": len(auditor.fixes),
            "modelspace_entities": sum(1 for _ in doc.modelspace()),
        }
        path_manager = isolated_path_manager(root)
        parser = DXFParser()
        parser.path_manager = path_manager
        raw = parser.parse(str(copied_source))
        geometry = GeometryEngine()
        geometry.path_manager = path_manager
        configured_tolerance = float(geometry.snap_tolerance)
        if configured_tolerance != PRODUCTION_TOLERANCE_MM:
            raise RuntimeError(f"configuration-drift: {configured_tolerance}")
        walls = geometry.run()
        topology = TopologyEngine()
        topology.path_manager = path_manager
        if float(topology.snap_tolerance) != PRODUCTION_TOLERANCE_MM:
            raise RuntimeError(f"configuration-drift: {topology.snap_tolerance}")
        graph = topology.run()
        solver = ConstraintSolver()
        solver.path_manager = path_manager
        resolved = solver.run(graph)

        components, node_to_component = component_inventory(graph)
        dangling = build_dangling_inventory(graph, walls, node_to_component)
        tiny_loop_ids = sorted(
            loop.get("id") for loop in graph.get("loops", [])
            if float(loop.get("area", 0.0)) < 1.0
        )
        result = {
            "source": {
                "name": source.name,
                "sha256": source_hash,
                "copy_sha256_before": copy_hash_before,
                "copy_sha256_after": sha256_file(copied_source),
                "original_sha256_after": sha256_file(source),
            },
            "intake": intake,
            "parser": {
                "entity_count": len(raw.get("entities", [])),
                "promoted_block": raw.get("metadata", {}).get("promoted_block"),
                "promotion_reason": raw.get("metadata", {}).get("promotion_reason"),
                "skipped_entities": raw.get("metadata", {}).get("skipped_entities", 0),
            },
            "configuration": {
                "production_tolerance_mm": configured_tolerance,
                "production_config_modified": False,
            },
            "geometry": {
                "hash": geometry.stats["geometry_sha256"],
                "stats": _stable_stats(geometry.stats),
                "walls_compact_sha256": stable_hash(walls),
            },
            "topology": {
                "hash": topology.stats["topology_sha256"],
                "stats": _stable_stats(topology.stats),
            },
            "counts": {
                "modelspace_entities": intake["modelspace_entities"],
                "parser_entities": len(raw.get("entities", [])),
                "walls": len(walls), "nodes": len(graph["nodes"]),
                "edges": len(graph["edges"]), "loops": len(graph["loops"]),
                "components": len(components), "dangling": len(dangling),
                "tiny_loops": len(tiny_loop_ids),
            },
            "tiny_loop_ids": tiny_loop_ids,
            "constraint": compare_constraint_graphs(graph, resolved),
            "validator": validate_topology_graph(resolved),
            "downstream_instantiated": False,
            "raw": raw,
            "walls": walls,
            "graph": graph,
            "components": components,
            "node_to_component": node_to_component,
            "dangling": dangling,
        }
        return result


def build_dangling_inventory(
    graph: dict, walls: list[dict], node_to_component: dict[int, int]
) -> list[dict]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    incident: dict[int, list[dict]] = defaultdict(list)
    for edge in graph["edges"]:
        incident[edge["from"]].append(edge)
        incident[edge["to"]].append(edge)
    records = []
    for node in sorted(graph["nodes"], key=lambda item: item["id"]):
        if node.get("degree") != 1:
            continue
        edge = incident[node["id"]][0]
        other_id = edge["to"] if edge["from"] == node["id"] else edge["from"]
        other = nodes[other_id]
        measurements = candidate_measurements(graph, node, edge["id"])
        hits = [
            label for label, key in (
                ("endpoint_to_endpoint", "endpoint_candidate_count_at_production_tolerance"),
                ("endpoint_to_junction", "junction_candidate_count_at_production_tolerance"),
                ("endpoint_to_segment", "segment_candidate_count_at_production_tolerance"),
            ) if measurements[key] > 0
        ]
        provenance = wall_provenance(
            (node["x"], node["y"]), (other["x"], other["y"]), walls
        )
        known = provenance["layer"] != "UNKNOWN"
        records.append({
            "node_id": node["id"], "x": node["x"], "y": node["y"],
            "component_id": node_to_component[node["id"]],
            "incident_edge_id": edge["id"],
            "incident_edge_length_mm": edge.get("length"),
            "provenance": {
                **provenance,
                "method": "geometric_incident-segment_match",
                "confidence": "inferred_unique_tuple" if known else "ambiguous_or_unavailable",
                "exact_entity_lineage": False,
            },
            **measurements,
            "candidate_types": hits,
            "classification": (
                "candidate_" + hits[0] if len(hits) == 1
                else "ambiguous_multiple_candidates" if hits
                else "unresolved_no_candidate_within_5mm"
            ),
            "evidence_level": "B" if len(hits) == 1 else "C" if hits else "D",
        })
    return records


def selection_experiments(raw: dict, walls: list[dict], dangling: list[dict]) -> dict:
    raw_layers = Counter(entity.get("layer", "UNKNOWN") for entity in raw.get("entities", []))
    raw_blocks = Counter(entity.get("block_name", "UNKNOWN") for entity in raw.get("entities", []))
    raw_types = Counter(entity.get("type", "UNKNOWN") for entity in raw.get("entities", []))
    wall_layers = Counter(wall.get("layer", "UNKNOWN") for wall in walls)
    wall_blocks = Counter(wall.get("block_name", "UNKNOWN") for wall in walls)
    return {
        "artifact_contract": "selection_inventory_v1",
        "method": "deterministic source and selected-wall inventory; no source mutation",
        "modelspace_policy": "modelspace_nonempty_so_block_promotion_not_executed",
        "raw_layer_counts": dict(sorted(raw_layers.items())),
        "raw_block_counts": dict(sorted(raw_blocks.items())),
        "raw_entity_type_counts": dict(sorted(raw_types.items())),
        "selected_wall_layer_counts": dict(sorted(wall_layers.items())),
        "selected_wall_block_counts": dict(sorted(wall_blocks.items())),
        "selection_counterfactual_status": "not_applied_without_ground_truth",
        "claim_boundary": "inventories identify concentration, not architectural correctness",
    }


def provenance_inventory(dangling: list[dict]) -> dict:
    confidence = Counter(item["provenance"].get("confidence", "UNKNOWN") for item in dangling)
    layers = Counter(item["provenance"].get("layer", "UNKNOWN") for item in dangling)
    blocks = Counter(item["provenance"].get("block", "UNKNOWN") for item in dangling)
    methods = Counter(item["provenance"].get("method", "UNKNOWN") for item in dangling)
    exact_lineage = Counter(
        str(item["provenance"].get("exact_entity_lineage", False)).lower()
        for item in dangling
    )
    return {
        "artifact_contract": "dangling_provenance_summary_v1",
        "method": "deterministic graph-to-wall geometric attribution",
        "record_count": len(dangling),
        "confidence_counts": dict(sorted(confidence.items())),
        "attributed_layer_counts": dict(sorted(layers.items())),
        "attributed_block_counts": dict(sorted(blocks.items())),
        "attribution_method_counts": dict(sorted(methods.items())),
        "exact_entity_lineage_counts": dict(sorted(exact_lineage.items())),
        "exact_entity_lineage_available": False,
        "claim_boundary": "geometric attribution is candidate provenance, not exact DXF entity lineage or causal proof",
    }


def tolerance_experiments(walls: list[dict]) -> dict:
    bands = []
    for tolerance in TOLERANCE_BANDS_MM:
        graph_a, stats_a = _run_topology(walls, tolerance)
        graph_b, stats_b = _run_topology(walls, tolerance)
        components, _ = component_inventory(graph_a)
        graph_hash_a, graph_hash_b = stable_hash(graph_a, pretty=True), stable_hash(graph_b, pretty=True)
        bands.append({
            "tolerance_mm": tolerance,
            "nodes": len(graph_a["nodes"]), "edges": len(graph_a["edges"]),
            "loops": len(graph_a["loops"]), "components": len(components),
            "dangling": sum(node.get("degree") == 1 for node in graph_a["nodes"]),
            "topology_sha256": graph_hash_a,
            "repeat_sha256": graph_hash_b,
            "deterministic": graph_hash_a == graph_hash_b and stats_a == stats_b,
        })
    return {
        "method": "topology-only ablation over identical production-5mm Geometry output",
        "production_tolerance_mm": PRODUCTION_TOLERANCE_MM,
        "production_config_modified": False,
        "accuracy_claim": "none_without_ground_truth",
        "false_link_risk": "unquantified_without_architectural_ground_truth",
        "bands": bands,
    }


def _comparable_run_evidence(run: dict) -> dict:
    keys = (
        "source", "intake", "parser", "configuration", "geometry", "topology",
        "counts", "tiny_loop_ids", "constraint", "validator", "downstream_instantiated",
    )
    return {key: run.get(key) for key in keys}


def evaluate_core_fix_gate(
    run: dict | None = None,
    repeat_run: dict | None = None,
    independent_reproducer: dict | None = None,
) -> dict:
    """Evaluate measured evidence; caller-provided claims never authorize a core edit.

    TQ-02 has no internal independent-reproducer executor.  Consequently an external
    mapping, even if it contains hashes or verifier-looking labels, is untrusted input
    and the reproducer-dependent checks remain fail-closed.
    """
    run = run or {}
    source = run.get("source", {})
    constraint = run.get("constraint", {})
    validator = run.get("validator", {})
    baseline_matches = bool(run) and all((
        run.get("counts") == EXPECTED_COUNTS,
        run.get("geometry", {}).get("hash") == EXPECTED_GEOMETRY_SHA256,
        run.get("topology", {}).get("hash") == EXPECTED_TOPOLOGY_SHA256,
        constraint.get("pre_core_sha256") == EXPECTED_GRAPH_CORE_SHA256,
    ))
    source_matches = bool(run) and all((
        source.get("sha256") == EXPECTED_SOURCE_SHA256,
        source.get("copy_sha256_before") == EXPECTED_SOURCE_SHA256,
        source.get("copy_sha256_after") == EXPECTED_SOURCE_SHA256,
        source.get("original_sha256_after") == EXPECTED_SOURCE_SHA256,
    ))
    deterministic = bool(run and repeat_run) and (
        _comparable_run_evidence(run) == _comparable_run_evidence(repeat_run)
    )
    validator_failed = validator.get("topology") == "FAIL"
    constraint_excluded = (
        constraint.get("graph_core_equal") is True
        and constraint.get("contribution") == "none_observed"
    )
    reproducer_submitted = independent_reproducer is not None
    reproducer_evidence_status = (
        "UNTRUSTED_CALLER_INPUT_INTERNAL_VERIFIER_NOT_IMPLEMENTED"
        if reproducer_submitted
        else "NOT_PROVIDED_INTERNAL_VERIFIER_NOT_IMPLEMENTED"
    )
    verified_payload = False
    defect_isolated = False
    minimal_exists = False
    permutation_invariant = False
    translation_invariant = False
    mathematical_expected = False
    checks = [
        ("exact_authoritative_source", source_matches),
        ("baseline_matches_locked_values", baseline_matches),
        ("two_independent_runs_deterministic", deterministic),
        ("validator_failure_reproduced", validator_failed),
        ("constraint_contribution_excluded", constraint_excluded),
        ("defect_isolated_to_topology_engine", defect_isolated),
        ("minimal_reproducer_exists", minimal_exists),
        ("permutation_invariant_reproducer", permutation_invariant),
        ("translation_invariant_reproducer", translation_invariant),
        ("mathematical_expected_result_unambiguous", mathematical_expected),
    ]
    passed = all(value for _, value in checks)
    return {
        "checks": [{"name": name, "passed": value} for name, value in checks],
        "passed": passed,
        "decision": "CORE_FIX_PERMITTED" if passed else "NO_CORE_FIX_INSUFFICIENT_PROOF",
        "frozen_core_edited": False,
        "independent_reproducer_evidence_verified": verified_payload,
        "independent_reproducer_evidence_status": reproducer_evidence_status,
        "caller_assertions_ignored": reproducer_submitted,
    }


def evidence_matrix(run: dict, gate: dict) -> list[dict]:
    counts = run["counts"]
    return [
        {"hypothesis": "source/modelspace content", "level": "A", "result": "observed_input_candidate_contributor",
         "evidence": f"{counts['modelspace_entities']} modelspace entities and {counts['components']} components observed; observation does not prove causality"},
        {"hypothesis": "parser/block/layer selection", "level": "B", "result": "candidate_contributor",
         "evidence": "modelspace selected; no block promotion; graph lacks exact entity lineage"},
        {"hypothesis": "geometry classification/filtering", "level": "B", "result": "candidate_contributor",
         "evidence": f"actual run produced {counts['walls']} walls; filtering/snapping/merge are measured"},
        {"hypothesis": "topology engine defect", "level": "D", "result": "not_proven",
         "evidence": "no independent minimal mathematical reproducer"},
        {"hypothesis": "constraint solver", "level": "A+", "result": "excluded_for_observed_graph",
         "evidence": f"pre/post graph core equal={run['constraint']['graph_core_equal']}"},
        {"hypothesis": "validator invariant mismatch", "level": "D", "result": "NOT_EVALUATED_INSUFFICIENT_GROUND_TRUTH",
         "evidence": "validator reports measured dangling/open graph; architectural ground truth is unavailable"},
        {"hypothesis": "overall", "level": "B", "result": "mixed_source_selection_geometry_insufficient_intent",
         "evidence": gate["decision"]},
    ]


def _spatial_svg(
    graph: dict,
    dangling: list[dict],
    title: str,
    component_node_ids: set[int] | None = None,
) -> str:
    nodes = {node["id"]: node for node in graph["nodes"]}
    dangling_by_id = {item["node_id"]: item for item in dangling}
    visible_nodes = set(nodes) if component_node_ids is None else set(component_node_ids)
    view_graph = {
        "nodes": [node for node in graph["nodes"] if node["id"] in visible_nodes],
        "edges": [
            edge for edge in graph["edges"]
            if edge["from"] in visible_nodes and edge["to"] in visible_nodes
        ],
        "loops": [],
    }
    if not view_graph["nodes"]:
        raise ValueError("Spatial SVG requires at least one visible graph node")
    transform, _, _ = svg_transform(view_graph, width=1400, height=900)
    rows = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="20" y="30" font-family="sans-serif" font-size="18">{html.escape(title)}</text>',
        '<g stroke="#94a3b8" stroke-width="1" fill="none">',
    ]
    for edge in graph["edges"]:
        if edge["from"] not in visible_nodes or edge["to"] not in visible_nodes:
            continue
        start, end = nodes[edge["from"]], nodes[edge["to"]]
        x1, y1 = transform(start["x"], start["y"])
        x2, y2 = transform(end["x"], end["y"])
        rows.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    rows.append('</g><g stroke="#991b1b" stroke-width="1" fill="#dc2626">')
    for node_id, item in sorted(dangling_by_id.items()):
        if node_id not in visible_nodes:
            continue
        node = nodes[node_id]
        x, y = transform(node["x"], node["y"])
        color = {"B": "#16a34a", "C": "#ea580c", "D": "#dc2626"}[item["evidence_level"]]
        rows.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" fill="{color}"><title>N{node_id} {html.escape(item["classification"])}</title></circle>')
    rows.append('</g><text x="20" y="880" font-family="sans-serif" font-size="12">Green=B candidate, orange=C ambiguous, red=D unresolved; geometry is spatial, not a text table.</text></svg>\n')
    return "".join(rows)


def candidate_svg(graph: dict, dangling: list[dict]) -> str:
    return _spatial_svg(graph, dangling, "TQ-02 spatial dangling candidate evidence")


def component_investigation(run: dict) -> list[dict]:
    graph, dangling = run["graph"], run["dangling"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = {edge["id"]: edge for edge in graph["edges"]}
    dangling_by_component: dict[int, list[dict]] = defaultdict(list)
    for item in dangling:
        dangling_by_component[item["component_id"]].append(item)
    records = []
    all_points = [(node["id"], node["x"], node["y"]) for node in graph["nodes"]]
    for base in run["components"]:
        node_ids, edge_ids = base["node_ids"], base["edge_ids"]
        points = [(nodes[node_id]["x"], nodes[node_id]["y"]) for node_id in node_ids]
        canonical_nodes = sorted((round(x, 6), round(y, 6)) for x, y in points)
        canonical_edges = sorted(
            tuple(sorted(((round(nodes[edges[eid]["from"]]["x"], 6), round(nodes[edges[eid]["from"]]["y"], 6)),
                          (round(nodes[edges[eid]["to"]]["x"], 6), round(nodes[edges[eid]["to"]]["y"], 6)))))
            for eid in edge_ids
        )
        signature = stable_hash({"nodes": canonical_nodes, "edges": canonical_edges})
        member = set(node_ids)
        outside_points = [
            (x, y) for node_id, x, y in all_points if node_id not in member
        ]
        nearest = min(
            (round(((inside_x - outside_x) ** 2 + (inside_y - outside_y) ** 2) ** 0.5, 6)
             for inside_x, inside_y in points
             for outside_x, outside_y in outside_points),
            default=None,
        )
        edge_id_set = set(edge_ids)
        loops = [
            loop for loop in graph.get("loops", [])
            if set(loop.get("edges", [])).issubset(edge_id_set)
        ]
        provenance = [item["provenance"] for item in dangling_by_component[base["component_id"]]]
        provenance_tuples = Counter(
            (
                item.get("layer", "UNKNOWN"),
                item.get("block", "UNKNOWN"),
                item.get("entity_type", "UNKNOWN"),
            )
            for item in provenance
        )
        records.append({
            **base, "stable_id": f"cmp-{signature[:16]}", "structural_sha256": signature,
            "bbox": {"min_x": min(x for x, _ in points), "min_y": min(y for _, y in points), "max_x": max(x for x, _ in points), "max_y": max(y for _, y in points)},
            "centroid": {"x": round(sum(x for x, _ in points) / len(points), 6), "y": round(sum(y for _, y in points) / len(points), 6)},
            "total_edge_length_mm": round(sum(float(edges[eid].get("length", 0.0)) for eid in edge_ids), 6),
            "degree_histogram": dict(sorted(Counter(str(nodes[node_id].get("degree", 0)) for node_id in node_ids).items())),
            "loop_count": len(loops), "tiny_loop_count": sum(float(loop.get("area", 0.0)) < 1.0 for loop in loops),
            "sliver_loop_count": sum(float(loop.get("area", 0.0)) < 10.0 for loop in loops),
            "nearest_component_node_distance_mm": nearest,
            "provenance_layer_counts": dict(sorted(Counter(item.get("layer", "UNKNOWN") for item in provenance).items())),
            "provenance_block_counts": dict(sorted(Counter(item.get("block", "UNKNOWN") for item in provenance).items())),
            "provenance_tuple_counts": [
                {"layer": layer, "block": block, "entity_type": entity_type, "count": count}
                for (layer, block, entity_type), count in sorted(provenance_tuples.items())
            ],
        })
    return sorted(records, key=lambda item: item["stable_id"])


def layer_ablation(walls: list[dict]) -> dict:
    layers = sorted({wall.get("layer", "UNKNOWN") for wall in walls})
    runs = []
    for label, selected in [("combined_production_baseline", walls)] + [
        (f"isolated_layer:{layer}", [wall for wall in walls if wall.get("layer", "UNKNOWN") == layer])
        for layer in layers
    ]:
        graph, _ = _run_topology(selected, PRODUCTION_TOLERANCE_MM)
        components, _ = component_inventory(graph)
        runs.append({"selection": label, "wall_count": len(selected), "nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "loops": len(graph["loops"]), "components": len(components), "dangling": sum(node.get("degree") == 1 for node in graph["nodes"]), "graph_sha256": stable_hash(graph, pretty=True)})
    return {"method": "isolated selected-wall-layer topology ablation plus combined production baseline", "production_config_modified": False, "accuracy_claim": "none_without_ground_truth", "runs": runs}


PRIORITY_ANSWER = "HAYIR — Bu değişiklik core algoritma davranışını değiştirmez; yalnız kanıt sözleşmesini ve insan inceleme paketini düzeltir."


def engineering_report(run: dict, matrix: list[dict], gate: dict) -> str:
    counts = run["counts"]
    checks = {item["name"]: item["passed"] for item in gate["checks"]}
    repeat_result = (
        "eşleşti" if checks["two_independent_runs_deterministic"]
        else "NOT_EVALUATED_OR_MISMATCH"
    )
    return f"""## 1. Kanıt

- Yetkili DXF SHA-256: `{run['source']['sha256']}`; AC1027, INSUNITS={run['intake']['insunits']}, audit errors/fixes={run['intake']['audit_errors']}/{run['intake']['audit_fixes']}.
- İki exact-source koşu karşılaştırması: `{repeat_result}`; production geometry `{run['geometry']['hash']}`, topology `{run['topology']['hash']}`.
- Ölçüm: {counts['nodes']} nodes, {counts['edges']} edges, {counts['loops']} loops, {counts['components']} components, {counts['dangling']} dangling, {counts['tiny_loops']} tiny loops.
- Evidence matrix sonucu: `{matrix[-1]['result']}`.

## 2. Risk Analizi

- Graph kontratı DXF entity kimliğini taşımadığı için provenance geometrik ve kanıt-sınırlıdır; exact entity lineage iddia edilmez.
- Ground truth olmadan opening, gereksiz çizgi ve yanlış duvar seçimi birbirinden kesin ayrıştırılamaz.
- Tolerance ablation bağlantı sayısını ölçer fakat mimari doğruluk veya false-link oranını kanıtlamaz.

## 3. Önerilen Çözüm

- İnsan-onaylı layer/entity ground truth ve bağımsız minimal reproducer sağlanmadan frozen core değiştirilmemeli.
- Provenance kontratı gelecekte Parser→Geometry→Topology boyunca açık kimlik eşlemesiyle ayrı ADR kapsamında ele alınmalı.

## 4. Uygulanan Değişiklik

- Production core değiştirilmedi; exact-source izole diagnostics, attribution envanteri ve atomik local artifact publisher eklendi.
- “Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir şekilde artırıyor mu?” **{PRIORITY_ANSWER}**

## 5. Doğrulama

- Constraint pre/post core equal=`{run['constraint']['graph_core_equal']}`; validator=`{run['validator']['topology']}`; downstream çalıştırılmadı.
- Conditional core-fix gate: `{gate['decision']}`; frozen_core_edited=`{gate['frozen_core_edited']}`.
- Production config değiştirilmedi; accuracy/F1/IoU iddiası yok.

## 6. Kalan Riskler

- Baskın sınıflandırma `mixed_source_selection_geometry_insufficient_intent`; Topology Engine defect kanıtlanmış değildir.
- Coordinate-bearing artifacts yalnız ignored `outputs/tq02/proje` altında tutulur; rollback atomik önceki paket geri yüklemesidir.
"""


def _write_csv(path: Path, dangling: list[dict]) -> None:
    fields = (
        "node_id", "x", "y", "component_id", "incident_edge_id",
        "nearest_endpoint_distance_mm", "nearest_junction_distance_mm",
        "nearest_nonincident_segment_distance_mm", "classification", "evidence_level",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in dangling:
            writer.writerow({key: item.get(key) for key in fields})


def _write_component_matrix(path: Path, components: list[dict]) -> None:
    fields = ("stable_id", "component_id", "node_count", "edge_count", "loop_count", "dangling_count", "layer", "block", "entity_type", "attributed_count")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for component in components:
            tuples = component["provenance_tuple_counts"] or [
                {"layer": "UNKNOWN", "block": "UNKNOWN", "entity_type": "UNKNOWN", "count": 0}
            ]
            for provenance_tuple in tuples:
                writer.writerow({
                    "stable_id": component["stable_id"],
                    "component_id": component["component_id"],
                    "node_count": component["node_count"],
                    "edge_count": component["edge_count"],
                    "loop_count": component["loop_count"],
                    "dangling_count": len(component["dangling_node_ids"]),
                    "layer": provenance_tuple["layer"],
                    "block": provenance_tuple["block"],
                    "entity_type": provenance_tuple["entity_type"],
                    "attributed_count": provenance_tuple["count"],
                })


def _write_ground_truth_review(path: Path, dangling: list[dict]) -> None:
    fields = ("node_id", "component_id", "x", "y", "classification", "layer", "block", "entity_type", "review_label", "reviewer", "review_notes")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in dangling:
            provenance = item["provenance"]
            writer.writerow({**{key: item.get(key, "") for key in fields}, "layer": provenance.get("layer", "UNKNOWN"), "block": provenance.get("block", "UNKNOWN"), "entity_type": provenance.get("entity_type", "UNKNOWN")})


def publish_package(
    run: dict,
    output_dir: Path,
    tolerance: dict | None = None,
    repeat_run: dict | None = None,
    layer_ablation_result: dict | None = None,
) -> dict:
    output_dir = validate_output_dir(output_dir)
    gate = evaluate_core_fix_gate(run, repeat_run)
    matrix = evidence_matrix(run, gate)
    tolerance = tolerance or {"status": "NOT_EXECUTED_IN_SYNTHETIC_PACKAGE"}
    classifications = Counter(item["classification"] for item in run["dangling"])
    baseline = {
        "expected_counts": EXPECTED_COUNTS,
        "actual_counts": run["counts"],
        "counts_equal": run["counts"] == EXPECTED_COUNTS,
        "expected_geometry_sha256": EXPECTED_GEOMETRY_SHA256,
        "actual_geometry_sha256": run["geometry"]["hash"],
        "expected_topology_sha256": EXPECTED_TOPOLOGY_SHA256,
        "actual_topology_sha256": run["topology"]["hash"],
        "expected_graph_core_sha256": EXPECTED_GRAPH_CORE_SHA256,
        "actual_graph_core_sha256": run["constraint"]["pre_core_sha256"],
    }
    baseline["locked_baseline_equal"] = all((
        baseline["counts_equal"],
        baseline["actual_geometry_sha256"] == baseline["expected_geometry_sha256"],
        baseline["actual_topology_sha256"] == baseline["expected_topology_sha256"],
        baseline["actual_graph_core_sha256"] == baseline["expected_graph_core_sha256"],
    ))
    root_cause = {
        "classification": "mixed_source_selection_geometry_insufficient_intent",
        "topology_defect_proven": False,
        "constraint_contribution": run["constraint"]["contribution"],
        "validator_invariant_mismatch": "NOT_EVALUATED_INSUFFICIENT_GROUND_TRUTH",
        "classification_counts": dict(sorted(classifications.items())),
        "conditional_core_fix_gate": gate,
    }
    with tempfile.TemporaryDirectory(prefix="karar-tq02-package-") as temp_dir:
        staging = Path(temp_dir)
        investigated_components = component_investigation(run)
        write_json(staging / "baseline_comparison.json", baseline)
        write_json(staging / "component_inventory.json", {"count": len(investigated_components), "components": investigated_components})
        _write_component_matrix(staging / "component_layer_matrix.csv", investigated_components)
        write_json(staging / "dangling_nodes.json", {"count": len(run["dangling"]), "nodes": run["dangling"]})
        _write_csv(staging / "dangling_nodes.csv", run["dangling"])
        write_json(staging / "provenance_inventory.json", provenance_inventory(run["dangling"]))
        selection = selection_experiments(run["raw"], run["walls"], run["dangling"])
        selection["layer_topology_ablation"] = layer_ablation_result or {
            "status": "NOT_EXECUTED_IN_SYNTHETIC_PACKAGE"
        }
        write_json(staging / "selection_experiments.json", selection)
        write_json(staging / "tolerance_sensitivity.json", tolerance)
        write_json(staging / "evidence_matrix.json", {"matrix": matrix})
        write_json(staging / "root_cause_summary.json", root_cause)
        (staging / "topology_overview.svg").write_text(
            topology_svg(run["graph"], run["dangling"], run["node_to_component"]), encoding="utf-8", newline="\n"
        )
        (staging / "dangling_candidates.svg").write_text(candidate_svg(run["graph"], run["dangling"]), encoding="utf-8", newline="\n")
        largest = max(
            investigated_components,
            key=lambda item: (item["node_count"], item["edge_count"], item["stable_id"]),
        )
        (staging / "largest_component.svg").write_text(
            _spatial_svg(
                run["graph"], run["dangling"], "TQ-02 largest component",
                set(largest["node_ids"]),
            ),
            encoding="utf-8",
            newline="\n",
        )
        _write_ground_truth_review(staging / "ground_truth_review.csv", run["dangling"])
        (staging / "TQ02_ENGINEERING_REPORT.md").write_text(engineering_report(run, matrix, gate), encoding="utf-8", newline="\n")
        names = sorted(set(MANAGED_ARTIFACTS) - {"manifest.json"})
        manifest = {
            "schema_version": "tq02-manifest-v2",
            "status": "TQ02_AWAITING_HUMAN_GROUND_TRUTH",
            "source": run["source"], "counts": run["counts"],
            "baseline_locked": baseline["locked_baseline_equal"],
            "validator": run["validator"], "downstream_instantiated": False,
            "production_config_modified": False,
            "artifacts": {name: {"size_bytes": (staging / name).stat().st_size, "sha256": sha256_file(staging / name)} for name in names},
            "forbidden_downstream_artifacts": {name: {"expected_absent": True, "absent": True} for name in FORBIDDEN_DOWNSTREAM},
        }
        write_json(staging / "manifest.json", manifest)
        if {path.name for path in staging.iterdir()} != set(MANAGED_ARTIFACTS):
            raise RuntimeError("Staged artifact set mismatch")

        output_dir.parent.mkdir(parents=True, exist_ok=True)
        publish_staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
        backup = output_dir.parent / f".{output_dir.name}.backup-{uuid.uuid4().hex}"
        try:
            for name in MANAGED_ARTIFACTS:
                shutil.copyfile(staging / name, publish_staging / name)
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


def _assert_baseline(run: dict) -> None:
    mismatches = []
    if run["counts"] != EXPECTED_COUNTS: mismatches.append("counts")
    if run["geometry"]["hash"] != EXPECTED_GEOMETRY_SHA256: mismatches.append("geometry_hash")
    if run["topology"]["hash"] != EXPECTED_TOPOLOGY_SHA256: mismatches.append("topology_hash")
    if run["constraint"]["pre_core_sha256"] != EXPECTED_GRAPH_CORE_SHA256: mismatches.append("graph_core_hash")
    if run["source"]["copy_sha256_before"] != run["source"]["copy_sha256_after"]: mismatches.append("copy_mutated")
    if run["source"]["sha256"] != run["source"]["original_sha256_after"]: mismatches.append("source_mutated")
    if mismatches:
        raise RuntimeError(f"BLOCKED_TQ02_BASELINE_DRIFT: {mismatches}")


def run_diagnostics(source: Path, output_dir: Path) -> dict:
    run_a = run_exact_pipeline(source)
    _assert_baseline(run_a)
    run_b = run_exact_pipeline(source)
    _assert_baseline(run_b)
    comparable_keys = (
        "source", "intake", "parser", "configuration", "geometry", "topology",
        "counts", "tiny_loop_ids", "constraint", "validator", "downstream_instantiated",
    )
    if any(run_a[key] != run_b[key] for key in comparable_keys):
        raise RuntimeError("BLOCKED_TQ02_BASELINE_DRIFT: independent runs differ")
    tolerance = tolerance_experiments(run_a["walls"])
    if not all(item["deterministic"] for item in tolerance["bands"]):
        raise RuntimeError("Tolerance ablation is not deterministic")
    ablation = layer_ablation(run_a["walls"])
    return publish_package(
        run_a,
        output_dir,
        tolerance,
        repeat_run=run_b,
        layer_ablation_result=ablation,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic TQ-02 root-cause diagnostics")
    parser.add_argument("--source", type=Path, default=Path("data/proje.dxf"))
    parser.add_argument("--output", type=Path, default=Path("outputs/tq02/proje"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_diagnostics(args.source, args.output)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()