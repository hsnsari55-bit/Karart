import json
import tempfile
import unittest
from pathlib import Path

from backend.output_manifest import build_manifest, verify_manifest


class TestOutputManifest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.outputs_dir = self.base / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.base / "manifest.json"
        self.files = ["bim_model.json", "spaces.json"]

        with (self.outputs_dir / "bim_model.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "provenance": {
                        "generated_at": "2026-01-01T00:00:00Z",
                        "canonical_bim_sha256": "abc",
                        "input_hashes": {
                            "bim_semantics_sha256": "hash-a",
                            "spaces_sha256": "hash-b",
                            "geometry_graph_sha256": "hash-c",
                        },
                        "engine": "KaRar BIM Core",
                    },
                    "walls": [{"uuid": "wall-1"}],
                },
                handle,
                indent=2,
            )

        with (self.outputs_dir / "spaces.json").open("w", encoding="utf-8") as handle:
            json.dump({"spaces": [{"uuid": "space-1", "area": 12.5}]}, handle, indent=2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_manifest_normalizes_volatile_bim_fields(self):
        manifest_a = build_manifest(self.outputs_dir, self.files)
        self.assertEqual(
            manifest_a["normalization"]["bim_model.json"],
            [
                "provenance.generated_at",
                "provenance.canonical_bim_sha256",
                "provenance.input_hashes.bim_semantics_sha256",
                "provenance.input_hashes.spaces_sha256",
                "provenance.input_hashes.geometry_graph_sha256",
            ],
        )

        with (self.outputs_dir / "bim_model.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "provenance": {
                        "generated_at": "2030-05-05T05:05:05Z",
                        "canonical_bim_sha256": "different",
                        "input_hashes": {
                            "bim_semantics_sha256": "hash-x",
                            "spaces_sha256": "hash-y",
                            "geometry_graph_sha256": "hash-z",
                        },
                        "engine": "KaRar BIM Core",
                    },
                    "walls": [{"uuid": "wall-1"}],
                },
                handle,
                indent=2,
            )

        manifest_b = build_manifest(self.outputs_dir, self.files)
        self.assertEqual(
            manifest_a["files"]["bim_model.json"]["sha256"],
            manifest_b["files"]["bim_model.json"]["sha256"],
        )

    def test_verify_manifest_fails_on_real_payload_change(self):
        manifest = build_manifest(self.outputs_dir, self.files)
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)

        with (self.outputs_dir / "spaces.json").open("w", encoding="utf-8") as handle:
            json.dump({"spaces": [{"uuid": "space-1", "area": 99.0}]}, handle, indent=2)

        with self.assertRaises(SystemExit):
            verify_manifest(self.manifest_path, self.outputs_dir, self.files)