import json
import os
import tempfile
import types
import unittest

from backend.constraint_solver import ConstraintSolver


class TestConstraintSolver(unittest.TestCase):
    def test_run_persists_resolved_graph_and_preserves_loop_contract(self):
        solver = ConstraintSolver()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "geometry_graph_resolved.json")
            solver.path_manager = types.SimpleNamespace(
                get_path=lambda dir_key, filename=None: output_path,
                get_relative_path=lambda path: path,
            )

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


if __name__ == "__main__":
    unittest.main()