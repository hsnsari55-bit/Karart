import os
import sys
import json
import tempfile
import types
import unittest
from pathlib import Path


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _install_stub_module(module_name: str, class_name: str):
    module = types.ModuleType(module_name)

    class _Stub:
        def __init__(self, *args, **kwargs):
            pass

    setattr(module, class_name, _Stub)
    sys.modules[module_name] = module


for _module_name, _class_name in [
    ("dxf_parser", "DXFParser"),
    ("geometry_engine", "GeometryEngine"),
    ("topology_engine", "TopologyEngine"),
    ("constraint_solver", "ConstraintSolver"),
    ("topology_health_report", "TopologyHealthReporter"),
    ("topology_validator", "TopologyValidator"),
    ("semantic_engine", "SemanticEngine"),
    ("space_engine", "SpaceEngine"),
    ("bim_core", "BIMCoreEngine"),
]:
    _install_stub_module(_module_name, _class_name)

import run_regression_tests as regression_module
from output_manifest import build_manifest, verify_manifest
from output_metrics import build_metrics, compare_metrics


RegressionTester = regression_module.RegressionTester


class TestRegressionTopologyReportPath(unittest.TestCase):
    def test_build_topology_validation_report_path_is_per_project_and_relative_to_outputs(self):
        tester = RegressionTester()

        report_path = tester._build_topology_validation_report_path("sample_plan.dxf")

        self.assertTrue(report_path.endswith(os.path.join("outputs", "topology_validation_sample_plan.json")))

    def test_load_topology_validation_summary_reads_status_and_checks(self):
        tester = RegressionTester()
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "topology_validation_sample_plan.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "status": "PASS",
                        "counts": {"nodes": 4, "edges": 4, "loops": 1},
                        "checks": {
                            "non_empty_nodes": True,
                            "non_empty_edges": True,
                            "non_empty_loops": True,
                            "closed_loops": True,
                        },
                    },
                    f,
                    indent=2,
                )

            summary = tester._load_topology_validation_summary(report_path)

        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["checks_passed"], 4)
        self.assertEqual(summary["checks_total"], 4)
        self.assertEqual(summary["counts"]["loops"], 1)

    def test_build_topology_health_report_path_is_per_project_and_relative_to_outputs(self):
        tester = RegressionTester()

        report_path = tester._build_topology_health_report_path("sample_plan.dxf")

        self.assertTrue(report_path.endswith(os.path.join("outputs", "topology_health_sample_plan.json")))

    def test_load_topology_health_summary_reads_status_and_counts(self):
        tester = RegressionTester()
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "topology_health_sample_plan.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "status": "WARNING",
                        "counts": {"nodes": 4, "edges": 3, "loops": 0},
                        "checks": {
                            "degree_metadata_consistency": False,
                        },
                        "graph_metrics": {
                            "connected_components": 2,
                            "component_sizes": [3, 1],
                            "component_size_histogram": {"1": 1, "3": 1},
                            "dangling_node_count": 2,
                            "dangling_node_component_indexes": [0],
                            "self_loop_edge_count": 0,
                            "isolated_node_component_indexes": [1],
                            "degree_metadata_mismatches": [
                                {"node_id": 0, "expected": 2, "actual": 1}
                            ],
                        },
                        "diagnostics": [
                            {
                                "code": "DEGREE_METADATA_MISMATCH",
                                "severity": "WARNING",
                                "message": "Node degree metadata mismatches detected",
                                "context": {
                                    "mismatches": [
                                        {"node_id": 0, "expected": 2, "actual": 1}
                                    ]
                                },
                            }
                        ],
                    },
                    f,
                    indent=2,
                )

            summary = tester._load_topology_health_summary(report_path)

        self.assertEqual(summary["status"], "WARNING")
        self.assertEqual(summary["connected_components"], 2)
        self.assertEqual(summary["component_sizes"], [3, 1])
        self.assertEqual(summary["component_size_histogram"], {"1": 1, "3": 1})
        self.assertEqual(summary["dangling_node_count"], 2)
        self.assertEqual(summary["dangling_node_component_indexes"], [0])
        self.assertEqual(summary["isolated_node_component_indexes"], [1])
        self.assertFalse(summary["degree_metadata_consistency"])
        self.assertEqual(summary["degree_metadata_mismatch_count"], 1)
        self.assertEqual(summary["failed_checks"], ["degree_metadata_consistency"])
        self.assertEqual(summary["issues"], [])
        self.assertEqual(summary["diagnostic_codes"], ["DEGREE_METADATA_MISMATCH"])
        self.assertEqual(summary["counts"]["edges"], 3)

    def test_load_topology_health_summary_adds_validator_check_aliases(self):
        tester = RegressionTester()
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "topology_health_sample_plan.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "status": "WARNING",
                        "checks": {
                            "has_loops": False,
                            "all_loops_closed": False,
                            "no_tiny_loops": False,
                        },
                        "graph_metrics": {},
                        "diagnostics": [],
                    },
                    f,
                    indent=2,
                )

            summary = tester._load_topology_health_summary(report_path)

        self.assertEqual(
            summary["failed_checks"],
            [
                "all_loops_closed",
                "closed_loops",
                "has_loops",
                "no_tiny_loops",
                "no_tiny_sliver_faces",
                "non_empty_loops",
            ],
        )

    def test_load_topology_health_summary_adds_node_and_edge_aliases(self):
        tester = RegressionTester()
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "topology_health_sample_plan.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "status": "WARNING",
                        "checks": {
                            "has_nodes": False,
                            "has_edges": False,
                        },
                        "graph_metrics": {},
                        "diagnostics": [],
                    },
                    f,
                    indent=2,
                )

            summary = tester._load_topology_health_summary(report_path)

        self.assertEqual(
            summary["failed_checks"],
            ["has_edges", "has_nodes", "non_empty_edges", "non_empty_nodes"],
        )

    def test_format_topology_health_markdown_cell_includes_degree_mismatch_count(self):
        tester = RegressionTester()

        cell = tester._format_topology_health_markdown_cell({
            "steps": {
                "constraint_solver": {
                    "topology_health_summary": {
                        "status": "WARNING",
                        "connected_components": 2,
                        "dangling_node_count": 1,
                        "degree_metadata_mismatch_count": 3,
                    }
                }
            }
        })

        self.assertEqual(cell, "⚠️ WARNING (2c/1d/3dm)")

    def test_format_topology_validation_markdown_cell_formats_pass_status(self):
        tester = RegressionTester()

        cell = tester._format_topology_validation_markdown_cell({
            "steps": {
                "constraint_solver": {
                    "topology_validation_summary": {
                        "status": "PASS",
                        "checks_passed": 4,
                        "checks_total": 4,
                    }
                }
            }
        })

        self.assertEqual(cell, "✅ PASS (4/4)")

    def test_evaluate_topology_health_gate_requires_healthy_status(self):
        tester = RegressionTester()

        gate = tester._evaluate_topology_health_gate({
            "status": "WARNING",
            "connected_components": 2,
            "dangling_node_count": 1,
            "self_loop_edge_count": 0,
        })

        self.assertFalse(gate["passed"])
        self.assertEqual(gate["required_status"], "HEALTHY")
        self.assertEqual(gate["actual_status"], "WARNING")
        self.assertFalse(gate["enforced"])
        self.assertEqual(gate["blocking_authority"], "topology_validator")

    def test_run_on_file_runs_validator_and_fails_on_validator_for_warning_health(self):
        tester = RegressionTester()

        class _Parser:
            def parse(self, filepath):
                return {"source": filepath}

        class _Geometry:
            stats = {"segments_in": 4, "segments_out": 4}

            def run(self):
                return [{"wall_id": 1}, {"wall_id": 2}]

        class _Topology:
            stats = {"nodes": 4, "edges": 4, "loops": 1}

            def run(self):
                return {
                    "nodes": [
                        {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                        {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                        {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                        {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
                    ],
                    "edges": [
                        {"id": 1, "from": 0, "to": 1},
                        {"id": 2, "from": 1, "to": 2},
                        {"id": 3, "from": 2, "to": 3},
                        {"id": 4, "from": 3, "to": 0},
                    ],
                    "loops": [
                        {
                            "id": 0,
                            "area": 100.0,
                            "edges": [1, 2, 3, 4],
                            "boundary": [
                                {"x": 0.0, "y": 0.0},
                                {"x": 10.0, "y": 0.0},
                                {"x": 10.0, "y": 10.0},
                                {"x": 0.0, "y": 10.0},
                                {"x": 0.0, "y": 0.0},
                            ],
                        }
                    ],
                }

        class _ConstraintSolver:
            def run(self, graph):
                return graph

        class _Semantic:
            def run(self):
                return {"elements": []}

        class _Space:
            def run(self):
                return {"spaces": []}

        class _BimCore:
            def run(self):
                return {"walls": [], "spaces": []}

        class _HealthReporter:
            def __init__(self, report_output_path):
                self.report_output_path = report_output_path

            def generate(self, graph):
                report = {
                    "status": "WARNING",
                    "counts": {"nodes": 4, "edges": 4, "loops": 1},
                    "graph_metrics": {
                        "connected_components": 2,
                        "component_sizes": [3, 1],
                        "dangling_node_component_indexes": [0],
                        "dangling_node_count": 1,
                        "isolated_node_component_indexes": [],
                        "self_loop_edge_count": 0,
                    },
                    "diagnostics": [
                        {
                            "code": "DANGLING_NODES",
                            "severity": "WARNING",
                            "message": "Dangling nodes detected: [0]",
                            "context": {"node_ids": [0]},
                        }
                    ],
                }
                with open(self.report_output_path, "w", encoding="utf-8") as handle:
                    json.dump(report, handle)
                return report

        class _Validator:
            def __init__(self, report_output_path):
                self.report_output_path = report_output_path

            def validate(self, graph):
                with open(self.report_output_path, "w", encoding="utf-8") as handle:
                    json.dump(
                        {
                            "status": "FAIL",
                            "counts": {"nodes": 4, "edges": 4, "loops": 1},
                            "checks": {
                                "non_empty_nodes": True,
                                "no_dangling_nodes": False,
                            },
                        },
                        handle,
                    )
                raise RuntimeError("Topology validation failed: dangling nodes are blocking.")

        tester.parser = _Parser()
        tester.geometry_engine = _Geometry()
        tester.topology_engine = _Topology()
        tester.constraint_solver = _ConstraintSolver()
        tester.semantic_engine = _Semantic()
        tester.space_engine = _Space()
        tester.bim_core_engine = _BimCore()
        tester.path_manager = types.SimpleNamespace(
            get_relative_path=lambda path: path,
            get_path=lambda *parts: os.path.join(*parts),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            health_report_path = os.path.join(temp_dir, "topology_health_sample_plan.json")
            validation_report_path = os.path.join(temp_dir, "topology_validation_sample_plan.json")

            tester._build_topology_health_report_path = lambda filename: health_report_path
            tester._build_topology_validation_report_path = lambda filename: validation_report_path

            original_health_reporter = regression_module.TopologyHealthReporter
            original_validator = regression_module.TopologyValidator
            regression_module.TopologyHealthReporter = _HealthReporter
            regression_module.TopologyValidator = _Validator
            try:
                report = tester.run_on_file("sample_plan.dxf")
            finally:
                regression_module.TopologyHealthReporter = original_health_reporter
                regression_module.TopologyValidator = original_validator

        self.assertEqual(report["status"], "FAILURE")
        self.assertEqual(report["error_step"], "constraint_solver")
        self.assertIn("Topology validation failed", report["error_msg"])
        self.assertNotIn("Topology health gate failed", report["error_msg"])
        self.assertEqual(report["steps"]["constraint_solver"]["status"], "FAILURE")
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_health_summary"]["status"],
            "WARNING",
        )
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_health_summary"]["failed_checks"],
            [],
        )
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_health_summary"]["diagnostic_codes"],
            ["DANGLING_NODES"],
        )
        self.assertFalse(report["steps"]["constraint_solver"]["topology_health_gate"]["passed"])
        self.assertFalse(report["steps"]["constraint_solver"]["topology_health_gate"]["enforced"])
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_health_gate"]["blocking_authority"],
            "topology_validator",
        )
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_validation_summary"]["status"],
            "FAIL",
        )
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_validation_summary"]["checks_passed"],
            1,
        )
        self.assertEqual(
            report["steps"]["constraint_solver"]["topology_validation_summary"]["checks_total"],
            2,
        )

    def test_manifest_and_metrics_verify_can_pass_while_topology_health_gate_remains_visibility_only(self):
        tester = RegressionTester()

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            outputs_dir = base / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)

            files = [
                "dxf_raw.json",
                "walls_clean.json",
                "geometry_graph.json",
                "bim_semantics.json",
                "spaces.json",
                "bim_model.json",
            ]

            payloads = {
                "dxf_raw.json": {"source": "sample_plan.dxf", "entities": []},
                "walls_clean.json": [
                    {"wall_id": 1, "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
                    {"wall_id": 2, "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
                ],
                "geometry_graph.json": {
                    "nodes": [
                        {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                        {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                        {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                        {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
                    ],
                    "edges": [
                        {"id": 0, "from": 0, "to": 1, "length": 10.0, "angle": 0.0},
                        {"id": 1, "from": 1, "to": 2, "length": 10.0, "angle": 90.0},
                        {"id": 2, "from": 2, "to": 3, "length": 10.0, "angle": 180.0},
                        {"id": 3, "from": 3, "to": 0, "length": 10.0, "angle": 270.0},
                    ],
                    "loops": [
                        {
                            "id": 0,
                            "area": 100.0,
                            "edges": [0, 1, 2, 3],
                            "boundary": [
                                {"x": 0.0, "y": 0.0},
                                {"x": 10.0, "y": 0.0},
                                {"x": 10.0, "y": 10.0},
                                {"x": 0.0, "y": 10.0},
                                {"x": 0.0, "y": 0.0},
                            ],
                        }
                    ],
                },
                "bim_semantics.json": {
                    "elements": [
                        {"type": "Wall"},
                        {"type": "Wall"},
                        {"type": "Door"},
                    ]
                },
                "spaces.json": {"spaces": [{"uuid": "space-1", "area": 100.0}]},
                "bim_model.json": {
                    "provenance": {
                        "generated_at": "2026-01-01T00:00:00Z",
                        "canonical_bim_sha256": "abc",
                        "engine": "KaRar BIM Core",
                    },
                    "walls": [{"uuid": "wall-1"}, {"uuid": "wall-2"}],
                    "doors": [{"uuid": "door-1"}],
                    "windows": [],
                    "columns": [],
                    "spaces": [{"uuid": "space-1"}],
                },
            }

            for file_name, payload in payloads.items():
                with (outputs_dir / file_name).open("w", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2)

            manifest_path = base / "modern_pipeline_outputs.json"
            metrics_path = base / "modern_pipeline_metrics.json"
            with manifest_path.open("w", encoding="utf-8") as handle:
                json.dump(build_manifest(outputs_dir, files), handle, indent=2)
            with metrics_path.open("w", encoding="utf-8") as handle:
                json.dump(build_metrics(outputs_dir), handle, indent=2)

            verify_manifest(manifest_path, outputs_dir, files, verbose=False)
            compare_metrics(metrics_path, outputs_dir, verbose=False)

            health_report_path = base / "topology_health_sample_plan.json"
            with health_report_path.open("w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "status": "WARNING",
                        "counts": {"nodes": 4, "edges": 4, "loops": 1},
                        "checks": {
                            "all_loops_closed": True,
                            "has_loops": True,
                            "no_tiny_loops": True,
                        },
                        "graph_metrics": {
                            "connected_components": 2,
                            "component_sizes": [3, 1],
                            "component_size_histogram": {"1": 1, "3": 1},
                            "dangling_node_count": 1,
                            "dangling_node_component_indexes": [0],
                            "isolated_node_component_indexes": [],
                            "self_loop_edge_count": 0,
                            "degree_metadata_mismatches": [],
                        },
                        "diagnostics": [
                            {
                                "code": "DANGLING_NODES",
                                "severity": "WARNING",
                                "message": "Dangling nodes detected: [0]",
                                "context": {"node_ids": [0]},
                            }
                        ],
                    },
                    handle,
                    indent=2,
                )

            summary = tester._load_topology_health_summary(str(health_report_path))
            gate = tester._evaluate_topology_health_gate(summary)

            self.assertEqual(summary["status"], "WARNING")
            self.assertEqual(summary["diagnostic_codes"], ["DANGLING_NODES"])
            self.assertFalse(gate["passed"])
            self.assertEqual(gate["required_status"], "HEALTHY")
            self.assertEqual(gate["actual_status"], "WARNING")
            self.assertFalse(gate["enforced"])
            self.assertEqual(gate["blocking_authority"], "topology_validator")
            self.assertEqual(tester._enforce_topology_health_gate(summary), gate)


if __name__ == "__main__":
    unittest.main()
