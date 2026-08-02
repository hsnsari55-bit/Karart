import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_OUTPUTS = [
    "dxf_raw.json",
    "walls_clean.json",
    "geometry_graph.json",
    "bim_semantics.json",
    "spaces.json",
    "bim_model.json",
]


VOLATILE_BIM_MODEL_FIELDS = [
    "provenance.generated_at",
    "provenance.canonical_bim_sha256",
    "provenance.input_hashes.bim_semantics_sha256",
    "provenance.input_hashes.spaces_sha256",
    "provenance.input_hashes.geometry_graph_sha256",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _outputs_dir() -> Path:
    return _repo_root() / "outputs"


def _default_manifest_path() -> Path:
    return _repo_root() / "datasets" / "golden_manifests" / "modern_pipeline_outputs.json"


def _normalize_json_payload(file_name: str, payload: Any) -> Any:
    """Remove known volatile fields before hashing for deterministic comparison."""
    if file_name == "bim_model.json" and isinstance(payload, dict):
        provenance = payload.get("provenance")
        if isinstance(provenance, dict):
            normalized_provenance = dict(provenance)
            normalized_provenance.pop("generated_at", None)
            normalized_provenance.pop("canonical_bim_sha256", None)
            input_hashes = normalized_provenance.get("input_hashes")
            if isinstance(input_hashes, dict):
                normalized_input_hashes = dict(input_hashes)
                normalized_input_hashes.pop("bim_semantics_sha256", None)
                normalized_input_hashes.pop("spaces_sha256", None)
                normalized_input_hashes.pop("geometry_graph_sha256", None)
                if normalized_input_hashes:
                    normalized_provenance["input_hashes"] = normalized_input_hashes
                else:
                    normalized_provenance.pop("input_hashes", None)
            payload = dict(payload)
            payload["provenance"] = normalized_provenance
    return payload


def _compute_json_sha256(file_path: Path) -> str:
    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    normalized = _normalize_json_payload(file_path.name, payload)
    serialized = json.dumps(normalized, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_manifest(outputs_dir: Path, files: List[str]) -> Dict[str, Any]:
    manifest_files: Dict[str, Dict[str, Any]] = {}

    for file_name in files:
        file_path = outputs_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Beklenen çıktı dosyası bulunamadı: {file_path}")

        manifest_files[file_name] = {
            "sha256": _compute_json_sha256(file_path),
            "size_bytes": file_path.stat().st_size,
        }

    return {
        "manifest_version": 1,
        "manifest_name": "modern_pipeline_outputs",
        "normalization": {
            "bim_model.json": list(VOLATILE_BIM_MODEL_FIELDS),
        },
        "files": manifest_files,
    }


def update_manifest(manifest_path: Path, outputs_dir: Path, files: List[str]) -> None:
    manifest = build_manifest(outputs_dir, files)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")

    print(f"Manifest güncellendi: {manifest_path}")
    for file_name, info in manifest["files"].items():
        print(f"  - {file_name}: {info['sha256'][:12]} ({info['size_bytes']} bytes)")


def verify_manifest(manifest_path: Path, outputs_dir: Path, files: List[str]) -> None:
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Manifest bulunamadı: {manifest_path}. Önce update çalıştırın."
        )

    with manifest_path.open("r", encoding="utf-8") as handle:
        expected = json.load(handle)

    current = build_manifest(outputs_dir, files)
    mismatches: List[str] = []

    expected_files = expected.get("files", {})
    current_files = current.get("files", {})

    for file_name in files:
        expected_info = expected_files.get(file_name)
        current_info = current_files.get(file_name)

        if expected_info is None:
            mismatches.append(f"Manifest girdisi eksik: {file_name}")
            continue

        if current_info is None:
            mismatches.append(f"Mevcut çıktı girdisi eksik: {file_name}")
            continue

        if expected_info.get("sha256") != current_info.get("sha256"):
            mismatches.append(
                f"Hash uyuşmazlığı {file_name}: expected={expected_info.get('sha256')} current={current_info.get('sha256')}"
            )

    extra_expected = sorted(set(expected_files.keys()) - set(files))
    if extra_expected:
        mismatches.append(f"Manifestte beklenmeyen ek girdiler var: {', '.join(extra_expected)}")

    if mismatches:
        print("Manifest doğrulaması BAŞARISIZ")
        for item in mismatches:
            print(f"  - {item}")
        raise SystemExit(1)

    print("Manifest doğrulaması başarılı")
    for file_name, info in current_files.items():
        print(f"  - {file_name}: {info['sha256'][:12]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KaRar output manifest updater/verifier")
    parser.add_argument("action", choices=["update", "verify"])
    parser.add_argument("--manifest", default=str(_default_manifest_path()))
    parser.add_argument("--outputs", default=str(_outputs_dir()))
    parser.add_argument("--files", nargs="*", default=DEFAULT_OUTPUTS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    outputs_dir = Path(args.outputs)
    files = args.files

    if not outputs_dir.exists():
        raise FileNotFoundError(f"Outputs dizini bulunamadı: {outputs_dir}")

    if args.action == "update":
        update_manifest(manifest_path, outputs_dir, files)
    else:
        verify_manifest(manifest_path, outputs_dir, files)


if __name__ == "__main__":
    main()