# KaRar Quality Gates & Verification Framework

## 1. Overview
Every pull request, refactoring attempt, or architectural proposal in KaRar must pass all applicable **Quality Gates (QG-1 through QG-8)** as defined in the [`ENGINEERING_MANUAL.md`](./ENGINEERING_MANUAL.md).

---

## 2. Quality Gates Classification (Hard vs. Soft Gates)

### 2.1 Hard Gates (Strictly Mandatory - Zero Tolerated Failures)
Failure on any Hard Gate results in immediate PR rejection (`QUALITY_GATE_REJECTED`):
- **QG-1 (Regression Suite Pass)**: 100% test pass rate on `run_regression_tests.py` (Level A+ / B).
- **QG-2 (P2 Audit Quality Gates)**: Layer 1-4 audit pass on Canonical BIM outputs (Level A+).
- **QG-3 (Domain Hash Identity)**: `canonical_bim_sha256` matching baseline per `DOMAIN_HASH_SPEC.md` v1.0 (Level A+).
- **QG-4 (Circular Import Check)**: Zero circular dependencies detected via static import analysis (Level A).
- **QG-5 (Linter & Type Check)**: `npm run lint` & `tsc --noEmit` cleanly passing (Level B).
- **QG-8 (Architectural Compliance)**: Zero layer boundary violations; P2 remains read-only; SSoT bypass strictly forbidden (Level A / A+).

### 2.2 Soft Gates (Advisory / Multi-Attribute Trade-Off Analysis)
Soft Gates require engineering review and justification, but allow multi-attribute trade-offs:
- **QG-6 (Multi-Attribute Performance)**: Latency vs. Peak RAM trade-offs evaluated holistically against baselines.
- **QG-7 (Governance & ADR Compliance)**: ADR review and rationale check for major architectural changes.

---

## 3. Evidence Scale & Audit Scope Definitions
- **Internal Evidence Scale** (Self-reported by automated agents/pipelines):
  - **Level A+ (Dynamic Execution Verified)**: Inspected source code AND verified actual execution trace, call stack, and runtime memory/timing behavior during test runs.
  - **Level A (Static Code Inspection)**: Inspected source code (`view_file`) directly line-by-line.
  - **Level B (Benchmark & Log Verification)**: Verified via automated execution logs, regression test outputs, or terminal test suites.
  - **Level C (Document Declaration)**: Based on documentation, `PROJECT_STATE.md` summaries, or system reports.
  - **Level D (Hypothesis / Proposal)**: Theoretical design proposals, architectural recommendations, or unverified assumptions.
- **External Audit Scope Note**: Internal Level A/A+ ratings represent internal automated/agent inspection. Third-party or external reviewers verify claims independently to establish external audit levels.

---

## 4. Pragmatic Change Tiers
Quality Gate enforcement is applied proportionally according to change risk:
- **Minor Tier** (Docs, Comments, Tests): Must pass QG-4, QG-5.
- **Medium Tier** (Restructuring, Refactoring): Must pass QG-1, QG-3, QG-4, QG-5, QG-8.
- **Major Tier** (Frozen Core Algorithm Modifications): Must pass ALL gates (**QG-1 through QG-8**).

---

## 5. Quality Gate Failure Protocol
If any required Quality Gate fails:
1. The commit is rejected automatically (`QUALITY_GATE_REJECTED`).
2. A technical diff report must highlight the exact failing gate and line-level root cause.
3. No refactoring changes may proceed until all required Quality Gates report **100% PASS**.

