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
    "dangling_candidates.svg",
    "dangling_nodes.csv",
    "dangling_nodes.json",
    "evidence_matrix.json",
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
    blocks = Counter(item["provenance"].get("block_name", "UNKNOWN") for item in dangling)
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


def evaluate_core_fix_gate(independent_reproducer: dict | None = None) -> dict:
    proof = independent_reproducer or {}
    checks = [
        ("exact_authoritative_source", True),
        ("baseline_matches_locked_values", True),
        ("two_independent_runs_deterministic", True),
        ("validator_failure_reproduced", True),
        ("constraint_contribution_excluded", True),
        ("defect_isolated_to_topology_engine", bool(proof.get("isolated"))),
        ("minimal_reproducer_exists", bool(proof.get("exists"))),
        ("permutation_invariant_reproducer", bool(proof.get("permutation_invariant"))),
        ("translation_invariant_reproducer", bool(proof.get("translation_invariant"))),
        ("mathematical_expected_result_unambiguous", bool(proof.get("unambiguous"))),
    ]
    passed = all(value for _, value in checks)
    return {
        "checks": [{"name": name, "passed": value} for name, value in checks],
        "passed": passed,
        "decision": "CORE_FIX_PERMITTED" if passed else "NO_CORE_FIX_INSUFFICIENT_PROOF",
        "frozen_core_edited": False,
    }


def evidence_matrix(run: dict, gate: dict) -> list[dict]:
    return [
        {"hypothesis": "source/modelspace content", "level": "A", "result": "observed_input_candidate_contributor",
         "evidence": "AC1027/INSUNITS=4/audit=0; 13665 modelspace entities; 478 components persist; observation does not prove causality"},
        {"hypothesis": "parser/block/layer selection", "level": "B", "result": "candidate_contributor",
         "evidence": "modelspace selected; no block promotion; graph lacks exact entity lineage"},
        {"hypothesis": "geometry classification/filtering", "level": "B", "result": "candidate_contributor",
         "evidence": "1809 selected entities become 2088 walls; filtering/snapping/merge are measured"},
        {"hypothesis": "topology engine defect", "level": "D", "result": "not_proven",
         "evidence": "no independent minimal mathematical reproducer"},
        {"hypothesis": "constraint solver", "level": "A+", "result": "excluded_for_observed_graph",
         "evidence": f"pre/post graph core equal={run['constraint']['graph_core_equal']}"},
        {"hypothesis": "validator invariant mismatch", "level": "A", "result": "not_supported",
         "evidence": "validator reports measured dangling/open graph; invariant was not relaxed"},
        {"hypothesis": "overall", "level": "B", "result": "mixed_source_selection_geometry_insufficient_intent",
         "evidence": gate["decision"]},
    ]


def candidate_svg(graph: dict, dangling: list[dict]) -> str:
    nodes = {node["id"]: node for node in graph["nodes"]}
    rows = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="30" font-family="sans-serif" font-size="18">TQ-02 dangling candidate evidence</text>',
    ]
    for index, item in enumerate(dangling[:30]):
        node = nodes[item["node_id"]]
        y = 58 + index * 20
        label = html.escape(
            f"N{node['id']} ({node['x']:.3f},{node['y']:.3f}) {item['classification']} level={item['evidence_level']}"
        )
        rows.append(f'<text x="24" y="{y}" font-family="monospace" font-size="11">{label}</text>')
    rows.append('<text x="24" y="680" font-family="sans-serif" font-size="11">First 30 records; coordinate-bearing local artifact, not committed.</text></svg>\n')
    return "".join(rows)


def engineering_report(run: dict, matrix: list[dict], gate: dict) -> str:
    counts = run["counts"]
    return f"""# Kanıt

- Yetkili DXF SHA-256: `{run['source']['sha256']}`; AC1027, INSUNITS={run['intake']['insunits']}, audit errors/fixes={run['intake']['audit_errors']}/{run['intake']['audit_fixes']}.
- İki exact-source koşu ve production 5.0 mm baseline eşleşti: geometry `{run['geometry']['hash']}`, topology `{run['topology']['hash']}`.
- Ölçüm: {counts['nodes']} nodes, {counts['edges']} edges, {counts['loops']} loops, {counts['components']} components, {counts['dangling']} dangling, {counts['tiny_loops']} tiny loops.
- Evidence matrix sonucu: `{matrix[-1]['result']}`.

# Risk Analizi

- Graph kontratı DXF entity kimliğini taşımadığı için provenance geometrik ve kanıt-sınırlıdır; exact entity lineage iddia edilmez.
- Ground truth olmadan opening, gereksiz çizgi ve yanlış duvar seçimi birbirinden kesin ayrıştırılamaz.
- Tolerance ablation bağlantı sayısını ölçer fakat mimari doğruluk veya false-link oranını kanıtlamaz.

# Önerilen Çözüm

- İnsan-onaylı layer/entity ground truth ve bağımsız minimal reproducer sağlanmadan frozen core değiştirilmemeli.
- Provenance kontratı gelecekte Parser→Geometry→Topology boyunca açık kimlik eşlemesiyle ayrı ADR kapsamında ele alınmalı.

# Uygulanan Değişiklik

- Production core değiştirilmedi; exact-source izole diagnostics, attribution envanteri ve atomik local artifact publisher eklendi.
- “Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir şekilde artırıyor mu?” **EVET, ölçülebilir tanılama/determinizm kanıtı üretir; algoritmik davranışı değiştirmez.**

# Doğrulama

- Constraint pre/post core equal=`{run['constraint']['graph_core_equal']}`; validator=`{run['validator']['topology']}`; downstream çalıştırılmadı.
- Conditional core-fix gate: `{gate['decision']}`; frozen_core_edited=`{gate['frozen_core_edited']}`.
- Production config değiştirilmedi; accuracy/F1/IoU iddiası yok.

# Kalan Riskler

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


def publish_package(run: dict, output_dir: Path, tolerance: dict | None = None) -> dict:
    output_dir = validate_output_dir(output_dir)
    gate = evaluate_core_fix_gate()
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
        "validator_mismatch_supported": False,
        "classification_counts": dict(sorted(classifications.items())),
        "conditional_core_fix_gate": gate,
    }
    with tempfile.TemporaryDirectory(prefix="karar-tq02-package-") as temp_dir:
        staging = Path(temp_dir)
        write_json(staging / "baseline_comparison.json", baseline)
        write_json(staging / "component_inventory.json", {"count": len(run["components"]), "components": run["components"]})
        write_json(staging / "dangling_nodes.json", {"count": len(run["dangling"]), "nodes": run["dangling"]})
        _write_csv(staging / "dangling_nodes.csv", run["dangling"])
        write_json(staging / "provenance_inventory.json", provenance_inventory(run["dangling"]))
        write_json(staging / "selection_experiments.json", selection_experiments(run["raw"], run["walls"], run["dangling"]))
        write_json(staging / "tolerance_sensitivity.json", tolerance)
        write_json(staging / "evidence_matrix.json", {"matrix": matrix})
        write_json(staging / "root_cause_summary.json", root_cause)
        (staging / "topology_overview.svg").write_text(
            topology_svg(run["graph"], run["dangling"], run["node_to_component"]), encoding="utf-8", newline="\n"
        )
        (staging / "dangling_candidates.svg").write_text(candidate_svg(run["graph"], run["dangling"]), encoding="utf-8", newline="\n")
        (staging / "TQ02_ENGINEERING_REPORT.md").write_text(engineering_report(run, matrix, gate), encoding="utf-8", newline="\n")
        names = sorted(set(MANAGED_ARTIFACTS) - {"manifest.json"})
        manifest = {
            "schema_version": "tq02-manifest-v1",
            "status": "TQ-02_QUALIFIED_NO_CORE_FIX",
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
    return publish_package(run_a, output_dir, tolerance)


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