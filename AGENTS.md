# KaRar Project and Architectural Guidelines

## Core Principles

1. **Deterministic CAD-to-BIM Focus**: KaRar's ultimate goal is to understand 2D CAD architectural drawings deterministically and produce a single, verifiable, and structured source of truth: the **Canonical BIM Model**. It is NOT a 3D visualizer, Blender project, or an IFC generator primarily. These are downstream output generators.
2. **Sequential Architecture Standard**:
   1. **Parser**: Reading and normalizing source files (.dxf, etc.).
   2. **Geometry Engine**: Coordinate normalization, noise filtering, and short segment repair.
   3. **Topology Engine**: Edge snapping, intersection splitting, and room polygon extraction.
   4. **Canonical BIM Model**: Single Source of Truth JSON Schema (verifiable, structured contract).
   5. **Semantic Enrichment**: Wall, Column, Door, Window, and Room function heuristics.
   6. **Blender Builder**: Solid B-Rep solid model output generation.
   7. **IFC Export**: openBIM compatibility output generation.
   8. **Engineering Dashboard (UI)**: System health, unit test results, validation and error rates.
   9. **Cloud & Collaboration**: Multi-user sync and remote standard validation (future).

## Project Guidelines and Constraints

- **No Premature "100% Complete" Labels**: Geometry Engine, Topology Engine, and Canonical BIM Model must be fully stabilized and mathematically validated before downstream modules (such as Blender Builder, IFC Export) can be marked complete.
- **Downstream Decoupling**: Blender Builder, IFC Export, and the UI MUST only read data from the Canonical BIM Model (JSON contract). They must not generate or assume geometry independently.
- **Pure Engineering Dashboard**: The UI must serve as an Engineering Dashboard, visualizing actual data flow status, geometry/topology health metrics, test results, and error rates instead of marketing placeholders.
- **Explicit Contracts**: Every module must have clearly defined inputs, outputs, and responsibilities centered around the Canonical BIM Model.

## Strict Development and Reporting Rules

1. **Deterministic Verification First**: Before adding any feature or proposing a modification, verify the current state of core algorithms.
2. **Do Not Touch Resolved Issues**: Topics marked as **Resolved** in `PROJECT_STATE.md` are archived and must not be touched or brought back into Gap Analysis unless new concrete technical evidence emerges.
3. **Strict Report Format**: Every future technical report/proposal must follow this 6-point structure exactly:
   1. **Kanıt** (Relevant file, line number, or test execution logs/outputs)
   2. **Risk Analizi** (Technical risks of the current state)
   3. **Önerilen Çözüm** (Proposed solution focusing on core deterministic robustness)
   4. **Uygulanan Değişiklik** (Implemented changes)
   5. **Doğrulama** (Benchmark, regression test, or build results)
   6. **Kalan Riskler** (Outstanding technical limitations or side-effects)
4. **No Repeated Gap Reports**: Never report the same gap or suggestion twice. Each Gap Analysis must present only newly identified technical debts and improvement areas.
5. **Priority Filtering Rule**: Every proposed change must answer this question explicitly:
   > *“Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir şekilde artırıyor mu?”*
   - If **YES**: The task is high priority.
   - If **NO**: The task is postponed or rejected.
6. **No Premature Status Claims**: No module or feature shall be marked as "complete", "100%", "production-ready", or similar terms unless backed by solid benchmark results, regression tests, or rigorous code reviews.
7. **No Non-Essential Refactoring**: Refactoring or cleanups that do not directly improve accuracy, determinism, or performance metrics of the core engines (Geometry Engine, Topology Engine, Canonical BIM Model) must not be prioritized.

