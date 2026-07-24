# KaRar Architecture Freeze & Refactoring Governance Policy

## 1. Overview
As of KaRar v1.0.0-RC1, the core deterministic CAD-to-BIM pipeline modules—**Geometry Engine**, **Topology Engine**, **Canonical BIM Model (SSoT)**, and **P2 Runtime Validation**—are formally **FROZEN**.

This policy governs code refactoring, directory organization, and repository maintenance to preserve deterministic guarantees, enforce architectural boundaries, and prevent unintended behavioral regressions.

---

## 2. Frozen Core Modules
The following components are strictly locked against unauthorized modifications:
1. **Geometry Engine** (`backend/geometry_engine.py`): Grid locking, R-Tree tie-breaking (`distance -> x -> y -> index`), sliver polygon filtering, deterministic snapping.
2. **Topology Engine** (`backend/topology_engine.py`): Planar graph noding, degree-2 node classification (`straight` vs `L_corner`), face loop extraction.
3. **Canonical BIM Model Core** (`backend/bim_core.py`): Single Source of Truth schema assembly, deterministic UUID namespace mapping, reciprocal spatial relationships, provenance envelope generation.
4. **P2 Runtime Validation Pipeline** (`backend/p2_validation_pipeline.py`): Read-Only Quality Gate Audits (Layer 1: Schema, Layer 2: UUIDs/Orphans, Layer 3: Topology/Graph, Layer 4: Semantic Invariants).

---

## 3. Evidence & Verification Taxonomy (Evidence Levels)
To ensure rigorous engineering claims, all technical reports and evaluations must categorize findings using the following evidence scale:

- **Level A+ (Dynamic Execution Verified)**: Inspected source code AND verified actual execution trace, call stack, and memory/timing behavior during test runs.
- **Level A (Static Inspection)**: Inspected source code (`view_file`) directly line-by-line.
- **Level B (Benchmark & Log Verification)**: Verified via automated execution logs, regression test outputs, or terminal test suites.
- **Level C (Document Declaration)**: Based on documentation, `PROJECT_STATE.md` summaries, or system reports.
- **Level D (Hypothesis / Proposal)**: Theoretical design proposals, architectural recommendations, or unverified assumptions.

---

## 4. Refactoring & Maintenance Guidelines

### 4.1 Allowed Changes
- Modular directory restructuring and clean import paths (e.g., isolating core, validators, and utility modules).
- Removal of obsolete debug scripts, legacy patches, and duplicate helper functions.
- Performance profiling and algorithmic optimization, provided zero domain-semantic regressions occur.
- Adding comprehensive type annotations, docstrings, and inline architectural comments.

### 4.2 Forbidden Changes
- Altering coordinate snapping tolerances or tie-breaking logic without a formal Architecture Decision Record (ADR).
- Modifying the Canonical BIM JSON schema or altering entity property key names without incrementing `schema_version`.
- Allowing the P2 Validation Pipeline to mutate input models or write persistent geometry artifacts.
- Relaxing or bypassing Layer 1-4 quality gate pass thresholds.

---

## 5. Refactoring Protocol & Hash Lock Standard

1. **No Unintended Domain Behavioral Changes**: Refactoring MUST preserve spatial geometry, topological graph connectivity, entity UUID mappings, and spatial adjacency lists.
2. **Domain-Content SHA-256 Hash Lock**:
   - The **Domain Content SHA-256** (hashing `spaces`, `walls`, `windows`, `columns`, and `doors` entities sorted deterministically) MUST remain **100% identical** across refactoring commits.
   - Non-domain metadata changes (such as `generated_at` timestamps in provenance) are excluded from the Domain Content Hash comparison.
3. **Automated Regression Gate**: Every refactoring commit must execute `python3 backend/run_regression_tests.py` and pass all synthetic and real-world benchmark suites without failures.

---

## 6. Governance & Freeze Exception Procedure

### 6.1 Unfreezing & Exception Protocol
If a critical defect or security flaw is discovered in a frozen module:
1. **File an Architectural Decision Record (ADR)** detailing the root cause, technical risks, proposed fix, and regression test plan.
2. **Require Technical Approval**: The fix must be approved against the 5-point evaluation criteria (Architecture, Performance, Maintenance, Scalability, Technical Debt).
3. **Execute Dual Verification**: Run regression tests before and after the patch, validating both Level A+ code execution and Level B log outputs.

### 6.2 Multi-Attribute Performance Evaluation & Rollback Strategy
- **Multi-Attribute Trade-Off Analysis**: Simple fixed percentage speed rules are replaced with holistic multi-attribute evaluation. A minor increase in execution time is acceptable if accompanied by a significant reduction in peak RAM usage, improved topological accuracy, or reduced code complexity.
- **Rollback Condition**: A refactoring commit MUST be reverted if it causes unapproved memory leaks, semantic regressions, or failure on any required Quality Gate (QG-1 through QG-8 defined in [`QUALITY_GATES.md`](./QUALITY_GATES.md) and indexed in [`ENGINEERING_MANUAL.md`](./ENGINEERING_MANUAL.md)). Domain content SHA-256 integrity is strictly governed by [`DOMAIN_HASH_SPEC.md`](./DOMAIN_HASH_SPEC.md).
