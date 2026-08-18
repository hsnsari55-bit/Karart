import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from backend.tq02_topology_root_cause import (
    MANAGED_ARTIFACTS,
    build_dangling_inventory,
    compare_constraint_graphs,
    evaluate_core_fix_gate,
    evidence_matrix,
    publish_package,
    provenance_inventory,
    selection_experiments,
    stable_hash,
    validate_output_dir,
)


def _graph():
    return {
        "nodes": [
            {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
            {"id": 1, "x": 10.0, "y": 0.0, "degree": 1},
            {"id": 2, "x": 12.0, "y": 0.0, "degree": 1},
            {"id": 3, "x": 20.0, "y": 0.0, "degree": 1},
        ],
        "edges": [
            {"id": 0, "from": 0, "to": 1, "length": 10.0},
            {"id": 1, "from": 2, "to": 3, "length": 8.0},
        ],
        "loops": [],
    }


def _run_fixture():
    graph = _graph()
    walls = [
        {"layer": "DUVAR", "block_name": "default", "type": "LWPOLYLINE", "points": [[0, 0], [10, 0]]},
        {"layer": "DUVAR", "block_name": "default", "type": "LWPOLYLINE", "points": [[12, 0], [20, 0]]},
    ]
    node_to_component = {0: 0, 1: 0, 2: 1, 3: 1}
    dangling = build_dangling_inventory(graph, walls, node_to_component)
    core_hash = stable_hash(graph)
    return {
        "source": {"name": "fixture.dxf", "sha256": "fixture", "copy_sha256_before": "fixture", "copy_sha256_after": "fixture", "original_sha256_after": "fixture"},
        "intake": {"insunits": 4, "audit_errors": 0, "audit_fixes": 0},
        "geometry": {"hash": "fixture"}, "topology": {"hash": "fixture"},
        "counts": {"modelspace_entities": 2, "parser_entities": 2, "walls": 2, "nodes": 4, "edges": 2, "loops": 0, "components": 2, "dangling": 4, "tiny_loops": 0},
        "constraint": {"graph_core_equal": True, "pre_core_sha256": core_hash, "contribution": "none_observed"},
        "validator": {"topology": "FAIL", "downstream_executed": False},
        "raw": {"entities": [{"layer": "DUVAR", "block_name": "default", "type": "LINE"}] * 2},
        "walls": walls, "graph": graph,
        "components": [{"component_id": 0}, {"component_id": 1}],
        "node_to_component": node_to_component, "dangling": dangling,
    }


def test_dangling_attribution_is_explicitly_inferred_and_candidate_based():
    run = _run_fixture()
    records = run["dangling"]
    assert records[1]["classification"] == "candidate_endpoint_to_endpoint"
    assert records[1]["provenance"]["exact_entity_lineage"] is False
    assert records[1]["provenance"]["confidence"] == "inferred_unique_tuple"


def test_provenance_and_selection_have_distinct_bounded_contracts():
    run = _run_fixture()
    provenance = provenance_inventory(run["dangling"])
    selection = selection_experiments(run["raw"], run["walls"], run["dangling"])
    assert provenance["artifact_contract"] == "dangling_provenance_summary_v1"
    assert provenance["exact_entity_lineage_available"] is False
    assert provenance["record_count"] == len(run["dangling"])
    assert selection["artifact_contract"] == "selection_inventory_v1"
    assert "raw_layer_counts" in selection
    assert "raw_layer_counts" not in provenance
    assert stable_hash(provenance) != stable_hash(selection)

    source_evidence = evidence_matrix(run, evaluate_core_fix_gate())[0]
    assert source_evidence["result"] == "observed_input_candidate_contributor"
    assert "does not prove causality" in source_evidence["evidence"]


def test_constraint_comparison_detects_equal_and_changed_core():
    graph = _graph()
    assert compare_constraint_graphs(graph, graph)["contribution"] == "none_observed"
    changed = {**graph, "edges": graph["edges"][:1]}
    assert compare_constraint_graphs(graph, changed)["contribution"] == "graph_changed"


def test_conditional_core_fix_gate_denies_without_independent_reproducer():
    gate = evaluate_core_fix_gate()
    assert gate["passed"] is False
    assert gate["decision"] == "NO_CORE_FIX_INSUFFICIENT_PROOF"
    assert len(gate["checks"]) == 10
    assert gate["frozen_core_edited"] is False


def test_unsafe_output_is_rejected_and_sentinel_preserved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_output_dir(tmp_path)
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_package_is_exact_byte_identical_and_six_section_report(tmp_path):
    run = _run_fixture()
    out_a = tmp_path / "tq02" / "a"
    out_b = tmp_path / "tq02" / "b"
    publish_package(run, out_a)
    publish_package(run, out_b)
    assert {path.name for path in out_a.iterdir()} == set(MANAGED_ARTIFACTS)
    assert {path.name: path.read_bytes() for path in out_a.iterdir()} == {
        path.name: path.read_bytes() for path in out_b.iterdir()
    }
    manifest = json.loads((out_a / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["downstream_instantiated"] is False
    assert manifest["production_config_modified"] is False
    assert manifest["artifacts"]["provenance_inventory.json"]["sha256"] != manifest["artifacts"]["selection_experiments.json"]["sha256"]
    for svg in ("topology_overview.svg", "dangling_candidates.svg"):
        ET.parse(out_a / svg)
    report = (out_a / "TQ02_ENGINEERING_REPORT.md").read_text(encoding="utf-8")
    assert [line for line in report.splitlines() if line.startswith("# ")] == [
        "# Kanıt", "# Risk Analizi", "# Önerilen Çözüm",
        "# Uygulanan Değişiklik", "# Doğrulama", "# Kalan Riskler",
    ]
    assert "Ã" not in report and "Â" not in report


def test_atomic_publish_removes_stale_file(tmp_path):
    output = tmp_path / "tq02" / "proje"
    output.mkdir(parents=True)
    (output / "stale.txt").write_text("stale", encoding="utf-8")
    publish_package(_run_fixture(), output)
    assert not (output / "stale.txt").exists()