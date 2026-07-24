# KaRar Engineering Manual & Architecture Index (v1.0)

## 1. Executive Summary
KaRar is a deterministic CAD-to-BIM processing platform engineered to parse 2D architectural drawings (.dxf) and produce a single, verifiable, and mathematically canonical **BIM Model (Single Source of Truth - SSoT)**.

This Engineering Manual serves as the central entry point for developers, software architects, and AI agents. It organizes project governance, technical specifications, and quality verification frameworks.

---

## 2. Core Architectural Pipeline

```
[ DXF Source ]
      ↓
[ Geometry Engine ]      🔒 FROZEN (Grid locking, R-Tree snapping, sliver filtering)
      ↓
[ Topology Engine ]      🔒 FROZEN (Planar graph noding, degree-2 node classification)
      ↓
[ Semantic Engine ]      ✔ Active (Wall, Door, Window, Column heuristics)
      ↓
[ Space Engine ]         ✔ Active (Room polygon extraction & adjacency graph)
      ↓
[ Canonical BIM (SSoT) ] 🔒 FROZEN (JSON schema, spatial links, provenance envelope)
      ↓
[ P2 Validation Gate ]   🔒 FROZEN (Read-only Layer 1-4 audit verification)
      ↓
[ Downstream Generators ] (Blender B-Rep Builder / IFC OpenBIM Exporter)
```

---

## 3. Master Governance Document Index

1. **[`PROJECT_STATE.md`](./PROJECT_STATE.md)**: Current system state, archived issues, and active technical debt.
2. **[`ARCHITECTURE_FREEZE.md`](./ARCHITECTURE_FREEZE.md)**: Frozen module bounds, governance rules, and freeze exception procedures.
3. **[`DOMAIN_HASH_SPEC.md`](./DOMAIN_HASH_SPEC.md)**: Byte-level specification for the Domain Content SHA-256 Hash (`v1.0`).
4. **[`QUALITY_GATES.md`](./QUALITY_GATES.md)**: Mandatory quality verification gates (QG-1 through QG-8) and pragmatic change classification tiers.

---

## 4. Change Classification & Pragmatic Governance

To ensure governance maintains high rigor without hindering development momentum, code changes are classified into three tiers:

| Tier | Change Scope | Required Governance Artifacts | Review & Verification |
| :--- | :--- | :--- | :--- |
| **Minor** | Documentation, comments, type hints, log formatting, new unit tests. | No ADR required. | QG-4 (Import Check), QG-5 (Lint/Build). |
| **Medium** | Directory restructuring, helper refactoring, non-core utility updates. | Lightweight ADR in PR description. | QG-1, QG-3 (Domain Hash), QG-4, QG-5, QG-8. |
| **Major** | Any edit to frozen core algorithms (`geometry_engine.py`, `topology_engine.py`, `bim_core.py`, `p2_validation_pipeline.py`). | Formal Architecture Decision Record (ADR) file. | Full Quality Gate Suite (**QG-1 through QG-8**) + Dual Benchmark Verification. |

---

## 5. Target Domain-Oriented Architecture
To prevent functional overlap and eliminate architectural ambiguity, backend refactoring will reorganize modules along domain boundaries:

```
backend/
├── geometry/            # Coordinate snapping, R-Tree tie-breaking, graph noding, planar repair
├── semantics/           # Wall/Door/Window/Column detectors & Space polygon heuristics
├── bim/                 # Canonical SSoT BIM Schema, JSON assembly, domain content hash (v1.0)
├── validation/          # Read-only P2 runtime quality gate audit pipeline (Layer 1-4)
├── exporters/           # Downstream presentation generators (Blender B-Rep, IFC)
├── cli/                 # Command-line entry points & user execution interfaces
├── common/              # Shared types, logging, math utilities, and error definitions
└── tests/               # Unit, integration, and regression test suites
```

### 5.1 Unidirectional Layer Dependency Rule
To eliminate circular dependencies and enforce clean architectural boundaries, imports MUST flow strictly in one direction:
$$\text{common} \longleftarrow \text{geometry} \longleftarrow \text{semantics} \longleftarrow \text{bim} \longleftarrow \text{validation / exporters / cli}$$
- **Strict Prohibition**: Lower-tier modules (`common`, `geometry`, `semantics`) are strictly forbidden from importing higher-tier modules (`bim`, `validation`, `exporters`). Any violation fails QG-4 and QG-8 automatically.

---

## 6. Public API Contract & Refactoring Definition of Done (DoD)

### 6.1 Public API Contract & Behavior Guarantees (Phase 0 Lock)
To guarantee zero breakage across downstream tools, CI pipelines, and consumers, the following interfaces and data structures are locked as **Public**:
- **Public Python Modules & Entry Points**:
  - `backend/main.py`: `run_pipeline(dxf_path: str, output_dir: str) -> dict`, `load_dxf(dxf_path: str)`, `export_canonical_bim(model: dict, output_path: str)`. Behavior: Must execute without throwing unhandled runtime exceptions on valid DXF inputs and generate valid JSON outputs.
- **Public CLI Commands & Arguments**:
  - `python3 backend/main.py <input.dxf> --out <output_dir>`: Positional argument for DXF path, `--out` optional directory flag (defaults to `outputs/`).
  - `python3 backend/run_regression_tests.py`: Standard test runner returning exit code `0` on 100% pass and non-zero on failure.
- **Public JSON Data Contract (`outputs/bim_model.json`)**:
  - **Mandatory Root Keys**: `spaces` (array), `walls` (array), `windows` (array), `columns` (array), `doors` (array), `provenance` (object with `domain_hash_spec: "1.0"`).
  - **Mandatory Entity Fields**: Every entity must contain `uuid` (str), `type` (str), `boundary_points` or `baseline_points` (array of `[x, y, z]` floats rounded to 6 decimals).
- **API Freeze vs. Schema Freeze Policy**:
  - **API Freeze**: Active immediately in Phase 0 (method signatures, CLI parameters, execution flows).
  - **Schema Freeze**: Finalized post-Golden Dataset benchmark. Future entity additions (e.g., slabs, stairs) will increment `domain_hash_spec` to `2.0` without breaking `v1.0` consumers.
- **Golden Dataset Classification & Verification Baseline**:
  - Refactoring MUST be verified against the official **Golden Dataset** (`backend/tests/golden_dataset/`) categorized into 7 functional groups:
    1. **Group 1 (Simple Plan)**: Basic regression and baseline snapping.
    2. **Group 2 (Real Residential)**: Normal production usage and space extraction.
    3. **Group 3 (Complex Commercial)**: Large-scale stress testing and performance limits.
    4. **Group 4 (Corrupt DXF)**: Self-healing, fault-tolerant recovery tests.
    5. **Group 5 (CAD Vendor Compatibility)**: Multi-CAD software export compatibility.
    6. **Group 6 (Determinism Stress)**: Multi-execution (100x/1000x) hash invariance checks.
    7. **Group 7 (Floating Point Stress)**: Micro-scale snap tolerance & boundary precision checks.
- **Internal Modules (Eligible for Restructuring)**: Internal geometry helpers, snapping math, graph node classes, and heuristic threshold functions inside `geometry_engine.py`, `topology_engine.py`, `bim_core.py`.

### 6.2 Phased Refactoring Roadmap
Refactoring proceeds sequentially across 6 isolated phases with strict regression testing between each phase:
- **Phase 0 (Public API Freeze & Golden Dataset Lock)**: Lock public entry points, CLI arguments, JSON contract, and establish Golden Dataset baseline.
- **Phase 1 (Skeleton Creation)**: Establish domain directories (`geometry`, `semantics`, `bim`, `validation`, `exporters`, `cli`, `common`, `tests`) and static import boundary checks (QG-4, QG-8). Automated CI workflow active via `.github/workflows/quality.yml`.
- **Phase 2 (Common Utilities)**: Move logging, error handling, and basic math helpers to `common/`. Verify regression suite.
- **Phase 3 (Geometry Module)**: Migrate grid locking, snapping, and planar graph logic to `geometry/`. Verify QG-1, QG-3.
- **Phase 4 (Semantics & BIM Core)**: Migrate entity heuristics, room polygon extraction, and SSoT assembly to `semantics/` and `bim/`.
- **Phase 5 (Validation & Exporters)**: Migrate P2 quality gates and export pipelines to `validation/` and `exporters/`. Verify QG-1 through QG-8.

### 6.3 Refactoring Definition of Done (DoD)
Refactoring is formally considered complete when all of the following conditions are met:
1. **Flat Backend Namespace Replaced**: Monolithic root files migrated to domain directories (`geometry/`, `semantics/`, `bim/`, `validation/`).
2. **Public API Unchanged**: `backend/main.py` entry points, CLI parameters, and `bim_model.json` schema behave identically.
3. **Hard Quality Gates All PASS**: QG-1 (Regression 100%), QG-2 (P2 Audit PASS), QG-3 (Domain Hash Identity v1.0), QG-4 (Zero Circular Imports), QG-5 (Lint/Type Check PASS), QG-8 (Zero Layer Violations).
4. **Core Module Test Coverage Maintained**: Test coverage metric monitored specifically per core module (`geometry/`, `semantics/`, `bim/`, `validation/`) and does NOT regress.
5. **Zero Open Critical Bugs**: Zero unresolved critical severity bugs or regression failures.
6. **Automated CI Enforcement Active**: All Hard Quality Gates pass automatically in `.github/workflows/quality.yml` on every pull request.
7. **No Open Governance Exceptions**: All change rationale documented and technical debt items updated in `PROJECT_STATE.md`.

---

## 7. Architectural Non-Negotiables
- **SSoT Isolation**: Downstream visualization tools (Blender, IFC) MUST ONLY read from the Canonical BIM Model JSON. They must never independently compute or modify geometry.
- **Read-Only P2 Validator**: The P2 Runtime Validation Pipeline must NEVER write or mutate persistent model data or geometry.
- **Automated Layer Enforcement**: Layer boundary violations are detected via static import analysis (QG-4, QG-8) and blocked automatically.
- **Evidence-Based Reporting**: All architectural claims must be categorized by Evidence Levels (Level A+ down to Level D) as defined in [`QUALITY_GATES.md`](./QUALITY_GATES.md).
