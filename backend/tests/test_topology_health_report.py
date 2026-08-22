import json
import os
import tempfile
import unittest

from backend.topology_health_report import TopologyHealthReporter


class TestTopologyHealthReporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.temp_dir.name, "topology_health_report.json")
        self.reporter = TopologyHealthReporter(report_output_path=self.report_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_reports_healthy_closed_square(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
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
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual(report["graph_metrics"]["degree_metadata_mismatches"], [])
        self.assertEqual(report["graph_metrics"]["connected_components"], 1)
        self.assertEqual(report["graph_metrics"]["component_sizes"], [4])
        self.assertEqual(report["graph_metrics"]["component_node_groups"], [[0, 1, 2, 3]])
        self.assertEqual(report["graph_metrics"]["component_size_histogram"], {"4": 1})
        self.assertEqual(report["graph_metrics"]["dangling_node_count"], 0)
        self.assertEqual(report["graph_metrics"]["dangling_node_component_indexes"], [])
        self.assertEqual(report["loop_metrics"]["closed_loop_count"], 1)
        self.assertTrue(report["checks"]["has_nodes"])
        self.assertTrue(report["checks"]["has_edges"])
        self.assertTrue(report["checks"]["has_loops"])
        self.assertTrue(report["checks"]["non_empty_nodes"])
        self.assertTrue(report["checks"]["non_empty_edges"])
        self.assertTrue(report["checks"]["non_empty_loops"])
        self.assertTrue(report["checks"]["all_loops_closed"])
        self.assertTrue(report["checks"]["closed_loops"])
        self.assertTrue(report["checks"]["no_tiny_loops"])
        self.assertTrue(report["checks"]["no_tiny_sliver_faces"])
        self.assertTrue(os.path.exists(self.report_path))
        with open(self.report_path, "r", encoding="utf-8") as handle:
            persisted = json.load(handle)
        self.assertEqual(persisted["status"], "HEALTHY")

    def test_generate_reports_warning_for_missing_loop_edges_metadata(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["sufficient_unique_loop_edges"])
        self.assertEqual(report["loop_metrics"]["insufficient_unique_loop_edge_count"], 1)
        self.assertEqual(
            report["loop_metrics"]["insufficient_unique_loop_edge_loop_ids"],
            [0],
        )
        self.assertIn(
            "Loops with insufficient unique edge references: [0]",
            report["issues"],
        )
        self.assertIn(
            "INSUFFICIENT_UNIQUE_LOOP_EDGES",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_warning_for_disconnected_and_dangling_graph(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
                {"id": 1, "x": 5.0, "y": 0.0, "degree": 1},
                {"id": 2, "x": 20.0, "y": 0.0, "degree": 0},
            ],
            "edges": [
                {"id": 10, "from": 0, "to": 1},
            ],
            "loops": [],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["single_connected_component"])
        self.assertFalse(report["checks"]["no_dangling_nodes"])
        self.assertEqual(report["graph_metrics"]["connected_components"], 2)
        self.assertEqual(report["graph_metrics"]["component_sizes"], [2, 1])
        self.assertEqual(report["graph_metrics"]["component_node_groups"], [[0, 1], [2]])
        self.assertEqual(report["graph_metrics"]["component_size_histogram"], {"1": 1, "2": 1})
        self.assertEqual(report["graph_metrics"]["dangling_node_count"], 2)
        self.assertEqual(report["graph_metrics"]["dangling_node_component_indexes"], [0])
        self.assertEqual(
            report["graph_metrics"]["dangling_node_components"],
            [
                {
                    "component_index": 0,
                    "component_size": 2,
                    "component_node_ids": [0, 1],
                    "issue_node_ids": [0, 1],
                }
            ],
        )
        self.assertEqual(report["graph_metrics"]["isolated_node_count"], 1)
        self.assertEqual(report["graph_metrics"]["isolated_node_component_indexes"], [1])
        self.assertEqual(
            report["graph_metrics"]["isolated_node_components"],
            [
                {
                    "component_index": 1,
                    "component_size": 1,
                    "component_node_ids": [2],
                    "issue_node_ids": [2],
                }
            ],
        )
        self.assertIn("Graph contains zero closed loops", report["issues"])
        self.assertIn("Disconnected components detected: 2", report["issues"])
        self.assertEqual(
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
            ["ZERO_LOOPS", "DISCONNECTED_COMPONENTS", "DANGLING_NODES", "ISOLATED_NODES"],
        )
        self.assertEqual(
            report["diagnostics"][1]["context"],
            {
                "component_count": 2,
                "component_sizes": [2, 1],
                "component_size_histogram": {"1": 1, "2": 1},
                "component_node_groups": [[0, 1], [2]],
            },
        )
        self.assertEqual(
            report["diagnostics"][2]["context"],
            {
                "node_ids": [0, 1],
                "component_indexes": [0],
                "components": [
                    {
                        "component_index": 0,
                        "component_size": 2,
                        "component_node_ids": [0, 1],
                        "issue_node_ids": [0, 1],
                    }
                ],
            },
        )
        self.assertEqual(
            report["diagnostics"][3]["context"],
            {
                "node_ids": [2],
                "component_indexes": [1],
                "components": [
                    {
                        "component_index": 1,
                        "component_size": 1,
                        "component_node_ids": [2],
                        "issue_node_ids": [2],
                    }
                ],
            },
        )

    def test_generate_reports_critical_for_invalid_edge_references(self):
        graph = {
            "nodes": [{"id": 0, "x": 0.0, "y": 0.0, "degree": 0}],
            "edges": [{"id": 99, "from": 0, "to": 42}],
            "loops": [],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["node_reference_integrity"])
        self.assertEqual(report["graph_metrics"]["invalid_edge_reference_ids"], [99])
        self.assertIn("Invalid edge references: [99]", report["issues"])
        self.assertIn(
            "INVALID_EDGE_REFERENCES",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_warning_for_duplicate_undirected_edges(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 3},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 3},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
                {"id": 4, "from": 1, "to": 0},
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
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["no_duplicate_undirected_edges"])
        self.assertEqual(
            report["graph_metrics"]["duplicate_undirected_edges"],
            [{"nodes": [0, 1], "count": 2}],
        )
        self.assertIn("Duplicate undirected edges detected", report["issues"])
        self.assertIn(
            "DUPLICATE_UNDIRECTED_EDGES",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_critical_for_self_loop_edge(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 4},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
                {"id": 4, "from": 0, "to": 0},
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
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["no_self_loop_edges"])
        self.assertEqual(report["graph_metrics"]["self_loop_edge_count"], 1)
        self.assertEqual(report["graph_metrics"]["self_loop_edge_ids"], [4])
        self.assertIn("Self-loop edges detected: [4]", report["issues"])
        self.assertIn(
            "SELF_LOOP_EDGES",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_critical_for_empty_graph_inputs(self):
        graph = {
            "nodes": [],
            "edges": [],
            "loops": [],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["has_nodes"])
        self.assertFalse(report["checks"]["has_edges"])
        self.assertFalse(report["checks"]["has_loops"])
        self.assertFalse(report["checks"]["non_empty_nodes"])
        self.assertFalse(report["checks"]["non_empty_edges"])
        self.assertFalse(report["checks"]["non_empty_loops"])
        self.assertIn("Graph contains zero nodes", report["issues"])
        self.assertIn("Graph contains zero edges", report["issues"])
        self.assertIn("Graph contains zero closed loops", report["issues"])
        self.assertEqual(
            [diagnostic["code"] for diagnostic in report["diagnostics"][:3]],
            ["ZERO_NODES", "ZERO_EDGES", "ZERO_LOOPS"],
        )

    def test_generate_reports_warning_for_degree_metadata_mismatch(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 3},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["degree_metadata_consistency"])
        self.assertIn(
            "Node degree metadata mismatches detected: [{'node_id': 0, 'expected': 2, 'actual': 3}]",
            report["issues"],
        )
        self.assertEqual(
            report["graph_metrics"]["degree_metadata_mismatches"],
            [{"node_id": 0, "expected": 2, "actual": 3}],
        )
        self.assertEqual(
            report["diagnostics"][0]["code"],
            "DEGREE_METADATA_MISMATCH",
        )

    def test_generate_reports_warning_for_missing_degree_metadata(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["degree_metadata_consistency"])
        self.assertIn(
            "Node degree metadata mismatches detected: [{'node_id': 0, 'expected': 2, 'actual': None}]",
            report["issues"],
        )
        self.assertEqual(
            report["graph_metrics"]["degree_metadata_mismatches"],
            [{"node_id": 0, "expected": 2, "actual": None}],
        )
        self.assertEqual(
            report["diagnostics"][0]["context"]["mismatches"],
            [{"node_id": 0, "expected": 2, "actual": None}],
        )

    def test_generate_reports_warning_for_face_edge_inconsistency(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [0, 1, 2],
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["face_edge_consistency"])
        self.assertEqual(report["loop_metrics"]["face_edge_inconsistency_count"], 1)
        self.assertEqual(report["loop_metrics"]["face_edge_inconsistency_loop_ids"], [0])
        self.assertIn("Face-edge inconsistencies detected: [0]", report["issues"])
        self.assertEqual(
            report["diagnostics"][-1]["code"],
            "FACE_EDGE_INCONSISTENCY",
        )

    def test_generate_reports_warning_for_missing_loop_edge_references(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [0, 1, 2, 999],
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["loop_edge_reference_integrity"])
        self.assertEqual(report["loop_metrics"]["missing_loop_edge_reference_count"], 1)
        self.assertEqual(
            report["loop_metrics"]["missing_loop_edge_reference_loop_ids"],
            [0],
        )
        self.assertIn("Loops reference missing edge ids: [0]", report["issues"])
        self.assertEqual(
            report["diagnostics"][-1]["code"],
            "MISSING_LOOP_EDGE_REFERENCES",
        )

    def test_generate_reports_warning_for_insufficient_unique_loop_edges(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [0, 0, 1, 1],
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["sufficient_unique_loop_edges"])
        self.assertEqual(report["loop_metrics"]["insufficient_unique_loop_edge_count"], 1)
        self.assertEqual(
            report["loop_metrics"]["insufficient_unique_loop_edge_loop_ids"],
            [0],
        )
        self.assertIn("Loops with insufficient unique edge references: [0]", report["issues"])
        self.assertEqual(
            report["diagnostics"][-1]["code"],
            "INSUFFICIENT_UNIQUE_LOOP_EDGES",
        )

    def test_generate_reports_warning_for_non_numeric_loop_boundary_coordinates(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [0, 1, 2, 3],
                    "boundary": [
                        {"x": 0.0, "y": 0.0},
                        {"x": "bad", "y": 0.0},
                        {"x": 10.0, "y": 10.0},
                        {"x": 0.0, "y": 10.0},
                        {"x": 0.0, "y": 0.0},
                    ],
                }
            ],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["face_edge_consistency"])
        self.assertEqual(report["loop_metrics"]["face_edge_inconsistency_count"], 1)
        self.assertEqual(report["loop_metrics"]["face_edge_inconsistency_loop_ids"], [0])
        self.assertIn("Face-edge inconsistencies detected: [0]", report["issues"])
        self.assertIn(
            "FACE_EDGE_INCONSISTENCY",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_critical_for_non_numeric_node_coordinates(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": "bad", "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
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
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["node_coordinate_integrity"])
        self.assertEqual(report["graph_metrics"]["invalid_node_coordinate_ids"], [1])
        self.assertIn("Invalid node coordinates: [1]", report["issues"])
        self.assertIn(
            "INVALID_NODE_COORDINATES",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_critical_for_non_numeric_node_ids(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": "bad", "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 2},
                {"id": 1, "from": 2, "to": 3},
                {"id": 2, "from": 3, "to": 0},
            ],
            "loops": [],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["node_id_integrity"])
        self.assertEqual(report["graph_metrics"]["invalid_node_ids"], ["bad"])
        self.assertIn("Invalid node ids: ['bad']", report["issues"])
        self.assertIn(
            "INVALID_NODE_IDS",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_critical_for_non_numeric_edge_endpoint_ids(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": "bad", "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["edge_endpoint_integrity"])
        self.assertEqual(report["graph_metrics"]["invalid_edge_endpoint_ids"], [0])
        self.assertIn("Invalid edge endpoint ids: [0]", report["issues"])
        self.assertIn(
            "INVALID_EDGE_ENDPOINTS",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_warning_for_non_numeric_loop_area(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": "bad",
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
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["loop_area_integrity"])
        self.assertEqual(report["loop_metrics"]["invalid_loop_area_count"], 1)
        self.assertEqual(report["loop_metrics"]["invalid_loop_area_ids"], [0])
        self.assertIn("Loops contain invalid area metadata: [0]", report["issues"])
        self.assertIn(
            "INVALID_LOOP_AREAS",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_warning_for_invalid_loop_edge_reference_list(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [0, "bad", 2, 3],
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

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertFalse(report["checks"]["loop_edge_id_integrity"])
        self.assertEqual(report["loop_metrics"]["invalid_loop_edge_reference_count"], 1)
        self.assertEqual(report["loop_metrics"]["invalid_loop_edge_reference_loop_ids"], [0])
        self.assertIn("Loops contain invalid edge reference lists: [0]", report["issues"])
        self.assertIn(
            "INVALID_LOOP_EDGE_REFERENCES",
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
        )

    def test_generate_reports_warning_exposes_validator_aliases_for_open_and_tiny_loops(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1},
                {"id": 1, "from": 1, "to": 2},
                {"id": 2, "from": 2, "to": 3},
                {"id": 3, "from": 3, "to": 0},
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 0.0001,
                    "edges": [0, 1, 2, 3],
                    "boundary": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 10.0, "y": 0.0},
                        {"x": 10.0, "y": 10.0},
                        {"x": 0.0, "y": 10.0},
                    ],
                }
            ],
        }

        report = self.reporter.generate(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertTrue(report["checks"]["has_nodes"])
        self.assertTrue(report["checks"]["has_edges"])
        self.assertTrue(report["checks"]["has_loops"])
        self.assertTrue(report["checks"]["non_empty_nodes"])
        self.assertTrue(report["checks"]["non_empty_edges"])
        self.assertTrue(report["checks"]["non_empty_loops"])
        self.assertFalse(report["checks"]["all_loops_closed"])
        self.assertFalse(report["checks"]["closed_loops"])
        self.assertFalse(report["checks"]["no_tiny_loops"])
        self.assertFalse(report["checks"]["no_tiny_sliver_faces"])
        self.assertEqual(report["loop_metrics"]["open_loop_count"], 1)
        self.assertEqual(report["loop_metrics"]["tiny_loop_count"], 1)
        self.assertEqual(report["loop_metrics"]["open_loop_ids"], [0])
        self.assertEqual(report["loop_metrics"]["tiny_loop_ids"], [0])
        self.assertIn("Open loops detected: [0]", report["issues"])
        self.assertIn("Tiny loops detected: [0]", report["issues"])
        self.assertIn("OPEN_LOOPS", [diagnostic["code"] for diagnostic in report["diagnostics"]])
        self.assertIn("TINY_LOOPS", [diagnostic["code"] for diagnostic in report["diagnostics"]])

    def test_logical_connector_improves_only_effective_connectivity_metrics(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 1},
                {"id": 2, "x": 20.0, "y": 0.0, "degree": 1},
                {"id": 3, "x": 30.0, "y": 0.0, "degree": 1},
            ],
            "edges": [
                {"id": 10, "from": 0, "to": 1},
                {"id": 11, "from": 2, "to": 3},
            ],
            "loops": [],
            "logical_connectors": [
                {
                    "id": "ag04-reporter-valid",
                    "role": "DOOR_PORTAL",
                    "physical": False,
                    "from": 1,
                    "to": 2,
                    "host_edge_ids": [10, 11],
                    "source_primitive_id": "door-source",
                    "source_layer_normalized": "kapi",
                    "evidence_class": "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS",
                    "length_mm": 10.0,
                }
            ],
        }

        report = self.reporter.build_report(graph)

        self.assertEqual(report["counts"]["edges"], 2)
        self.assertEqual(report["counts"]["physical_edges"], 2)
        self.assertEqual(report["counts"]["logical_connectors"], 1)
        self.assertEqual(report["counts"]["effective_edges"], 3)
        self.assertEqual(report["graph_metrics"]["connected_components"], 1)
        self.assertEqual(report["graph_metrics"]["dangling_node_ids"], [0, 3])
        self.assertEqual(report["graph_metrics"]["degree_histogram"], {"1": 4})
        self.assertEqual(report["graph_metrics"]["physical_degree_histogram"], {"1": 4})
        self.assertEqual(
            report["graph_metrics"]["effective_degree_histogram"],
            {"1": 2, "2": 2},
        )
        self.assertTrue(report["checks"]["logical_connector_integrity"])
        self.assertEqual(report["graph_metrics"]["logical_connector_rejections"], [])
        self.assertEqual(graph["edges"], [{"id": 10, "from": 0, "to": 1}, {"id": 11, "from": 2, "to": 3}])

    def test_malformed_logical_connector_is_critical_and_does_not_change_topology(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 1},
                {"id": 2, "x": 20.0, "y": 0.0, "degree": 1},
                {"id": 3, "x": 30.0, "y": 0.0, "degree": 1},
            ],
            "edges": [
                {"id": 10, "from": 0, "to": 1},
                {"id": 11, "from": 2, "to": 3},
            ],
            "loops": [],
            "logical_connectors": [
                {
                    "id": "ag04-reporter-invalid",
                    "role": "DOOR_PORTAL",
                    "physical": True,
                    "from": 1,
                    "to": 2,
                    "host_edge_ids": [10, 11],
                    "source_primitive_id": "door-source",
                    "source_layer_normalized": "kapi",
                    "evidence_class": "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS",
                    "length_mm": 10.0,
                }
            ],
        }

        report = self.reporter.build_report(graph)

        rejection = {
            "connector_id": "ag04-reporter-invalid",
            "reason": "CONNECTOR_MUST_BE_NON_PHYSICAL",
        }
        self.assertEqual(report["status"], "CRITICAL")
        self.assertFalse(report["checks"]["logical_connector_integrity"])
        self.assertEqual(report["counts"]["logical_connectors"], 0)
        self.assertEqual(report["counts"]["effective_edges"], 2)
        self.assertEqual(report["graph_metrics"]["connected_components"], 2)
        self.assertEqual(report["graph_metrics"]["dangling_node_ids"], [0, 1, 2, 3])
        self.assertEqual(report["graph_metrics"]["logical_connector_rejections"], [rejection])
        self.assertEqual(report["diagnostics"][-1]["code"], "INVALID_LOGICAL_CONNECTORS")
        self.assertEqual(report["diagnostics"][-1]["context"], {"rejections": [rejection]})

    def test_no_connector_evidence_preserves_legacy_report_shape(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 1},
            ],
            "edges": [{"id": 10, "from": 0, "to": 1}],
            "loops": [],
        }

        report = self.reporter.build_report(graph)

        self.assertEqual(report["counts"], {"nodes": 2, "edges": 1, "loops": 0})
        self.assertNotIn("logical_connector_integrity", report["checks"])
        self.assertNotIn("physical_degree_histogram", report["graph_metrics"])
        self.assertNotIn("effective_degree_histogram", report["graph_metrics"])
        self.assertNotIn("logical_connector_rejections", report["graph_metrics"])


if __name__ == "__main__":
    unittest.main()