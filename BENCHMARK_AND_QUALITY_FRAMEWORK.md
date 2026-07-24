# KaRar: Production Benchmark, Accuracy Metrics & Telemetry Framework
*Document Version: 1.0 (Industrial CTO Specification)*
*Scope: 1000+ Real-World DXF Benchmark Suite, Precision Metrics, Deterministic Regression CI/CD, and Privacy-Preserving Telemetry*

---

## Executive Summary

To transition KaRar from a mathematically sound prototype to an impenetrable enterprise CAD-to-BIM kernel, the core pipeline must be continuously audited against real-world drawings. This document defines KaRar's 4 Operational Engineering Pillars:
1. **Real-World Benchmark Dataset (1000+ Anonymized DXFs)**
2. **Quantitative Accuracy Metrics (Precision / Recall / Closure Rates)**
3. **Deterministic Regression Infrastructure (SHA-256 State Locking)**
4. **Privacy-Preserving Production Telemetry (Anonymized Diagnostic Insights)**

---

## Pillar 1: Real-World Benchmark Dataset (1000+ Anonymized Architectural DXFs)

A world-class CAD-to-BIM engine cannot rely solely on clean, synthetic drawings. KaRar maintains a curated, version-controlled benchmark pool of **1000+ anonymized real-world architectural DXF plans** sourced across global CAD vendor formats and drafting conventions.

### Dataset Categorization & Vendor Distribution

| CAD Vendor / Software Source | Target Share | Primary Failure Characteristics & Test Focus |
| :--- | :--- | :--- |
| **AutoCAD (Autodesk)** | 40% (400 DXFs) | Proxy entities (`ACAD_PROXY_ENTITY`), nested block insertions, dynamic blocks, non-standard MTEXT encodings. |
| **BricsCAD (Bricsys)** | 20% (200 DXFs) | Custom BIM entities, MLINE multi-lines, extended entity data (XData) overlays. |
| **ZWCAD / StarCAD** | 15% (150 DXFs) | Chinese/CJK font codepages, unclosed polyline flags, non-standard layer dictionaries. |
| **DraftSight (Dassault)** | 15% (150 DXFs) | Large UTM surveying coordinate offsets ($10^6\text{ m}$), floating-point precision loss. |
| **LibreCAD & Open Source** | 10% (100 DXFs) | Missing layer tables, zero-length lines, unscaled arc chords, missing header variables. |

### Classification of Benchmark Failure Types

Every DXF in the dataset is tagged with one or more operational difficulty classifications:
- **CLASS-A (Clean Standard):** Conforms fully to AIA/ISO 13567 layer standards with closed wall polylines ($>95\%$ expected auto-conversion).
- **CLASS-B (Minor Drafting Noise):** Contains micro-gaps ($<5\text{ mm}$), collinear line fragments, and overlapping wall segments ($>90\%$ expected conversion).
- **CLASS-C (Unstructured / Messy Layers):** Walls drawn on `Layer 0`, door blocks exploded into raw lines, hatch overlays touching wall centerlines ($>80\%$ expected conversion).
- **CLASS-D (Extreme / Degenerate):** Non-orthogonal angled walls ($89.2^\circ$), large coordinate offsets, proxy blocks, missing layer headers (Requires repair heuristics & warning reports).

---

## Pillar 2: Quantitative Accuracy Metrics

Every benchmark run produces 4 standardized quantitative accuracy metrics. Releases are rejected if any metric falls below production thresholds.

### 1. Wall Precision & Recall ($F_1$-Score)
Measures the accuracy of extracted 2D wall centerlines against ground-truth vector layers:
$$\text{Precision}_{\text{Wall}} = \frac{\text{True Positive Wall Length}}{\text{Extracted Wall Length}}, \quad \text{Recall}_{\text{Wall}} = \frac{\text{True Positive Wall Length}}{\text{Ground Truth Wall Length}}$$
$$\text{Threshold:} \quad F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} \ge 0.985$$

### 2. Room Closure & Polygon Extraction Rate
Measures the proportion of valid architectural spaces extracted without volumetric leaks:
$$\text{Closure Rate}_{\text{Room}} = \frac{\text{Number of Topologically Closed Room Polygons}}{\text{Ground Truth Room Count}} \times 100\%$$
$$\text{Threshold:} \quad \text{Closure Rate} \ge 99.0\%$$

### 3. Door & Window Ownership Accuracy
Measures whether wall openings (doors/windows) are attached to the correct parent wall segment in the Canonical BIM SSoT model:
$$\text{Accuracy}_{\text{Opening}} = \frac{\text{Openings Attached to Correct Parent Wall UUID}}{\text{Total Identified Openings}} \times 100\%$$
$$\text{Threshold:} \quad \text{Accuracy} \ge 99.5\%$$

### 4. Canonical BIM Schema & Topological Consistency Rate
Evaluates full compliance with the Canonical BIM JSON Schema, Euler-Poincare invariants ($V - E + F = 2 - 2G$), and relational integrity:
$$\text{Consistency Rate} = \frac{\text{Valid Canonical BIM Models (Passes Validator Gates)}}{\text{Total Processed DXF Models}} \times 100\%$$
$$\text{Threshold:} \quad \text{Consistency Rate} = 100\% \quad \text{(Zero schema/topological crashes allowed)}$$

---

## Pillar 3: Deterministic Regression Infrastructure

To guarantee 100% repeatability across commits, KaRar enforces a strict deterministic regression testing pipeline in CI/CD.

```
Git Commit ──► Pre-Flight Linter ──► Unit Tests ──► 1000+ DXF Benchmark Execution ──► SHA-256 Hash Comparison ──► Regression Report
```

### Deterministic State Locking (SHA-256 SSoT Verification)
- **Zero Flakiness Rule:** For any given input DXF, running the engine across different operating systems (Linux, macOS, Windows) or CPU architectures MUST produce an identical `bim_model.json` file.
- **Sorted Serialization:** All JSON keys, arrays, and entity dictionaries are sorted alphabetically prior to serialization.
- **Cryptographic Hash Lock:**
  $$\text{SHA256}(\text{bim\_model.json}_{\text{commit\_N}}) \equiv \text{SHA256}(\text{bim\_model.json}_{\text{Golden Master}})$$

### Performance & Memory Regression Limits
- **Execution Time Limit:** Processing time per megabyte of DXF must not increase by more than $5\%$ compared to the baseline commit.
  $$\text{Max Time Tolerance:} \quad \Delta t_{\text{proc}} \le 150\text{ ms / MB}$$
- **Peak Memory Threshold:** Memory consumption during $O(N \log N)$ STRtree spatial indexing and half-edge traversal must stay strictly bounded:
  $$\text{Max Peak RAM:} \quad M_{\text{peak}} \le 256\text{ MB} \quad \text{(for 50,000+ entity DXF drawings)}$$

---

## Pillar 4: Privacy-Preserving Production Telemetry

To continuously improve KaRar's geometry repair algorithms without exposing sensitive user Intellectual Property (IP) or proprietary architectural drawings, KaRar implements an opt-in, zero-knowledge diagnostic telemetry protocol.

### Strictly Anonymized Telemetry Payload (No Geometry or Text Exported)

The telemetry payload **NEVER** exports raw coordinates, entity handles, text strings, or project names. It collects purely anonymized structural metrics:

```json
{
  "telemetry_version": "1.0",
  "engine_version": "v0.9.4-deterministic",
  "dxf_metadata": {
    "cad_vendor": "AutoCAD 2024",
    "dxf_version": "AC1032",
    "total_entity_count": 14250,
    "file_size_kb": 3240
  },
  "execution_metrics": {
    "parse_time_ms": 42,
    "geometry_engine_ms": 118,
    "topology_engine_ms": 85,
    "ssot_builder_ms": 19,
    "peak_memory_mb": 48.2
  },
  "repair_patterns_triggered": {
    "zero_length_lines_dropped": 14,
    "collinear_segments_merged": 132,
    "micro_gaps_bridged": 3,
    "duplicate_overlays_deduplicated": 45,
    "unclosed_polylines_auto_closed": 2
  },
  "topological_health": {
    "extracted_rooms": 18,
    "euler_poincare_satisfied": true,
    "unresolved_topological_leaks": 0
  }
}
```

### Telemetry Diagnostic Insights & Algorithm Refinement
- **Most Frequently Failing Geometry Patterns:** Identifies if specific CAD tools (e.g., exploded block hatches) trigger high micro-gap counts.
- **Repair Heuristic Cost Profiling:** Measures which repair algorithms (e.g., Snap-Rounding vs. Sweep-Line Intersections) consume the most CPU cycles.
- **Continuous Algorithm Optimization:** Data feeds directly into the **Research Track** to refine tolerance bands and edge cases for future kernel releases.

---

## Summary of Verification Pipeline Integration

With these 4 pillars active, KaRar enforces a complete 5-gate Release Approval Pipeline:
$$\text{Code Commit} \longrightarrow \text{Repo Verification} \longrightarrow \text{Regression Tests} \longrightarrow \text{1000+ DXF Benchmark} \longrightarrow \text{BIM Validation} \longrightarrow \text{Release Approval}$$

*Document Specification Complete.*
