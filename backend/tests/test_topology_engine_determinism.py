import json
import os
import sys
import tempfile
import types
import unittest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from backend.topology_engine import TopologyEngine
from backend.topology_health_report import TopologyHealthReporter


class TestTopologyEngineDeterminism(unittest.TestCase):
    def _run_engine(self, walls):
        with tempfile.TemporaryDirectory() as temp_dir:
            outputs_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)

            walls_path = os.path.join(outputs_dir, "walls_clean.json")
            with open(walls_path, "w", encoding="utf-8") as handle:
                json.dump(walls, handle, indent=2)

            engine = TopologyEngine()
            engine.path_manager = types.SimpleNamespace(
                get_path=lambda *parts: os.path.join(temp_dir, *parts),
                get_relative_path=lambda path: path,
            )

            graph = engine.run()
            return graph, engine.stats["topology_sha256"]

    def _generate_health_report(self, graph):
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = TopologyHealthReporter(
                report_output_path=os.path.join(temp_dir, "topology_health_report.json")
            )
            return reporter.generate(graph)

    def test_run_is_deterministic_across_wall_order_and_direction_permutations(self):
        walls_a = [
            {"wall_id": 10, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 11, "layer": "duvar", "points": [[0.0, 10.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 12, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 13, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
        ]
        walls_b = [
            {"wall_id": 99, "layer": "duvar", "points": [[10.0, 10.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 98, "layer": "duvar", "points": [[0.0, 0.0], [0.0, 10.0]], "thickness": 25.0},
            {"wall_id": 97, "layer": "duvar", "points": [[10.0, 10.0], [0.0, 10.0]], "thickness": 25.0},
            {"wall_id": 96, "layer": "duvar", "points": [[10.0, 0.0], [0.0, 0.0]], "thickness": 25.0},
        ]

        graph_a, sha_a = self._run_engine(walls_a)
        graph_b, sha_b = self._run_engine(walls_b)

        self.assertEqual(graph_a, graph_b)
        self.assertEqual(sha_a, sha_b)
        self.assertEqual(
            graph_a["nodes"],
            [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2, "type": "L_corner"},
                {"id": 1, "x": 0.0, "y": 10.0, "degree": 2, "type": "L_corner"},
                {"id": 2, "x": 10.0, "y": 0.0, "degree": 2, "type": "L_corner"},
                {"id": 3, "x": 10.0, "y": 10.0, "degree": 2, "type": "L_corner"},
            ],
        )
        self.assertEqual(
            graph_a["edges"],
            [
                {"id": 0, "from": 0, "to": 1, "length": 10.0, "angle": 90.0},
                {"id": 1, "from": 0, "to": 2, "length": 10.0, "angle": 0.0},
                {"id": 2, "from": 1, "to": 3, "length": 10.0, "angle": 0.0},
                {"id": 3, "from": 2, "to": 3, "length": 10.0, "angle": 90.0},
            ],
        )
        self.assertEqual(
            graph_a["loops"],
            [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [0, 1, 2, 3],
                    "boundary": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 0.0, "y": 10.0},
                        {"x": 10.0, "y": 10.0},
                        {"x": 10.0, "y": 0.0},
                        {"x": 0.0, "y": 0.0},
                    ],
                }
            ],
        )

    def test_closed_square_graph_produces_healthy_topology_health_report(self):
        walls = [
            {"wall_id": 10, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 11, "layer": "duvar", "points": [[0.0, 10.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 12, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 13, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
        ]

        graph, _ = self._run_engine(walls)
        report = self._generate_health_report(graph)

        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["counts"], {"nodes": 4, "edges": 4, "loops": 1})
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual(report["graph_metrics"]["degree_metadata_mismatches"], [])
        self.assertTrue(report["checks"]["degree_metadata_consistency"])
        self.assertTrue(report["checks"]["no_dangling_nodes"])
        self.assertTrue(report["checks"]["closed_loops"])

    def test_single_segment_graph_reports_only_sparse_input_warnings(self):
        walls = [
            {"wall_id": 201, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
        ]

        graph, _ = self._run_engine(walls)
        report = self._generate_health_report(graph)

        self.assertEqual(report["status"], "WARNING")
        self.assertEqual(report["counts"], {"nodes": 2, "edges": 1, "loops": 0})
        self.assertEqual(report["graph_metrics"]["connected_components"], 1)
        self.assertEqual(report["graph_metrics"]["degree_metadata_mismatches"], [])
        self.assertTrue(report["checks"]["degree_metadata_consistency"])
        self.assertFalse(report["checks"]["has_loops"])
        self.assertFalse(report["checks"]["no_dangling_nodes"])
        self.assertEqual(
            [diagnostic["code"] for diagnostic in report["diagnostics"]],
            ["ZERO_LOOPS", "DANGLING_NODES"],
        )

    def test_run_resets_stats_when_same_engine_instance_is_reused(self):
        walls = [
            {"wall_id": 10, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 11, "layer": "duvar", "points": [[0.0, 10.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 12, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 13, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            outputs_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)

            walls_path = os.path.join(outputs_dir, "walls_clean.json")
            with open(walls_path, "w", encoding="utf-8") as handle:
                json.dump(walls, handle, indent=2)

            engine = TopologyEngine()
            engine.path_manager = types.SimpleNamespace(
                get_path=lambda *parts: os.path.join(temp_dir, *parts),
                get_relative_path=lambda path: path,
            )

            graph_first = engine.run()
            stats_first = dict(engine.stats)
            graph_second = engine.run()
            stats_second = dict(engine.stats)

        self.assertEqual(graph_first, graph_second)
        self.assertEqual(stats_first["topology_sha256"], stats_second["topology_sha256"])
        self.assertEqual(stats_second["final_nodes"], 4)
        self.assertEqual(stats_second["final_edges"], 4)
        self.assertEqual(stats_second["closed_loops_found"], 1)
        self.assertEqual(stats_second["L_corner_nodes_count"], 4)
        self.assertEqual(stats_second["straight_nodes_count"], 0)
        self.assertEqual(stats_second["T_nodes_count"], 0)
        self.assertEqual(stats_second["X_nodes_count"], 0)
        self.assertEqual(stats_second["t_junctions_snapped"], 0)

    def test_duplicate_and_degenerate_segments_do_not_create_duplicate_edges(self):
        walls = [
            {"wall_id": 10, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 11, "layer": "duvar", "points": [[0.0, 10.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 12, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 13, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
            {"wall_id": 14, "layer": "duvar", "points": [[10.0, 0.0], [0.0, 0.0]], "thickness": 25.0},
            {"wall_id": 15, "layer": "duvar", "points": [[5.0, 5.0], [5.0, 5.0]], "thickness": 25.0},
        ]

        graph, _ = self._run_engine(walls)

        self.assertEqual(len(graph["edges"]), 4)
        self.assertEqual(len(graph["loops"]), 1)

        undirected_pairs = {
            tuple(sorted((edge["from"], edge["to"])))
            for edge in graph["edges"]
        }

        self.assertEqual(len(undirected_pairs), len(graph["edges"]))
        self.assertTrue(all(edge["from"] != edge["to"] for edge in graph["edges"]))

    def test_t_junction_graph_is_deterministic_despite_duplicate_backtracking_wall(self):
        walls_a = [
            {"wall_id": 21, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 22, "layer": "duvar", "points": [[5.0, 5.0], [5.0, 0.0]], "thickness": 25.0},
            {"wall_id": 23, "layer": "duvar", "points": [[10.0, 0.0], [0.0, 0.0]], "thickness": 25.0},
        ]
        walls_b = [
            {"wall_id": 31, "layer": "duvar", "points": [[5.0, 0.0], [5.0, 5.0]], "thickness": 25.0},
            {"wall_id": 32, "layer": "duvar", "points": [[10.0, 0.0], [0.0, 0.0]], "thickness": 25.0},
            {"wall_id": 33, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
        ]

        graph_a, sha_a = self._run_engine(walls_a)
        graph_b, sha_b = self._run_engine(walls_b)

        self.assertEqual(graph_a, graph_b)
        self.assertEqual(sha_a, sha_b)
        self.assertEqual(len(graph_a["nodes"]), 4)
        self.assertEqual(len(graph_a["edges"]), 3)
        self.assertEqual(len(graph_a["loops"]), 0)

        t_nodes = [node for node in graph_a["nodes"] if node["type"] == "T"]
        self.assertEqual(len(t_nodes), 1)
        self.assertEqual(t_nodes[0]["degree"], 3)

        undirected_pairs = {
            tuple(sorted((edge["from"], edge["to"])))
            for edge in graph_a["edges"]
        }
        self.assertEqual(len(undirected_pairs), len(graph_a["edges"]))

    def test_interior_projection_t_junction_is_snapped_and_counted_once(self):
        walls = [
            {"wall_id": 81, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 82, "layer": "duvar", "points": [[5.0, 0.8], [5.0, 5.0]], "thickness": 25.0},
        ]

        graph, sha = self._run_engine(walls)

        self.assertEqual(sha, "6ff1b3d962546c046bb851ed968c4d5ff4d5b2c2276954918d8e1840b2569513")
        self.assertEqual(
            graph["nodes"],
            [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 1, "type": "end"},
                {"id": 1, "x": 5.0, "y": 0.0, "degree": 3, "type": "T"},
                {"id": 2, "x": 5.0, "y": 5.0, "degree": 1, "type": "end"},
                {"id": 3, "x": 10.0, "y": 0.0, "degree": 1, "type": "end"},
            ],
        )
        self.assertEqual(
            graph["edges"],
            [
                {"id": 0, "from": 0, "to": 1, "length": 5.0, "angle": 0.0},
                {"id": 1, "from": 1, "to": 2, "length": 5.0, "angle": 90.0},
                {"id": 2, "from": 1, "to": 3, "length": 5.0, "angle": 0.0},
            ],
        )
        self.assertEqual(graph["loops"], [])

        with tempfile.TemporaryDirectory() as temp_dir:
            outputs_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)

            walls_path = os.path.join(outputs_dir, "walls_clean.json")
            with open(walls_path, "w", encoding="utf-8") as handle:
                json.dump(walls, handle, indent=2)

            engine = TopologyEngine()
            engine.path_manager = types.SimpleNamespace(
                get_path=lambda *parts: os.path.join(temp_dir, *parts),
                get_relative_path=lambda path: path,
            )

            rerun_graph = engine.run()

        self.assertEqual(rerun_graph, graph)
        self.assertEqual(engine.stats["t_junctions_snapped"], 1)
        self.assertEqual(engine.stats["T_nodes_count"], 1)
        self.assertEqual(engine.stats["final_nodes"], 4)
        self.assertEqual(engine.stats["final_edges"], 3)
        self.assertEqual(engine.stats["closed_loops_found"], 0)

    def test_collinear_segments_are_classified_with_single_straight_node_deterministically(self):
        walls_a = [
            {"wall_id": 61, "layer": "duvar", "points": [[0.0, 0.0], [5.0, 0.0]], "thickness": 25.0},
            {"wall_id": 62, "layer": "duvar", "points": [[5.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
        ]
        walls_b = [
            {"wall_id": 72, "layer": "duvar", "points": [[10.0, 0.0], [5.0, 0.0]], "thickness": 25.0},
            {"wall_id": 71, "layer": "duvar", "points": [[5.0, 0.0], [0.0, 0.0]], "thickness": 25.0},
        ]

        graph_a, sha_a = self._run_engine(walls_a)
        graph_b, sha_b = self._run_engine(walls_b)

        self.assertEqual(graph_a, graph_b)
        self.assertEqual(sha_a, sha_b)
        self.assertEqual(len(graph_a["nodes"]), 3)
        self.assertEqual(len(graph_a["edges"]), 2)
        self.assertEqual(len(graph_a["loops"]), 0)

        straight_nodes = [node for node in graph_a["nodes"] if node["type"] == "straight"]
        self.assertEqual(straight_nodes, [{"id": 1, "x": 5.0, "y": 0.0, "degree": 2, "type": "straight"}])

        end_nodes = [node for node in graph_a["nodes"] if node["type"] == "end"]
        self.assertEqual(len(end_nodes), 2)
        self.assertTrue(all(node["degree"] == 1 for node in end_nodes))

    def test_angle_threshold_separates_straight_from_l_corner_classification(self):
        near_straight_walls = [
            {"wall_id": 91, "layer": "duvar", "points": [[0.0, 0.0], [5.0, 0.0]], "thickness": 25.0},
            {"wall_id": 92, "layer": "duvar", "points": [[5.0, 0.0], [10.0, 1.0]], "thickness": 25.0},
        ]
        near_corner_walls = [
            {"wall_id": 93, "layer": "duvar", "points": [[0.0, 0.0], [5.0, 0.0]], "thickness": 25.0},
            {"wall_id": 94, "layer": "duvar", "points": [[5.0, 0.0], [10.0, 2.0]], "thickness": 25.0},
        ]

        near_straight_graph, _ = self._run_engine(near_straight_walls)
        near_corner_graph, _ = self._run_engine(near_corner_walls)

        self.assertEqual(
            [node for node in near_straight_graph["nodes"] if node["degree"] == 2],
            [{"id": 1, "x": 5.0, "y": 0.0, "degree": 2, "type": "straight"}],
        )
        self.assertEqual(
            [node for node in near_corner_graph["nodes"] if node["degree"] == 2],
            [{"id": 1, "x": 5.0, "y": 0.0, "degree": 2, "type": "L_corner"}],
        )

    def test_cross_intersection_is_classified_as_single_x_node_deterministically(self):
        walls_a = [
            {"wall_id": 71, "layer": "duvar", "points": [[0.0, 5.0], [10.0, 5.0]], "thickness": 25.0},
            {"wall_id": 72, "layer": "duvar", "points": [[5.0, 0.0], [5.0, 10.0]], "thickness": 25.0},
        ]
        walls_b = [
            {"wall_id": 82, "layer": "duvar", "points": [[5.0, 10.0], [5.0, 0.0]], "thickness": 25.0},
            {"wall_id": 81, "layer": "duvar", "points": [[10.0, 5.0], [0.0, 5.0]], "thickness": 25.0},
        ]

        graph_a, sha_a = self._run_engine(walls_a)
        graph_b, sha_b = self._run_engine(walls_b)

        self.assertEqual(graph_a, graph_b)
        self.assertEqual(sha_a, sha_b)
        self.assertEqual(len(graph_a["nodes"]), 5)
        self.assertEqual(len(graph_a["edges"]), 4)
        self.assertEqual(len(graph_a["loops"]), 0)

        x_nodes = [node for node in graph_a["nodes"] if node["type"] == "X"]
        self.assertEqual(x_nodes, [{"id": 2, "x": 5.0, "y": 5.0, "degree": 4, "type": "X"}])

        end_nodes = [node for node in graph_a["nodes"] if node["type"] == "end"]
        self.assertEqual(len(end_nodes), 4)
        self.assertTrue(all(node["degree"] == 1 for node in end_nodes))

    def test_near_degenerate_segment_collapsed_by_rounding_does_not_pollute_graph(self):
        walls = [
            {"wall_id": 41, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 42, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 43, "layer": "duvar", "points": [[10.0, 10.0], [0.0, 10.0]], "thickness": 25.0},
            {"wall_id": 44, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
            {"wall_id": 45, "layer": "duvar", "points": [[5.0004, 5.0004], [5.00049, 5.00049]], "thickness": 25.0},
        ]

        graph, _ = self._run_engine(walls)

        self.assertEqual(len(graph["nodes"]), 4)
        self.assertEqual(len(graph["edges"]), 4)
        self.assertEqual(len(graph["loops"]), 1)
        self.assertTrue(all(edge["length"] >= 10.0 for edge in graph["edges"]))

    def test_disconnected_equal_area_loops_are_canonically_ordered_across_input_permutations(self):
        walls_a = [
            {"wall_id": 51, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
            {"wall_id": 52, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 53, "layer": "duvar", "points": [[10.0, 10.0], [0.0, 10.0]], "thickness": 25.0},
            {"wall_id": 54, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
            {"wall_id": 55, "layer": "duvar", "points": [[30.0, 0.0], [40.0, 0.0]], "thickness": 25.0},
            {"wall_id": 56, "layer": "duvar", "points": [[40.0, 0.0], [40.0, 10.0]], "thickness": 25.0},
            {"wall_id": 57, "layer": "duvar", "points": [[40.0, 10.0], [30.0, 10.0]], "thickness": 25.0},
            {"wall_id": 58, "layer": "duvar", "points": [[30.0, 10.0], [30.0, 0.0]], "thickness": 25.0},
        ]
        walls_b = [
            {"wall_id": 68, "layer": "duvar", "points": [[30.0, 10.0], [30.0, 0.0]], "thickness": 25.0},
            {"wall_id": 67, "layer": "duvar", "points": [[40.0, 10.0], [30.0, 10.0]], "thickness": 25.0},
            {"wall_id": 66, "layer": "duvar", "points": [[40.0, 0.0], [40.0, 10.0]], "thickness": 25.0},
            {"wall_id": 65, "layer": "duvar", "points": [[40.0, 0.0], [30.0, 0.0]], "thickness": 25.0},
            {"wall_id": 64, "layer": "duvar", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 25.0},
            {"wall_id": 63, "layer": "duvar", "points": [[10.0, 10.0], [0.0, 10.0]], "thickness": 25.0},
            {"wall_id": 62, "layer": "duvar", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 25.0},
            {"wall_id": 61, "layer": "duvar", "points": [[10.0, 0.0], [0.0, 0.0]], "thickness": 25.0},
        ]

        graph_a, sha_a = self._run_engine(walls_a)
        graph_b, sha_b = self._run_engine(walls_b)

        self.assertEqual(graph_a, graph_b)
        self.assertEqual(sha_a, sha_b)
        self.assertEqual(len(graph_a["loops"]), 2)
        self.assertEqual([loop["area"] for loop in graph_a["loops"]], [100.0, 100.0])
        self.assertEqual(
            [loop["boundary"] for loop in graph_a["loops"]],
            [
                [
                    {"x": 0.0, "y": 0.0},
                    {"x": 0.0, "y": 10.0},
                    {"x": 10.0, "y": 10.0},
                    {"x": 10.0, "y": 0.0},
                    {"x": 0.0, "y": 0.0},
                ],
                [
                    {"x": 30.0, "y": 0.0},
                    {"x": 30.0, "y": 10.0},
                    {"x": 40.0, "y": 10.0},
                    {"x": 40.0, "y": 0.0},
                    {"x": 30.0, "y": 0.0},
                ],
            ],
        )


if __name__ == "__main__":
    unittest.main()