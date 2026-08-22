import json
import os
import tempfile
import types
import unittest

from backend.constraint_solver import ConstraintSolver


class TestConstraintSolver(unittest.TestCase):
    def _make_solver(self, output_path):
        solver = ConstraintSolver()
        solver.path_manager = types.SimpleNamespace(
            get_path=lambda dir_key, filename=None: output_path,
            get_relative_path=lambda path: path,
        )
        return solver

    def test_run_persists_resolved_graph_and_preserves_loop_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "geometry_graph_resolved.json")
            solver = self._make_solver(output_path)

            graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0},
                    {"id": 1, "x": 10.0, "y": 0.0},
                    {"id": 2, "x": 10.0, "y": 10.0},
                ],
                "edges": [
                    {"id": 1, "from": 0, "to": 1, "length": 10.0},
                    {"id": 2, "from": 1, "to": 0, "length": 10.0},
                    {"id": 3, "from": 1, "to": 2, "length": 10.0},
                ],
                "loops": [
                    {
                        "id": 0,
                        "area": 100.0,
                        "edges": [1, 3],
                        "boundary": [
                            {"x": 0.0, "y": 0.0},
                            {"x": 10.0, "y": 0.0},
                            {"x": 10.0, "y": 10.0},
                            {"x": 0.0, "y": 0.0},
                        ],
                    }
                ],
            }

            resolved = solver.run(graph)

            self.assertTrue(resolved["constraints_resolved"])
            self.assertEqual(resolved["initial_edge_count"], 3)
            self.assertEqual(resolved["resolved_edge_count"], 2)
            self.assertEqual([edge["id"] for edge in resolved["edges"]], [1, 3])
            self.assertEqual(resolved["loops"], graph["loops"])
            self.assertEqual(resolved["faces"], graph["loops"])

            with open(output_path, "r", encoding="utf-8") as handle:
                persisted = json.load(handle)

            self.assertEqual(persisted, resolved)

    def test_run_does_not_overwrite_topology_engine_geometry_graph_artifact(self):
        solver = ConstraintSolver()

        with tempfile.TemporaryDirectory() as temp_dir:
            topology_graph_path = os.path.join(temp_dir, "geometry_graph.json")
            resolved_graph_path = os.path.join(temp_dir, ConstraintSolver.RESOLVED_GRAPH_FILENAME)

            solver.path_manager = types.SimpleNamespace(
                get_path=lambda dir_key, filename=None: os.path.join(temp_dir, filename) if filename else temp_dir,
                get_relative_path=lambda path: path,
            )

            topology_graph = {
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
            }

            with open(topology_graph_path, "w", encoding="utf-8") as handle:
                json.dump(topology_graph, handle, indent=2)

            resolved = solver.run(
                {
                    **topology_graph,
                    "edges": topology_graph["edges"] + [
                        {"id": 4, "from": 1, "to": 0, "length": 10.0, "angle": 180.0},
                    ],
                }
            )

            with open(topology_graph_path, "r", encoding="utf-8") as handle:
                persisted_topology_graph = json.load(handle)

            with open(resolved_graph_path, "r", encoding="utf-8") as handle:
                persisted_resolved_graph = json.load(handle)

            self.assertEqual(persisted_topology_graph, topology_graph)
            self.assertEqual(persisted_resolved_graph, resolved)
            self.assertEqual(len(persisted_topology_graph["edges"]), 4)
            self.assertEqual(len(persisted_resolved_graph["edges"]), 4)
            self.assertTrue(persisted_resolved_graph["constraints_resolved"])

    def test_run_selects_duplicate_winner_deterministically_independent_of_input_order(self):
        graph_a = {
            "nodes": [{"id": 0}, {"id": 1}],
            "edges": [
                {"id": "B", "from": 1, "to": 0, "meta": "second"},
                {"id": "A", "from": 0, "to": 1, "meta": "first"},
            ],
            "loops": [],
        }
        graph_b = {
            **graph_a,
            "edges": list(reversed(graph_a["edges"])),
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_a = os.path.join(temp_dir, "resolved_a.json")
            output_b = os.path.join(temp_dir, "resolved_b.json")

            resolved_a = self._make_solver(output_a).run(graph_a)
            resolved_b = self._make_solver(output_b).run(graph_b)

            self.assertEqual(resolved_a["edges"], resolved_b["edges"])
            self.assertEqual(resolved_a["resolved_edge_count"], 1)
            self.assertEqual(resolved_b["resolved_edge_count"], 1)
            self.assertEqual(resolved_a["edges"][0]["id"], "A")
            self.assertEqual(resolved_a["edges"][0]["from"], 0)
            self.assertEqual(resolved_a["edges"][0]["to"], 1)

            with open(output_a, "r", encoding="utf-8") as handle:
                persisted_a = json.load(handle)
            with open(output_b, "r", encoding="utf-8") as handle:
                persisted_b = json.load(handle)

            self.assertEqual(persisted_a["edges"], persisted_b["edges"])

    def test_run_preserves_missing_node_reference_edges_but_filters_invalid_edge_shapes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "geometry_graph_resolved.json")
            solver = self._make_solver(output_path)

            resolved = solver.run(
                {
                    "nodes": [{"id": 0}, {"id": 1}],
                    "edges": [
                        {"id": "ok", "from": 0, "to": 1},
                        {"id": "missing_to", "from": 1, "to": 99},
                        {"id": "missing_from", "from": 42, "to": 0},
                        {"id": "self", "from": 0, "to": 0},
                        {"id": "null_to", "from": 0, "to": None},
                    ],
                    "loops": [],
                }
            )

            self.assertEqual(resolved["initial_edge_count"], 5)
            self.assertEqual(resolved["resolved_edge_count"], 3)
            self.assertEqual(
                [edge["id"] for edge in resolved["edges"]],
                ["ok", "missing_to", "missing_from"],
            )
            self.assertEqual(resolved["edges"][1]["to"], 99)
            self.assertEqual(resolved["edges"][2]["from"], 42)

    def test_run_keeps_logical_connectors_separate_from_physical_edges(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            solver = self._make_solver(os.path.join(temp_dir, "resolved.json"))
            physical_edges = [
                {"id": 10, "from": 0, "to": 1},
                {"id": 11, "from": 2, "to": 3},
            ]
            connector = {
                "id": "ag04-valid",
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

            resolved = solver.run(
                {
                    "nodes": [
                        {"id": 0, "x": 0.0, "y": 0.0},
                        {"id": 1, "x": 10.0, "y": 0.0},
                        {"id": 2, "x": 20.0, "y": 0.0},
                        {"id": 3, "x": 30.0, "y": 0.0},
                    ],
                    "edges": physical_edges,
                    "loops": [],
                    "logical_connectors": [connector],
                }
            )

            self.assertEqual(resolved["edges"], physical_edges)
            self.assertEqual(resolved["initial_edge_count"], 2)
            self.assertEqual(resolved["resolved_edge_count"], 2)
            self.assertEqual(resolved["logical_connectors"], [connector])
            self.assertEqual(resolved["logical_connector_rejections"], [])
            self.assertEqual(resolved["initial_logical_connector_count"], 1)
            self.assertEqual(resolved["resolved_logical_connector_count"], 1)

    def test_run_rejects_malformed_logical_connector_without_changing_edges(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            solver = self._make_solver(os.path.join(temp_dir, "resolved.json"))
            graph = {
                "nodes": [{"id": 0}, {"id": 1}],
                "edges": [{"id": 10, "from": 0, "to": 1}],
                "loops": [],
                "logical_connectors": [
                    {
                        "id": "ag04-invalid",
                        "role": "DOOR_PORTAL",
                        "physical": True,
                        "from": 0,
                        "to": 1,
                    }
                ],
            }

            resolved = solver.run(graph)

            self.assertEqual(resolved["edges"], graph["edges"])
            self.assertEqual(resolved["logical_connectors"], [])
            self.assertEqual(
                resolved["logical_connector_rejections"],
                [{"connector_id": "ag04-invalid", "reason": "CONNECTOR_MUST_BE_NON_PHYSICAL"}],
            )
            self.assertEqual(resolved["initial_logical_connector_count"], 1)
            self.assertEqual(resolved["resolved_logical_connector_count"], 0)

    def test_run_without_logical_connector_evidence_preserves_legacy_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            solver = self._make_solver(os.path.join(temp_dir, "resolved.json"))
            resolved = solver.run(
                {
                    "nodes": [{"id": 0}, {"id": 1}],
                    "edges": [{"id": 10, "from": 0, "to": 1}],
                    "loops": [],
                }
            )

            self.assertNotIn("logical_connectors", resolved)
            self.assertNotIn("logical_connector_rejections", resolved)
            self.assertNotIn("initial_logical_connector_count", resolved)
            self.assertNotIn("resolved_logical_connector_count", resolved)


if __name__ == "__main__":
    unittest.main()