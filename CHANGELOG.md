# KaRar Changelog & Technical Review Package

## [v1.0-alpha] - 2026-07-22

### 📋 Overview
KaRar v1.0-alpha deterministic CAD-to-BIM core and SSoT (`bim_model.json`) contract have been officially locked and established as the baseline reference release.

### ✨ Added Files
* **`backend/constraint_solver.py`**: Deterministic constraint resolution engine for topology graph edge optimization and intersection adjustment.
* **`backend/topology_validator.py`**: Mandatory blocking quality gate validating node-edge network topological integrity.
* **`outputs/production_metrics_report.md`**: Quantitative production and quality metrics matrix confirming %100 success rate across benchmarks.
* **`outputs/benchmark_report.md`**: Comprehensive benchmark execution breakdown for reference and synthetic edge-case datasets.
* **`outputs/release_verification_summary.md`**: Release sign-off documentation and architectural verification checklist.

### 🔄 Modified Files
* **`backend/dxf_parser.py`**: Enhanced `$INSUNITS` scaling normalization and layer filtering.
* **`backend/geometry_engine.py`**: Adaptive fuzzy snapping and collinear segment merge optimization.
* **`backend/topology_engine.py`**: Unary union noding and closed loop (face) extraction.
* **`backend/space_engine.py`**: Iterative gap closing retry mechanism (400.0mm threshold) for robust room polygon extraction.
* **`backend/run_regression_tests.py`**: Automated regression test suite covering reference dataset (`20_market_gida.dxf`) and synthetic edge-case stress tests.

### 📌 Git Commit Summary
* **Commit SHA:** `842a294a517cbd4f7f0ef346018b611a771e33b9`
* **Commit Message:** `KaRar v1.0-RC1: Clean workspace state ready for push`
* **Diff Stats:** Core deterministic pipeline fully stabilized across geometry, topology, semantic, and space engines.

### 🧪 Regression Test Results
* **Test Suite:** `python3 -m backend.run_regression_tests`
* **Execution Status:** PASS (%100 successful)
* **Exit Code:** `0`
* **Verification Scope:** Reference dataset + 5 synthetic stress/edge-case benchmarks.

### 🏛️ Architecture Change Summary
* **Geometry Engine:** R-Tree spatial indexing and grid-locked coordinate quantization.
* **Topology Engine:** Planar graph construction and face extraction.
* **BIM SSoT (`bim_model.json`):** Strict single source of truth contract separating geometry computation from downstream consumers (Blender Builder, IFC Exporter).
* **Parser & Performance:** Scaled DXF parsing with ~185ms execution time and ~68MB peak memory usage.
