import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict

from backend.topology_health_report import TopologyHealthReporter


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _outputs_dir() -> Path:
    return _repo_root() / "outputs"


def _default_metrics_path() -> Path:
    return _repo_root() / "datasets" / "golden_manifests" / "modern_pipeline_metrics.json"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _sum_segment_lengths(walls: list[dict[str, Any]]) -> float:
    total = 0.0
    for wall in walls:
        points = wall.get("points") or []
        if len(points) >= 2:
            start = points[0]
            end = points[-1]
            if len(start) >= 2 and len(end) >= 2:
                dx = float(end[0]) - float(start[0])
                dy = float(end[1]) - float(start[1])
                total += (dx * dx + dy * dy) ** 0.5
    return round(total, 6)


def _loop_area_list(graph: dict[str, Any]) -> list[float]:
    loops = graph.get("loops", []) if isinstance(graph, dict) else []
    areas = [round(float(loop.get("area", 0.0)), 6) for loop in loops]
    return sorted(areas)


def _failed_checks(checks: dict[str, Any]) -> list[str]:
    if not isinstance(checks, dict):
        return []
    return sorted(str(name) for name, passed in checks.items() if not bool(passed))


def _diagnostic_codes(diagnostics: Any) -> list[str]:
    if not isinstance(diagnostics, list):
        return []

    codes = {
        str(diagnostic.get("code"))
        for diagnostic in diagnostics
        if isinstance(diagnostic, dict) and diagnostic.get("code")
    }
    return sorted(codes)


def _build_topology_health_metrics(graph: dict[str, Any]) -> Dict[str, Any]:
    report = TopologyHealthReporter().build_report(graph)
    counts = report.get("counts", {}) if isinstance(report, dict) else {}
    graph_metrics = report.get("graph_metrics", {}) if isinstance(report, dict) else {}
    loop_metrics = report.get("loop_metrics", {}) if isinstance(report, dict) else {}

    return {
        "status": str(report.get("status", "UNKNOWN")),
        "failed_checks": _failed_checks(report.get("checks", {})),
        "diagnostic_codes": _diagnostic_codes(report.get("diagnostics", [])),
        "counts": {
            "nodes": int(counts.get("nodes", 0)),
            "edges": int(counts.get("edges", 0)),
            "loops": int(counts.get("loops", 0)),
        },
        "graph_metrics": {
            "connected_components": int(graph_metrics.get("connected_components", 0)),
            "component_sizes": [
                int(size) for size in graph_metrics.get("component_sizes", [])
            ],
            "dangling_node_count": int(graph_metrics.get("dangling_node_count", 0)),
            "isolated_node_count": int(graph_metrics.get("isolated_node_count", 0)),
            "self_loop_edge_count": int(graph_metrics.get("self_loop_edge_count", 0)),
            "degree_metadata_mismatch_count": len(
                graph_metrics.get("degree_metadata_mismatches", [])
            ),
        },
        "loop_metrics": {
            "closed_loop_count": int(loop_metrics.get("closed_loop_count", 0)),
            "open_loop_count": int(loop_metrics.get("open_loop_count", 0)),
            "invalid_loop_area_count": int(loop_metrics.get("invalid_loop_area_count", 0)),
            "tiny_loop_count": int(loop_metrics.get("tiny_loop_count", 0)),
            "invalid_loop_edge_reference_count": int(
                loop_metrics.get("invalid_loop_edge_reference_count", 0)
            ),
            "missing_loop_edge_reference_count": int(
                loop_metrics.get("missing_loop_edge_reference_count", 0)
            ),
            "insufficient_unique_loop_edge_count": int(
                loop_metrics.get("insufficient_unique_loop_edge_count", 0)
            ),
            "face_edge_inconsistency_count": int(
                loop_metrics.get("face_edge_inconsistency_count", 0)
            ),
        },
    }


def build_metrics(outputs_dir: Path) -> Dict[str, Any]:
    walls = _read_json(outputs_dir / "walls_clean.json")
    graph = _read_json(outputs_dir / "geometry_graph.json")
    semantics = _read_json(outputs_dir / "bim_semantics.json")
    spaces_payload = _read_json(outputs_dir / "spaces.json")
    bim_model = _read_json(outputs_dir / "bim_model.json")

    spaces = spaces_payload.get("spaces", []) if isinstance(spaces_payload, dict) else []
    elements = semantics.get("elements", []) if isinstance(semantics, dict) else []
    element_type_counts = Counter(str(el.get("type", "Unknown")) for el in elements)

    bim_space_items = bim_model.get("spaces", []) if isinstance(bim_model, dict) else []
    loop_area_list = _loop_area_list(graph)

    return {
        "metrics_version": 2,
        "source": "modern_pipeline_outputs",
        "walls": {
            "count": len(walls),
            "total_segment_length": _sum_segment_lengths(walls),
        },
        "graph": {
            "node_count": len(graph.get("nodes", [])),
            "edge_count": len(graph.get("edges", [])),
            "loop_count": len(graph.get("loops", [])),
            "loop_area_list": loop_area_list,
            "total_loop_area": round(
                sum(loop_area_list),
                6,
            ),
        },
        "semantics": {
            "element_count": len(elements),
            "element_type_counts": dict(sorted(element_type_counts.items())),
        },
        "spaces": {
            "count": len(spaces),
            "total_area": round(sum(float(space.get("area", 0.0)) for space in spaces), 6),
        },
        "bim": {
            "wall_count": len(bim_model.get("walls", [])),
            "door_count": len(bim_model.get("doors", [])),
            "window_count": len(bim_model.get("windows", [])),
            "column_count": len(bim_model.get("columns", [])),
            "space_count": len(bim_space_items),
        },
        "topology_health": _build_topology_health_metrics(graph),
    }


def update_metrics(snapshot_path: Path, outputs_dir: Path) -> None:
    metrics = build_metrics(outputs_dir)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with snapshot_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")

    print(f"Metrik snapshot güncellendi: {snapshot_path}")
    print(json.dumps(metrics, indent=2, ensure_ascii=False, sort_keys=True))


def _emit_metrics_comparison_result(expected: Dict[str, Any], current: Dict[str, Any], *, verbose: bool) -> None:
    if not verbose:
        return

    if expected != current:
        print("Metrik doğrulaması BAŞARISIZ")
        print("Beklenen:")
        print(json.dumps(expected, indent=2, ensure_ascii=False, sort_keys=True))
        print("Mevcut:")
        print(json.dumps(current, indent=2, ensure_ascii=False, sort_keys=True))
        return

    print("Metrik doğrulaması başarılı")
    print(json.dumps(current, indent=2, ensure_ascii=False, sort_keys=True))


def compare_metrics(snapshot_path: Path, outputs_dir: Path, *, verbose: bool = True) -> None:
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Metrik snapshot bulunamadı: {snapshot_path}. Önce update çalıştırın.")

    with snapshot_path.open("r", encoding="utf-8") as handle:
        expected = json.load(handle)

    current = build_metrics(outputs_dir)
    _emit_metrics_comparison_result(expected, current, verbose=verbose)

    if expected != current:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KaRar output metrics snapshot/compare")
    parser.add_argument("action", choices=["update", "verify"])
    parser.add_argument("--snapshot", default=str(_default_metrics_path()))
    parser.add_argument("--outputs", default=str(_outputs_dir()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_path = Path(args.snapshot)
    outputs_dir = Path(args.outputs)

    if not outputs_dir.exists():
        raise FileNotFoundError(f"Outputs dizini bulunamadı: {outputs_dir}")

    if args.action == "update":
        update_metrics(snapshot_path, outputs_dir)
    else:
        compare_metrics(snapshot_path, outputs_dir)


if __name__ == "__main__":
    main()