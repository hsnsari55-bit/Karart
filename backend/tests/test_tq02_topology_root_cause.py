import copy
import csv
import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from backend.tq02_topology_root_cause import (
    EXPECTED_COUNTS,
    EXPECTED_GEOMETRY_SHA256,
    EXPECTED_GRAPH_CORE_SHA256,
    EXPECTED_SOURCE_SHA256,
    EXPECTED_TOPOLOGY_SHA256,
    MANAGED_ARTIFACTS,
    build_dangling_inventory,
    compare_constraint_graphs,
    component_investigation,
    evaluate_core_fix_gate,
    evidence_matrix,
    layer_ablation,
    publish_package,
    provenance_inventory,
    selection_experiments,
    stable_hash,
    validate_output_dir,
)
from backend.tq01_topology_diagnostics import component_inventory


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
    components, node_to_component = component_inventory(graph)
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
        "components": components,
        "node_to_component": node_to_component, "dangling": dangling,
    }


def _locked_gate_run():
    run = _run_fixture()
    run.update({
        "source": {
            "name": "proje.dxf",
            "sha256": EXPECTED_SOURCE_SHA256,
            "copy_sha256_before": EXPECTED_SOURCE_SHA256,
            "copy_sha256_after": EXPECTED_SOURCE_SHA256,
            "original_sha256_after": EXPECTED_SOURCE_SHA256,
        },
        "parser": {"entity_count": EXPECTED_COUNTS["parser_entities"]},
        "configuration": {"production_tolerance_mm": 5.0, "production_config_modified": False},
        "geometry": {"hash": EXPECTED_GEOMETRY_SHA256},
        "topology": {"hash": EXPECTED_TOPOLOGY_SHA256},
        "counts": copy.deepcopy(EXPECTED_COUNTS),
        "tiny_loop_ids": [1, 2, 3],
        "constraint": {
            "graph_core_equal": True,
            "pre_core_sha256": EXPECTED_GRAPH_CORE_SHA256,
            "contribution": "none_observed",
        },
        "validator": {"topology": "FAIL", "downstream_executed": False},
        "downstream_instantiated": False,
    })
    return run


class TestTQ02TopologyRootCause(unittest.TestCase):
    def test_dangling_attribution_is_explicitly_inferred_and_candidate_based(self):
        run = _run_fixture()
        records = run["dangling"]
        self.assertEqual(records[1]["classification"], "candidate_endpoint_to_endpoint")
        self.assertFalse(records[1]["provenance"]["exact_entity_lineage"])
        self.assertEqual(records[1]["provenance"]["confidence"], "inferred_unique_tuple")

    def test_provenance_and_selection_have_distinct_bounded_contracts(self):
        run = _run_fixture()
        provenance = provenance_inventory(run["dangling"])
        selection = selection_experiments(run["raw"], run["walls"], run["dangling"])
        self.assertEqual(provenance["artifact_contract"], "dangling_provenance_summary_v1")
        self.assertFalse(provenance["exact_entity_lineage_available"])
        self.assertEqual(provenance["record_count"], len(run["dangling"]))
        self.assertEqual(provenance["attributed_block_counts"], {"default": 4})
        self.assertTrue(all(item["provenance"]["block"] == "default" for item in run["dangling"]))
        self.assertTrue(all("block_name" not in item["provenance"] for item in run["dangling"]))
        self.assertEqual(selection["artifact_contract"], "selection_inventory_v1")
        self.assertIn("raw_layer_counts", selection)
        self.assertNotIn("raw_layer_counts", provenance)
        self.assertNotEqual(stable_hash(provenance), stable_hash(selection))

        source_evidence = evidence_matrix(run, evaluate_core_fix_gate())[0]
        self.assertEqual(source_evidence["result"], "observed_input_candidate_contributor")
        self.assertIn("does not prove causality", source_evidence["evidence"])

    def test_constraint_comparison_detects_equal_and_changed_core(self):
        graph = _graph()
        self.assertEqual(compare_constraint_graphs(graph, graph)["contribution"], "none_observed")
        changed = {**graph, "edges": graph["edges"][:1]}
        self.assertEqual(compare_constraint_graphs(graph, changed)["contribution"], "graph_changed")

    def test_conditional_core_fix_gate_denies_without_independent_reproducer(self):
        gate = evaluate_core_fix_gate()
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["decision"], "NO_CORE_FIX_INSUFFICIENT_PROOF")
        self.assertEqual(len(gate["checks"]), 10)
        self.assertFalse(gate["frozen_core_edited"])

    def test_first_five_gate_checks_are_run_derived_and_individually_falsifiable(self):
        run = _locked_gate_run()
        repeat = copy.deepcopy(run)
        names = [
            "exact_authoritative_source",
            "baseline_matches_locked_values",
            "two_independent_runs_deterministic",
            "validator_failure_reproduced",
            "constraint_contribution_excluded",
        ]
        baseline = {item["name"]: item["passed"] for item in evaluate_core_fix_gate(run, repeat)["checks"]}
        self.assertTrue(all(baseline[name] for name in names))

        mutations = [
            lambda current, repeated: current["source"].__setitem__("sha256", "drift"),
            lambda current, repeated: current["counts"].__setitem__("nodes", -1),
            lambda current, repeated: repeated["counts"].__setitem__("nodes", -1),
            lambda current, repeated: current["validator"].__setitem__("topology", "PASS"),
            lambda current, repeated: current["constraint"].__setitem__("graph_core_equal", False),
        ]
        for expected_false, mutate in zip(names, mutations):
            with self.subTest(check=expected_false):
                current, repeated = copy.deepcopy(run), copy.deepcopy(repeat)
                mutate(current, repeated)
                checks = {
                    item["name"]: item["passed"]
                    for item in evaluate_core_fix_gate(current, repeated)["checks"]
                }
                self.assertFalse(checks[expected_false])
                self.assertFalse(evaluate_core_fix_gate(current, repeated)["passed"])

    def test_caller_boolean_assertions_cannot_authorize_core_edit(self):
        claimed = {name: True for name in (
            "defect_isolated_to_topology_engine", "minimal_reproducer_exists",
            "permutation_invariant_reproducer", "translation_invariant_reproducer",
            "mathematical_expected_result_unambiguous",
        )}
        gate = evaluate_core_fix_gate(_locked_gate_run(), _locked_gate_run(), claimed)
        self.assertFalse(gate["passed"])
        self.assertTrue(gate["caller_assertions_ignored"])
        self.assertFalse(gate["independent_reproducer_evidence_verified"])
        self.assertTrue(all(not item["passed"] for item in gate["checks"][5:]))

    def test_crafted_reproducer_envelope_cannot_authorize_core_edit(self):
        expected_graph = {"nodes": [{"id": 1}], "edges": []}
        actual_graph = {"nodes": [{"id": 2}], "edges": []}
        expected_hash = stable_hash(expected_graph)
        actual_hash = stable_hash(actual_graph)
        payload = {
            "stage_isolation": {
                "parser_geometry_reproduced_sha256": "same",
                "parser_geometry_expected_sha256": "same",
                "topology_actual_sha256": actual_hash,
                "topology_expected_sha256": expected_hash,
            },
            "minimal_reproducer": {
                "input_graph": {"nodes": [{"id": 0}]},
                "expected_graph": expected_graph,
                "actual_graph": actual_graph,
                "expected_graph_sha256": expected_hash,
                "actual_graph_sha256": actual_hash,
            },
            "permutation_output_sha256": [actual_hash, actual_hash],
            "translation_normalized_output_sha256": [actual_hash, actual_hash],
            "mathematical_rule": "caller supplied claim",
        }
        envelope = {
            "schema_version": "tq02-independent-reproducer-v1",
            "verifier": "backend.tq02_topology_root_cause",
            "payload_sha256": stable_hash(payload),
            "verified_payload": payload,
        }
        gate = evaluate_core_fix_gate(_locked_gate_run(), _locked_gate_run(), envelope)
        self.assertFalse(gate["passed"])
        self.assertFalse(gate["independent_reproducer_evidence_verified"])
        self.assertEqual(
            gate["independent_reproducer_evidence_status"],
            "UNTRUSTED_CALLER_INPUT_INTERNAL_VERIFIER_NOT_IMPLEMENTED",
        )
        self.assertTrue(all(not item["passed"] for item in gate["checks"][5:]))

    def test_layer_ablation_has_combined_baseline_and_sorted_isolated_layers(self):
        walls = [
            {"layer": "Z", "id": 1},
            {"layer": "A", "id": 2},
            {"layer": "Z", "id": 3},
        ]

        def fake_run_topology(selected, tolerance):
            count = len(selected)
            graph = {
                "nodes": [
                    {"id": index, "x": float(index), "y": 0.0, "degree": 0}
                    for index in range(count)
                ],
                "edges": [],
                "loops": [],
            }
            return graph, {"tolerance": tolerance}

        with patch("backend.tq02_topology_root_cause._run_topology", side_effect=fake_run_topology):
            result = layer_ablation(walls)

        self.assertEqual(
            [item["selection"] for item in result["runs"]],
            ["combined_production_baseline", "isolated_layer:A", "isolated_layer:Z"],
        )
        self.assertEqual([item["wall_count"] for item in result["runs"]], [3, 1, 2])
        self.assertFalse(result["production_config_modified"])

    def test_component_investigation_is_stable_and_uses_real_provenance_tuples(self):
        run = _run_fixture()
        first = component_investigation(run)
        second = component_investigation(copy.deepcopy(run))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)
        self.assertTrue(all(item["stable_id"].startswith("cmp-") for item in first))
        self.assertTrue(all(len(item["structural_sha256"]) == 64 for item in first))
        self.assertTrue(all(item["nearest_component_node_distance_mm"] == 2.0 for item in first))
        self.assertEqual(
            sum(row["count"] for item in first for row in item["provenance_tuple_counts"]),
            len(run["dangling"]),
        )
        self.assertEqual(
            {row["block"] for item in first for row in item["provenance_tuple_counts"]},
            {"default"},
        )

    def test_unsafe_output_is_rejected_and_sentinel_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sentinel = temp_path / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            previous_cwd = Path.cwd()
            try:
                os.chdir(temp_path)
                with self.assertRaises(ValueError):
                    validate_output_dir(temp_path)
            finally:
                os.chdir(previous_cwd)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_package_is_exact_byte_identical_and_six_section_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            run = _run_fixture()
            out_a = temp_path / "tq02" / "a"
            out_b = temp_path / "tq02" / "b"
            publish_package(run, out_a)
            publish_package(run, out_b)
            self.assertEqual({path.name for path in out_a.iterdir()}, set(MANAGED_ARTIFACTS))
            self.assertEqual(
                {path.name: path.read_bytes() for path in out_a.iterdir()},
                {path.name: path.read_bytes() for path in out_b.iterdir()},
            )
            manifest = json.loads((out_a / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "tq02-manifest-v2")
            self.assertEqual(manifest["status"], "TQ02_AWAITING_HUMAN_GROUND_TRUTH")
            self.assertEqual(set(manifest["artifacts"]), set(MANAGED_ARTIFACTS) - {"manifest.json"})
            self.assertFalse(manifest["downstream_instantiated"])
            self.assertFalse(manifest["production_config_modified"])
            self.assertNotEqual(
                manifest["artifacts"]["provenance_inventory.json"]["sha256"],
                manifest["artifacts"]["selection_experiments.json"]["sha256"],
            )
            for svg in ("topology_overview.svg", "dangling_candidates.svg", "largest_component.svg"):
                root = ET.parse(out_a / svg).getroot()
                self.assertTrue(root.findall(".//{http://www.w3.org/2000/svg}line"))
            dangling_svg = (out_a / "dangling_candidates.svg").read_text(encoding="utf-8")
            self.assertIn("<circle", dangling_svg)

            with (out_a / "component_layer_matrix.csv").open(encoding="utf-8", newline="") as handle:
                matrix_rows = list(csv.DictReader(handle))
            self.assertEqual(sum(int(row["attributed_count"]) for row in matrix_rows), 4)
            self.assertEqual({row["block"] for row in matrix_rows}, {"default"})
            self.assertEqual({row["entity_type"] for row in matrix_rows}, {"LWPOLYLINE"})

            with (out_a / "ground_truth_review.csv").open(encoding="utf-8", newline="") as handle:
                review_rows = list(csv.DictReader(handle))
            self.assertEqual(len(review_rows), 4)
            self.assertTrue(all(row["review_label"] == row["reviewer"] == row["review_notes"] == "" for row in review_rows))

            root_cause = json.loads((out_a / "root_cause_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(root_cause["validator_invariant_mismatch"], "NOT_EVALUATED_INSUFFICIENT_GROUND_TRUTH")
            report = (out_a / "TQ02_ENGINEERING_REPORT.md").read_text(encoding="utf-8")
            self.assertEqual(
                [line for line in report.splitlines() if line.startswith("## ")],
                [
                    "## 1. Kanıt", "## 2. Risk Analizi", "## 3. Önerilen Çözüm",
                    "## 4. Uygulanan Değişiklik", "## 5. Doğrulama", "## 6. Kalan Riskler",
                ],
            )
            self.assertIn("HAYIR — Bu değişiklik core algoritma davranışını değiştirmez", report)
            self.assertNotIn("Ã", report)
            self.assertNotIn("Â", report)

    def test_atomic_publish_removes_stale_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "tq02" / "proje"
            output.mkdir(parents=True)
            (output / "stale.txt").write_text("stale", encoding="utf-8")
            publish_package(_run_fixture(), output)
            self.assertFalse((output / "stale.txt").exists())
