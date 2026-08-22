import os
import sys
import json
import tempfile
import unittest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.topology_validator import TopologyValidator, TopologyValidationError


class TestTopologyValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.temp_dir.name, "topology_validation_report.json")
        self.validator = TopologyValidator(report_output_path=self.report_path)
        self.valid_graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2, "type": "L_corner"},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2, "type": "L_corner"},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2, "type": "L_corner"},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2, "type": "L_corner"},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1, "length": 10.0, "angle": 0.0},
                {"id": 1, "from": 1, "to": 2, "length": 10.0, "angle": 90.0},
                {"id": 2, "from": 2, "to": 3, "length": 10.0, "angle": 0.0},
                {"id": 3, "from": 3, "to": 0, "length": 10.0, "angle": 90.0},
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

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_passes_for_closed_consistent_loop(self):
        self.assertTrue(self.validator.validate(self.valid_graph))
        self.assertTrue(os.path.exists(self.report_path))
        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["counts"]["loops"], 1)

    def test_validate_pass_report_includes_full_loop_integrity_contract(self):
        self.assertTrue(self.validator.validate(self.valid_graph))

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["checks"]["all_loops_closed"])
        self.assertTrue(report["checks"]["loop_area_integrity"])
        self.assertTrue(report["checks"]["loop_edge_id_integrity"])
        self.assertTrue(report["checks"]["loop_edge_reference_integrity"])
        self.assertTrue(report["checks"]["sufficient_unique_loop_edges"])
        self.assertTrue(report["checks"]["face_edge_consistency"])
        self.assertTrue(report["checks"]["closed_loops"])
        self.assertTrue(report["checks"]["no_tiny_sliver_faces"])

    def test_validate_fails_for_dangling_node(self):
        graph = {**self.valid_graph}
        graph["edges"] = self.valid_graph["edges"][:-1]
        graph["nodes"] = [
            {**node, "degree": 1} if node["id"] in {0, 3} else node
            for node in self.valid_graph["nodes"]
        ]
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["edges"] = [0, 1, 2]
        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)
        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Dangling/open topology", report["error"])

    def test_validate_fails_when_node_degree_metadata_disagrees_with_edges(self):
        graph = {
            **self.valid_graph,
            "nodes": [
                {**self.valid_graph["nodes"][0], "degree": 3},
                *self.valid_graph["nodes"][1:],
            ],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Node degree metadata is inconsistent", report["error"])

    def test_validate_fails_when_node_degree_metadata_is_missing(self):
        graph = {
            **self.valid_graph,
            "nodes": [
                {key: value for key, value in self.valid_graph["nodes"][0].items() if key != "degree"},
                *self.valid_graph["nodes"][1:],
            ],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Node degree metadata is inconsistent", report["error"])

    def test_validate_fails_for_open_loop(self):
        graph = {**self.valid_graph}
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["boundary"] = graph["loops"][0]["boundary"][:-1]
        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

    def test_validate_fails_for_tiny_sliver_face(self):
        graph = {**self.valid_graph}
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["area"] = 0.5
        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

    def test_validate_fails_for_face_edge_mismatch(self):
        graph = {**self.valid_graph}
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["edges"] = [0, 1, 2]
        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

    def test_validate_fails_for_self_loop_edge(self):
        graph = {
            **self.valid_graph,
            "edges": [
                *self.valid_graph["edges"],
                {"id": 4, "from": 0, "to": 0, "length": 0.0, "angle": 0.0},
            ],
            "nodes": [
                {**self.valid_graph["nodes"][0], "degree": 4},
                {**self.valid_graph["nodes"][1], "degree": 2},
                *self.valid_graph["nodes"][2:],
            ],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Self-loop edges detected", report["error"])

    def test_validate_fails_for_duplicate_undirected_edges(self):
        graph = {
            **self.valid_graph,
            "edges": [
                self.valid_graph["edges"][0],
                {"id": 4, "from": 1, "to": 0, "length": 10.0, "angle": 0.0},
                *self.valid_graph["edges"][1:],
            ],
            "nodes": [
                {**self.valid_graph["nodes"][0], "degree": 3},
                {**self.valid_graph["nodes"][1], "degree": 3},
                *self.valid_graph["nodes"][2:],
            ],
            "loops": [
                {
                    **self.valid_graph["loops"][0],
                    "edges": [0, 1, 2, 3, 4],
                }
            ],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Duplicate undirected edges detected", report["error"])

    def test_validate_fails_for_invalid_edge_references(self):
        graph = {
            **self.valid_graph,
            "edges": [
                {"id": 99, "from": 0, "to": 42, "length": 10.0, "angle": 0.0},
                *self.valid_graph["edges"][1:],
            ],
            "nodes": [
                {**self.valid_graph["nodes"][0], "degree": 1},
                {**self.valid_graph["nodes"][1], "degree": 1},
                {**self.valid_graph["nodes"][2], "degree": 2},
                {**self.valid_graph["nodes"][3], "degree": 2},
            ],
            "loops": self.valid_graph["loops"],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("references missing node ids", report["error"])

    def test_validate_fails_for_disconnected_closed_components(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2, "type": "L_corner"},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2, "type": "L_corner"},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2, "type": "L_corner"},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2, "type": "L_corner"},
                {"id": 4, "x": 100.0, "y": 100.0, "degree": 2, "type": "L_corner"},
                {"id": 5, "x": 110.0, "y": 100.0, "degree": 2, "type": "L_corner"},
                {"id": 6, "x": 110.0, "y": 110.0, "degree": 2, "type": "L_corner"},
                {"id": 7, "x": 100.0, "y": 110.0, "degree": 2, "type": "L_corner"},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1, "length": 10.0, "angle": 0.0},
                {"id": 1, "from": 1, "to": 2, "length": 10.0, "angle": 90.0},
                {"id": 2, "from": 2, "to": 3, "length": 10.0, "angle": 0.0},
                {"id": 3, "from": 3, "to": 0, "length": 10.0, "angle": 90.0},
                {"id": 4, "from": 4, "to": 5, "length": 10.0, "angle": 0.0},
                {"id": 5, "from": 5, "to": 6, "length": 10.0, "angle": 90.0},
                {"id": 6, "from": 6, "to": 7, "length": 10.0, "angle": 0.0},
                {"id": 7, "from": 7, "to": 4, "length": 10.0, "angle": 90.0},
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
                },
                {
                    "id": 1,
                    "area": 100.0,
                    "edges": [4, 5, 6, 7],
                    "boundary": [
                        {"x": 100.0, "y": 100.0},
                        {"x": 110.0, "y": 100.0},
                        {"x": 110.0, "y": 110.0},
                        {"x": 100.0, "y": 110.0},
                        {"x": 100.0, "y": 100.0},
                    ],
                },
            ],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Disconnected components detected", report["error"])

    def test_validate_treats_isolated_nodes_as_disconnected_not_dangling(self):
        graph = {
            **self.valid_graph,
            "nodes": [
                *self.valid_graph["nodes"],
                {"id": 4, "x": 100.0, "y": 100.0, "degree": 0, "type": "isolated"},
            ],
        }

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Disconnected components detected", report["error"])
        self.assertNotIn("Dangling/open topology", report["error"])

    def test_validate_fails_deterministically_for_loop_boundary_missing_coordinates(self):
        graph = {**self.valid_graph}
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["boundary"] = [
            {"x": 0.0, "y": 0.0},
            {"x": 10.0},
            {"x": 10.0, "y": 10.0},
            {"x": 0.0, "y": 10.0},
            {"x": 0.0, "y": 0.0},
        ]

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains invalid boundary coordinates", report["error"])

    def test_validate_fails_deterministically_for_non_numeric_node_coordinates(self):
        graph = {
            **self.valid_graph,
            "nodes": [dict(node) for node in self.valid_graph["nodes"]],
        }
        graph["nodes"][1]["x"] = "bad"

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains invalid node coordinates", report["error"])

    def test_validate_fails_deterministically_for_non_numeric_node_id(self):
        graph = {
            **self.valid_graph,
            "nodes": [dict(node) for node in self.valid_graph["nodes"]],
        }
        graph["nodes"][1]["id"] = "bad"

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains invalid node id", report["error"])

    def test_validate_fails_deterministically_for_non_numeric_edge_endpoint_ids(self):
        graph = {
            **self.valid_graph,
            "edges": [dict(edge) for edge in self.valid_graph["edges"]],
        }
        graph["edges"][0]["from"] = "bad"

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains invalid endpoint node ids", report["error"])

    def test_validate_fails_deterministically_for_non_numeric_loop_area(self):
        graph = {**self.valid_graph}
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["area"] = "bad"

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains invalid area metadata", report["error"])

    def test_validate_fails_deterministically_for_invalid_loop_edge_reference(self):
        graph = {**self.valid_graph}
        graph["loops"] = [dict(self.valid_graph["loops"][0])]
        graph["loops"][0]["edges"] = [0, "bad", 2, 3]

        with self.assertRaises(TopologyValidationError):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains invalid edge reference", report["error"])

    def test_logical_connector_closes_effective_topology_without_changing_physical_integrity(self):
        graph = {
            **self.valid_graph,
            "nodes": [
                *self.valid_graph["nodes"],
                {"id": 4, "x": 20.0, "y": 0.0, "degree": 1, "type": "endpoint"},
                {"id": 5, "x": 20.0, "y": 10.0, "degree": 1, "type": "endpoint"},
            ],
            "edges": [
                *self.valid_graph["edges"],
                {"id": 4, "from": 4, "to": 5, "length": 10.0, "angle": 90.0},
            ],
            "logical_connectors": [
                {
                    "id": "ag04-validator-valid-a",
                    "role": "DOOR_PORTAL",
                    "physical": False,
                    "from": 1,
                    "to": 4,
                    "host_edge_ids": [1, 4],
                    "source_primitive_id": "door-source-a",
                    "source_layer_normalized": "kapi",
                    "evidence_class": "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS",
                    "length_mm": 10.0,
                },
                {
                    "id": "ag04-validator-valid-b",
                    "role": "WINDOW_OPENING",
                    "physical": False,
                    "from": 2,
                    "to": 5,
                    "host_edge_ids": [2, 4],
                    "source_primitive_id": "window-source-b",
                    "source_layer_normalized": "pencere",
                    "evidence_class": "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS",
                    "length_mm": 10.0,
                },
            ],
        }

        physical_edges_before = [dict(edge) for edge in graph["edges"]]
        self.assertTrue(self.validator.validate(graph))

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(graph["edges"], physical_edges_before)
        self.assertEqual(report["counts"]["edges"], 5)
        self.assertEqual(report["counts"]["physical_edges"], 5)
        self.assertEqual(report["counts"]["logical_connectors"], 2)
        self.assertEqual(report["counts"]["effective_edges"], 7)
        self.assertTrue(report["checks"]["logical_connector_integrity"])

    def test_malformed_logical_connector_fails_before_effective_projection(self):
        graph = {
            **self.valid_graph,
            "logical_connectors": [
                {
                    "id": "ag04-validator-invalid",
                    "role": "DOOR_PORTAL",
                    "physical": True,
                    "from": 0,
                    "to": 1,
                    "host_edge_ids": [0, 1],
                    "source_primitive_id": "door-source",
                    "source_layer_normalized": "kapi",
                    "evidence_class": "EXACT_SOURCE_SPAN_WITH_TWO_UNIQUE_PARALLEL_HOSTS",
                    "length_mm": 10.0,
                }
            ],
        }

        with self.assertRaisesRegex(TopologyValidationError, "CONNECTOR_MUST_BE_NON_PHYSICAL"):
            self.validator.validate(graph)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["counts"]["edges"], 4)
        self.assertEqual(report["counts"]["physical_edges"], 4)
        self.assertEqual(report["counts"]["logical_connectors"], 0)
        self.assertEqual(report["counts"]["effective_edges"], 4)
        self.assertIn(
            "{'connector_id': 'ag04-validator-invalid', 'reason': 'CONNECTOR_MUST_BE_NON_PHYSICAL'}",
            report["error"],
        )

    def test_no_connector_evidence_preserves_legacy_report_shape(self):
        self.assertTrue(self.validator.validate(self.valid_graph))

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["counts"], {"nodes": 4, "edges": 4, "loops": 1})
        self.assertNotIn("logical_connector_integrity", report["checks"])


if __name__ == "__main__":
    unittest.main()