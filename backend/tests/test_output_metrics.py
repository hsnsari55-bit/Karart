import json
import tempfile
import unittest
from pathlib import Path

from backend.output_metrics import build_metrics, compare_metrics


class TestOutputMetrics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.outputs_dir = self.base / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_path = self.base / "metrics.json"

        self._write_payloads(area=100.0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_payloads(self, area: float, loop_areas: list[float] | None = None) -> None:
        if loop_areas is None:
            loop_areas = [area]
        with (self.outputs_dir / "walls_clean.json").open("w", encoding="utf-8") as handle:
            json.dump(
                [
                    {"wall_id": 1, "points": [[0.0, 0.0], [3.0, 4.0]], "thickness": 25.0},
                    {"wall_id": 2, "points": [[3.0, 4.0], [3.0, 8.0]], "thickness": 25.0},
                ],
                handle,
                indent=2,
            )

        with (self.outputs_dir / "geometry_graph.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
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
                            "id": index,
                            "area": loop_area,
                            "edges": [0, 1, 2, 3],
                            "boundary": [
                                {"x": 0.0, "y": 0.0},
                                {"x": 10.0, "y": 0.0},
                                {"x": 10.0, "y": 10.0},
                                {"x": 0.0, "y": 10.0},
                                {"x": 0.0, "y": 0.0},
                            ],
                        }
                        for index, loop_area in enumerate(loop_areas)
                    ],
                },
                handle,
                indent=2,
            )

        with (self.outputs_dir / "bim_semantics.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "elements": [
                        {"type": "Wall"},
                        {"type": "Door"},
                        {"type": "Wall"},
                    ]
                },
                handle,
                indent=2,
            )

        with (self.outputs_dir / "spaces.json").open("w", encoding="utf-8") as handle:
            json.dump({"spaces": [{"space_id": "s1", "area": area}]}, handle, indent=2)

        with (self.outputs_dir / "bim_model.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "walls": [{"uuid": "w1"}, {"uuid": "w2"}],
                    "doors": [{"uuid": "d1"}],
                    "windows": [],
                    "columns": [],
                    "spaces": [{"uuid": "s1"}],
                },
                handle,
                indent=2,
            )

    def test_build_metrics_collects_deterministic_counts(self):
        metrics = build_metrics(self.outputs_dir)
        self.assertEqual(metrics["walls"]["count"], 2)
        self.assertEqual(metrics["walls"]["total_segment_length"], 9.0)
        self.assertEqual(metrics["graph"]["node_count"], 4)
        self.assertEqual(metrics["graph"]["edge_count"], 4)
        self.assertEqual(metrics["graph"]["loop_count"], 1)
        self.assertEqual(metrics["graph"]["loop_area_list"], [100.0])
        self.assertEqual(metrics["graph"]["total_loop_area"], 100.0)
        self.assertEqual(metrics["semantics"]["element_count"], 3)
        self.assertEqual(metrics["semantics"]["element_type_counts"], {"Door": 1, "Wall": 2})
        self.assertEqual(metrics["spaces"]["count"], 1)
        self.assertEqual(metrics["spaces"]["total_area"], 100.0)
        self.assertEqual(metrics["bim"]["wall_count"], 2)
        self.assertEqual(metrics["bim"]["door_count"], 1)
        self.assertEqual(metrics["topology_health"]["status"], "HEALTHY")
        self.assertEqual(metrics["topology_health"]["failed_checks"], [])
        self.assertEqual(metrics["topology_health"]["diagnostic_codes"], [])
        self.assertEqual(metrics["topology_health"]["graph_metrics"]["connected_components"], 1)
        self.assertEqual(metrics["topology_health"]["graph_metrics"]["dangling_node_count"], 0)
        self.assertEqual(metrics["topology_health"]["graph_metrics"]["degree_metadata_mismatch_count"], 0)
        self.assertEqual(metrics["topology_health"]["loop_metrics"]["closed_loop_count"], 1)
        self.assertEqual(metrics["topology_health"]["loop_metrics"]["open_loop_count"], 0)

    def test_compare_metrics_fails_when_topology_loop_area_changes(self):
        with self.snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(build_metrics(self.outputs_dir), handle, indent=2)

        with (self.outputs_dir / "geometry_graph.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "nodes": [{"id": 0}, {"id": 1}, {"id": 2}],
                    "edges": [{"id": 1}, {"id": 2}],
                    "loops": [{"id": 0, "area": 130.0}],
                },
                handle,
                indent=2,
            )

        with self.assertRaises(SystemExit):
            compare_metrics(self.snapshot_path, self.outputs_dir, verbose=False)

    def test_compare_metrics_fails_when_topology_loop_count_changes(self):
        with self.snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(build_metrics(self.outputs_dir), handle, indent=2)

        with (self.outputs_dir / "geometry_graph.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
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
                        },
                        {
                            "id": 1,
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
                    ],
                },
                handle,
                indent=2,
            )

        with self.assertRaises(SystemExit):
            compare_metrics(self.snapshot_path, self.outputs_dir, verbose=False)

    def test_compare_metrics_fails_when_loop_area_distribution_changes(self):
        self._write_payloads(area=100.0, loop_areas=[40.0, 60.0])
        with self.snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(build_metrics(self.outputs_dir), handle, indent=2)

        self._write_payloads(area=100.0, loop_areas=[30.0, 70.0])

        with self.assertRaises(SystemExit):
            compare_metrics(self.snapshot_path, self.outputs_dir, verbose=False)

    def test_compare_metrics_fails_when_topology_health_changes_without_count_drift(self):
        with self.snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(build_metrics(self.outputs_dir), handle, indent=2)

        with (self.outputs_dir / "geometry_graph.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "nodes": [
                        {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
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
                handle,
                indent=2,
            )

        with self.assertRaises(SystemExit):
            compare_metrics(self.snapshot_path, self.outputs_dir, verbose=False)

    def test_compare_metrics_fails_when_metrics_change(self):
        with self.snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(build_metrics(self.outputs_dir), handle, indent=2)

        self._write_payloads(area=120.0)

        with self.assertRaises(SystemExit):
            compare_metrics(self.snapshot_path, self.outputs_dir, verbose=False)