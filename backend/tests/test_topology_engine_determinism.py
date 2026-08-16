import inspect
import itertools
import json
import math
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from backend.config import ConfigManager
from backend.topology_engine import TopologyEngine
from backend.topology_health_report import TopologyHealthReporter


class TestTopologyEngineDeterminism(unittest.TestCase):
    def _wall_permutations_and_directions(self, walls):
        for wall_order in itertools.permutations(walls):
            for reversals in itertools.product((False, True), repeat=len(walls)):
                yield [
                    {
                        **wall,
                        "points": list(reversed(wall["points"])) if reverse else list(wall["points"]),
                    }
                    for wall, reverse in zip(wall_order, reversals)
                ]

    def _stable_stats(self, stats):
        return {
            key: value
            for key, value in stats.items()
            if key != "processing_time_ms"
        }

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

    def _run_engine_with_stats(self, walls, snap_tolerance=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            outputs_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)

            walls_path = os.path.join(outputs_dir, "walls_clean.json")
            with open(walls_path, "w", encoding="utf-8") as handle:
                json.dump(walls, handle, indent=2)

            engine = TopologyEngine()
            if snap_tolerance is not None:
                engine.snap_tolerance = snap_tolerance
            engine.path_manager = types.SimpleNamespace(
                get_path=lambda *parts: os.path.join(temp_dir, *parts),
                get_relative_path=lambda path: path,
            )

            graph = engine.run()
            return graph, dict(engine.stats)

    def _run_engine_with_final_projection_trace(self, walls, snap_tolerance=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            outputs_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)

            walls_path = os.path.join(outputs_dir, "walls_clean.json")
            with open(walls_path, "w", encoding="utf-8") as handle:
                json.dump(walls, handle, indent=2)

            engine = TopologyEngine()
            if snap_tolerance is not None:
                engine.snap_tolerance = snap_tolerance
            engine.path_manager = types.SimpleNamespace(
                get_path=lambda *parts: os.path.join(temp_dir, *parts),
                get_relative_path=lambda path: path,
            )

            projection_calls = []
            original_project = engine._project_pt_to_line

            def traced_project(point, target_start, target_end):
                result = original_project(point, target_start, target_end)
                projection_calls.append((point, target_start, target_end, result))
                return result

            engine._project_pt_to_line = traced_project
            graph = engine.run()
            accepted_count = engine.stats["t_junctions_snapped"]
            final_projection_calls = projection_calls[-accepted_count:] if accepted_count else []
            return graph, dict(engine.stats), final_projection_calls, engine.min_segment_length

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

    def test_rotated_near_collinear_t_junctions_explicitly_split_target_segments(self):
        walls_a = [
            {"wall_id": 1, "layer": "A-WALL", "points": [[-195471.0, 13998635.0], [0.0, 0.0]]},
            {"wall_id": 2, "layer": "A-WALL", "points": [[19802580.0, 14277879.0], [-195471.0, 13998635.0]]},
            {"wall_id": 3, "layer": "A-WALL", "points": [[0.0, 0.0], [19998050.0, 279244.0]]},
            {"wall_id": 4, "layer": "A-WALL", "points": [[6666017.0, 93081.0], [6470546.0, 14091717.0]]},
            {"wall_id": 5, "layer": "A-WALL", "points": [[13332034.0, 186162.0], [13136563.0, 14184798.0]]},
            {"wall_id": 6, "layer": "A-WALL", "points": [[19998050.0, 279244.0], [19802580.0, 14277879.0]]},
        ]
        walls_b = [
            {**wall, "wall_id": 100 + index, "points": list(reversed(wall["points"]))}
            for index, wall in enumerate(reversed(walls_a))
        ]

        graph_a, stats_a = self._run_engine_with_stats(walls_a)
        graph_b, stats_b = self._run_engine_with_stats(walls_b)

        self.assertEqual(graph_a, graph_b)
        self.assertEqual(stats_a["topology_sha256"], stats_b["topology_sha256"])
        self.assertEqual(stats_a["t_junctions_snapped"], 4)
        self.assertEqual(stats_a["T_nodes_count"], 4)
        self.assertEqual(stats_a["final_nodes"], 8)
        self.assertEqual(stats_a["final_edges"], 10)
        self.assertEqual(stats_a["closed_loops_found"], 3)
        self.assertFalse(any(node["degree"] == 1 for node in graph_a["nodes"]))

    def test_exact_tie_target_selection_is_publicly_deterministic_for_all_permutations(self):
        walls = [
            {"wall_id": 401, "layer": "duvar", "points": [[-10.0, 0.0], [10.0, 0.0]]},
            {"wall_id": 402, "layer": "duvar", "points": [[-5.0, 0.0], [15.0, 0.0]]},
            {"wall_id": 403, "layer": "duvar", "points": [[0.0, 0.5], [0.0, 5.0]]},
        ]

        baseline_graph = None
        baseline_stats = None
        variants = 0
        for variant in self._wall_permutations_and_directions(walls):
            graph, stats = self._run_engine_with_stats(variant, snap_tolerance=1.0)
            stable_stats = self._stable_stats(stats)
            if baseline_graph is None:
                baseline_graph = graph
                baseline_stats = stable_stats
            else:
                self.assertEqual(graph, baseline_graph)
                self.assertEqual(stable_stats, baseline_stats)
            variants += 1

        self.assertEqual(variants, 48)
        self.assertEqual(baseline_stats["t_junctions_snapped"], 1)
        self.assertEqual(baseline_stats["T_nodes_count"], 1)
        self.assertEqual(baseline_stats["closed_loops_found"], 0)

    def test_multiple_near_equal_target_projections_preserve_planar_contract(self):
        separations = {
            "below_minimum": 0.5,
            "equal_minimum": 1.0,
            "above_minimum": 1.5,
            "numerically_near_equal": 1e-7,
        }

        for case_name, separation in separations.items():
            walls = [
                {"wall_id": 501, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]]},
                {"wall_id": 502, "layer": "duvar", "points": [[5.0, 0.5], [5.0, 5.0]]},
                {"wall_id": 503, "layer": "duvar", "points": [[5.0 + separation, 0.5], [5.0 + separation, 5.0]]},
            ]
            baseline_graph = None
            baseline_stats = None
            variants = 0

            for variant in self._wall_permutations_and_directions(walls):
                graph, stats = self._run_engine_with_stats(variant, snap_tolerance=1.0)
                stable_stats = self._stable_stats(stats)
                if baseline_graph is None:
                    baseline_graph = graph
                    baseline_stats = stable_stats
                else:
                    self.assertEqual(graph, baseline_graph, case_name)
                    self.assertEqual(stable_stats, baseline_stats, case_name)
                variants += 1

            with self.subTest(case=case_name):
                self.assertEqual(variants, 48)
                self.assertEqual(baseline_stats["t_junctions_snapped"], 2)
                self.assertEqual(baseline_stats["closed_loops_found"], 0)
                self.assertFalse(any(edge["from"] == edge["to"] for edge in baseline_graph["edges"]))
                edge_pairs = [tuple(sorted((edge["from"], edge["to"]))) for edge in baseline_graph["edges"]]
                self.assertEqual(len(edge_pairs), len(set(edge_pairs)))
                accepted_x = {round(5.0, 3), round(5.0 + separation, 3)}
                junction_nodes = [
                    node
                    for node in baseline_graph["nodes"]
                    if node["y"] == 0.0 and node["x"] in accepted_x
                ]
                self.assertEqual(len(junction_nodes), len(accepted_x))
                self.assertTrue(all(node["degree"] >= 2 for node in junction_nodes))

    def test_below_minimum_noded_target_subedge_preserves_connectivity_for_all_permutations(self):
        walls = [
            {"wall_id": 511, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]]},
            {"wall_id": 512, "layer": "duvar", "points": [[5.0, 0.5], [5.0, 5.0]]},
            {"wall_id": 513, "layer": "duvar", "points": [[5.5, 0.5], [5.5, 5.0]]},
        ]

        baseline_graph = None
        baseline_stats = None
        variants = 0
        for variant in self._wall_permutations_and_directions(walls):
            graph, stats = self._run_engine_with_stats(variant, snap_tolerance=1.0)
            stable_stats = self._stable_stats(stats)
            if baseline_graph is None:
                baseline_graph = graph
                baseline_stats = stable_stats
            else:
                self.assertEqual(graph, baseline_graph)
                self.assertEqual(stable_stats, baseline_stats)
            variants += 1

        self.assertEqual(variants, 48)
        self.assertEqual(baseline_stats["t_junctions_snapped"], 2)
        self.assertEqual(baseline_stats["T_nodes_count"], 2)

        nodes_by_coordinate = {
            (node["x"], node["y"]): node
            for node in baseline_graph["nodes"]
        }
        first_junction = nodes_by_coordinate[(5.0, 0.0)]
        second_junction = nodes_by_coordinate[(5.5, 0.0)]
        self.assertEqual(first_junction["degree"], 3)
        self.assertEqual(second_junction["degree"], 3)

        nodes_by_id = {node["id"]: node for node in baseline_graph["nodes"]}
        edge_coordinates = {
            frozenset(
                (
                    (nodes_by_id[edge["from"]]["x"], nodes_by_id[edge["from"]]["y"]),
                    (nodes_by_id[edge["to"]]["x"], nodes_by_id[edge["to"]]["y"]),
                )
            )
            for edge in baseline_graph["edges"]
        }
        self.assertIn(frozenset(((5.0, 0.0), (5.5, 0.0))), edge_coordinates)

        target_adjacency = {coordinate: set() for coordinate in nodes_by_coordinate}
        for edge in baseline_graph["edges"]:
            start = (nodes_by_id[edge["from"]]["x"], nodes_by_id[edge["from"]]["y"])
            end = (nodes_by_id[edge["to"]]["x"], nodes_by_id[edge["to"]]["y"])
            if start[1] == 0.0 and end[1] == 0.0:
                target_adjacency[start].add(end)
                target_adjacency[end].add(start)

        reachable = {(0.0, 0.0)}
        pending = [(0.0, 0.0)]
        while pending:
            current = pending.pop()
            for neighbor in target_adjacency[current] - reachable:
                reachable.add(neighbor)
                pending.append(neighbor)
        self.assertIn((10.0, 0.0), reachable)

    def test_final_reprojection_can_clamp_outside_strict_interior_contract(self):
        walls = [
            {"wall_id": 521, "layer": "duvar", "points": [[0.5, 2.0], [-2.0, -1.0]]},
            {"wall_id": 522, "layer": "duvar", "points": [[0.0, 2.0], [0.5, -0.5]]},
        ]

        graph, stats, final_calls, _ = self._run_engine_with_final_projection_trace(
            walls,
            snap_tolerance=1.1,
        )

        self.assertEqual(stats["t_junctions_snapped"], 2)
        self.assertEqual(len(final_calls), 2)
        self.assertEqual(
            [(node["x"], node["y"], node["degree"]) for node in graph["nodes"]],
            [(-2.0, -1.0, 1), (0.019, 1.904, 2), (0.295, 1.754, 2), (0.5, -0.5, 1)],
        )
        self.assertEqual(
            [(edge["from"], edge["to"], edge["length"]) for edge in graph["edges"]],
            [(0, 1, 3.537), (1, 2, 0.314), (2, 3, 2.263)],
        )
        self.assertEqual(
            [result[2] for *_, result in final_calls],
            [-0.0769230769230769, -0.009765501946800082],
        )
        self.assertEqual(stats["filtered_short_segments"], 0)

    def test_final_reprojection_can_observe_a_collapsed_target(self):
        walls = [
            {"wall_id": 531, "layer": "duvar", "points": [[1.0, 0.5], [-1.0, 0.0]]},
            {"wall_id": 532, "layer": "duvar", "points": [[-1.0, 4.0], [0.0, 0.0]]},
        ]

        graph, stats, final_calls, _ = self._run_engine_with_final_projection_trace(
            walls,
            snap_tolerance=1.1,
        )

        self.assertEqual(stats["t_junctions_snapped"], 3)
        self.assertEqual(len(final_calls), 3)
        self.assertEqual(len(graph["nodes"]), 2)
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual([result[2] for *_, result in final_calls], [1.0, 1.0, 0.0])
        self.assertEqual(final_calls[2][1], final_calls[2][2])

    def test_final_reprojection_can_observe_a_below_minimum_target(self):
        walls = [
            {"wall_id": 541, "layer": "duvar", "points": [[4.0, 2.5], [3.0, 1.0]]},
            {"wall_id": 542, "layer": "duvar", "points": [[3.5, 0.5], [2.5, 2.0]]},
        ]

        graph, stats, final_calls, minimum_length = self._run_engine_with_final_projection_trace(
            walls,
            snap_tolerance=1.1,
        )

        self.assertEqual(stats["t_junctions_snapped"], 2)
        self.assertEqual(len(final_calls), 2)
        self.assertEqual(
            [(node["x"], node["y"], node["degree"]) for node in graph["nodes"]],
            [(3.341, 1.441, 2), (3.374, 1.129, 2), (3.5, 0.5, 1), (4.0, 2.5, 1)],
        )
        self.assertEqual(
            [(edge["from"], edge["to"], edge["length"]) for edge in graph["edges"]],
            [(0, 1, 0.314), (0, 3, 1.247), (1, 2, 0.641)],
        )
        self.assertLess(
            math.dist(final_calls[0][1], final_calls[0][2]),
            minimum_length,
        )
        self.assertEqual(stats["filtered_short_segments"], 0)

    def test_target_endpoint_snap_and_interior_projection_remain_collinear_for_all_permutations(self):
        walls = [
            {"wall_id": 601, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]]},
            {"wall_id": 602, "layer": "duvar", "points": [[5.0, 0.5], [5.0, 5.0]]},
            {"wall_id": 603, "layer": "duvar", "points": [[-2.0, -1.0], [1.0, 2.0]]},
        ]

        baseline_graph = None
        baseline_stats = None
        variants = 0
        for variant in self._wall_permutations_and_directions(walls):
            graph, stats = self._run_engine_with_stats(variant, snap_tolerance=1.0)
            stable_stats = self._stable_stats(stats)
            if baseline_graph is None:
                baseline_graph = graph
                baseline_stats = stable_stats
            else:
                self.assertEqual(graph, baseline_graph)
                self.assertEqual(stable_stats, baseline_stats)
            variants += 1

        self.assertEqual(variants, 48)
        self.assertEqual(baseline_stats["t_junctions_snapped"], 2)
        self.assertEqual(baseline_stats["closed_loops_found"], 0)

        nodes_by_id = {node["id"]: node for node in baseline_graph["nodes"]}
        dangling_coordinates = {
            (node["x"], node["y"])
            for node in baseline_graph["nodes"]
            if node["degree"] == 1
        }
        self.assertEqual(
            dangling_coordinates,
            {(-2.0, -1.0), (1.0, 2.0), (5.0, 5.0), (10.0, 0.0)},
        )

        branch_terminal = next(
            node
            for node in baseline_graph["nodes"]
            if (node["x"], node["y"]) == (5.0, 5.0)
        )
        branch_edge = next(
            edge
            for edge in baseline_graph["edges"]
            if branch_terminal["id"] in (edge["from"], edge["to"])
        )
        junction_id = (
            branch_edge["to"]
            if branch_edge["from"] == branch_terminal["id"]
            else branch_edge["from"]
        )
        junction = nodes_by_id[junction_id]
        self.assertEqual(junction["degree"], 3)

        incident_edges = [
            edge
            for edge in baseline_graph["edges"]
            if junction["id"] in (edge["from"], edge["to"])
        ]
        self.assertIn(branch_edge, incident_edges)
        target_edges = [edge for edge in incident_edges if edge is not branch_edge]
        self.assertEqual(len(target_edges), 2)
        target_angles = sorted(edge["angle"] % 180.0 for edge in target_edges)
        self.assertAlmostEqual(target_angles[0], target_angles[1], places=1)

    def test_topology_snap_tolerance_source_prefers_config_and_defaults_to_5mm(self):
        with patch.object(
            ConfigManager,
            "get",
            side_effect=lambda key, default=None: 0.125 if key == "tolerances.snapping_distance_mm" else default,
        ):
            configured_engine = TopologyEngine()

        with patch.object(ConfigManager, "get", side_effect=lambda key, default=None: default):
            default_engine = TopologyEngine()

        self.assertEqual(configured_engine.snap_tolerance, 0.125)
        self.assertEqual(default_engine.snap_tolerance, 5.0)

    def test_topology_t_junction_production_code_uses_strict_distance_comparison(self):
        init_source = inspect.getsource(TopologyEngine.__init__).replace(" ", "")
        run_source = inspect.getsource(TopologyEngine.run).replace(" ", "")

        self.assertIn(
            'self.snap_tolerance=self.config.get("tolerances.snapping_distance_mm",5.0)',
            init_source,
        )
        self.assertIn("0.001<t<0.999", run_source)
        self.assertIn("1e-4<d<self.snap_tolerance", run_source)

    def test_t_junction_boundary_contract_below_equal_above_tolerance_is_deterministic(self):
        snap_tolerance = 0.125
        cases = {
            "below": {
                "offset": 0.0625,
                "expected_hash": "6ff1b3d962546c046bb851ed968c4d5ff4d5b2c2276954918d8e1840b2569513",
                "expected_t_junctions_snapped": 1,
                "expected_T_nodes_count": 1,
                "expected_nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0, "degree": 1, "type": "end"},
                    {"id": 1, "x": 5.0, "y": 0.0, "degree": 3, "type": "T"},
                    {"id": 2, "x": 5.0, "y": 5.0, "degree": 1, "type": "end"},
                    {"id": 3, "x": 10.0, "y": 0.0, "degree": 1, "type": "end"},
                ],
                "expected_edges": [
                    {"id": 0, "from": 0, "to": 1, "length": 5.0, "angle": 0.0},
                    {"id": 1, "from": 1, "to": 2, "length": 5.0, "angle": 90.0},
                    {"id": 2, "from": 1, "to": 3, "length": 5.0, "angle": 0.0},
                ],
                "expected_counts": {"nodes": 4, "edges": 3, "loops": 0},
            },
            "equal": {
                "offset": 0.125,
                "expected_hash": "70e62d6ad5c42802adeb73d47b05c849f2fa06014ef4342d649adf6750ce20e7",
                "expected_t_junctions_snapped": 0,
                "expected_T_nodes_count": 0,
                "expected_nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0, "degree": 1, "type": "end"},
                    {"id": 1, "x": 5.0, "y": 0.125, "degree": 1, "type": "end"},
                    {"id": 2, "x": 5.0, "y": 5.0, "degree": 1, "type": "end"},
                    {"id": 3, "x": 10.0, "y": 0.0, "degree": 1, "type": "end"},
                ],
                "expected_edges": [
                    {"id": 0, "from": 0, "to": 3, "length": 10.0, "angle": 0.0},
                    {"id": 1, "from": 1, "to": 2, "length": 4.875, "angle": 90.0},
                ],
                "expected_counts": {"nodes": 4, "edges": 2, "loops": 0},
            },
            "above": {
                "offset": 0.1875,
                "expected_hash": "f5596c974d5474403826cbcdf7a9814d68ace530f54deb4666fca7fb335c2165",
                "expected_t_junctions_snapped": 0,
                "expected_T_nodes_count": 0,
                "expected_nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0, "degree": 1, "type": "end"},
                    {"id": 1, "x": 5.0, "y": 0.188, "degree": 1, "type": "end"},
                    {"id": 2, "x": 5.0, "y": 5.0, "degree": 1, "type": "end"},
                    {"id": 3, "x": 10.0, "y": 0.0, "degree": 1, "type": "end"},
                ],
                "expected_edges": [
                    {"id": 0, "from": 0, "to": 3, "length": 10.0, "angle": 0.0},
                    {"id": 1, "from": 1, "to": 2, "length": 4.812, "angle": 90.0},
                ],
                "expected_counts": {"nodes": 4, "edges": 2, "loops": 0},
            },
        }

        for case_name, case in cases.items():
            walls = [
                {"wall_id": 301, "layer": "duvar", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 25.0},
                {"wall_id": 302, "layer": "duvar", "points": [[5.0, case["offset"]], [5.0, 5.0]], "thickness": 25.0},
            ]

            with self.subTest(case=case_name):
                graph_first, stats_first = self._run_engine_with_stats(walls, snap_tolerance=snap_tolerance)
                graph_second, stats_second = self._run_engine_with_stats(walls, snap_tolerance=snap_tolerance)

                self.assertEqual(graph_first, graph_second)
                self.assertEqual(stats_first["topology_sha256"], stats_second["topology_sha256"])
                self.assertEqual(stats_first["topology_sha256"], case["expected_hash"])
                self.assertEqual(stats_first["t_junctions_snapped"], case["expected_t_junctions_snapped"])
                self.assertEqual(stats_first["T_nodes_count"], case["expected_T_nodes_count"])
                self.assertEqual(stats_first["final_nodes"], case["expected_counts"]["nodes"])
                self.assertEqual(stats_first["final_edges"], case["expected_counts"]["edges"])
                self.assertEqual(stats_first["closed_loops_found"], case["expected_counts"]["loops"])
                self.assertEqual(graph_first["nodes"], case["expected_nodes"])
                self.assertEqual(graph_first["edges"], case["expected_edges"])
                self.assertEqual(graph_first["loops"], [])

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