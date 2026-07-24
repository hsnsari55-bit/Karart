# KaRar Domain Content Hash Specification (v1.0)

## 1. Objective & Design Intent
This specification defines the exact, byte-level algorithm for calculating the **Domain Content SHA-256 Hash** (`canonical_bim_sha256`) for KaRar Canonical BIM models (`outputs/bim_model.json`).

**Design Intent & Scope**:
- **Canonical Representation Equality**: The Domain Hash evaluates equality over a **deterministic, canonical JSON byte representation** of physical BIM entities (sorted keys, rounded 6-decimal floating points, UTF-8 LF endings) to verify identical domain extraction across refactoring iterations, OS platforms, and Python library versions.
- **Serialization Isolation**: Volatile runtime metadata (timestamps, environment paths, execution logs) are strictly excluded from the payload.
- **Spec Version Alignment**: Hash calculation rules are tied to `domain_hash_spec: "1.0"`. Schema additions during Phase 1-5 refactoring (e.g., Golden Dataset extensions) that modify entity shapes will transition under a formal `v2.0` spec bump.

---

## 2. Specification Semantic Versioning (`v1.0`)
- **Version Identifier**: `1.0`
- **Provenance Registration**: Every generated Canonical BIM model MUST record `"domain_hash_spec": "1.0"` inside its `provenance` metadata envelope.
- **Breaking Changes (`v2.0`)**: If a new BIM entity type (e.g. `slabs`, `beams`) or rounding precision rule is introduced, `domain_hash_spec` MUST be bumped to `2.0`. Legacy hashes produced under `1.0` are evaluated against `v1.0` canonicalization rules.

---

## 3. Included Domain Entities
Only core physical BIM entities are included in the hash payload:
1. `spaces` (Space boundaries, area, related walls/openings/columns, neighbor links)
2. `walls` (Baseline points, thickness, related spaces)
3. `windows` (Boundary points, parent wall link)
4. `columns` (Polygon points, parent spaces link)
5. `doors` (Boundary points, parent wall link)

---

## 4. Excluded Volatile Metadata
The following metadata fields are strictly **EXCLUDED** from the Domain Content Hash calculation to prevent false diffs caused by execution context:
- `provenance.generated_at` (UTC timestamp)
- `provenance.python_version`
- `provenance.shapely_version`
- `provenance.input_hashes`

---

## 5. Canonicalization Rules (Byte-Level Rules)

### Rule 5.1: Floating-Point Coordinate Rounding
- All spatial coordinates (`x`, `y`, `z`, `area`, `width`, `height`, `thickness`) MUST be rounded to **6 decimal places** (`0.000001 mm / unit precision`) before string serialization.
- Exponential floating-point notation (`1.0e-05`) is normalized to standard decimal strings (`0.000010`).

### Rule 5.2: Entity Sorting
All entity collections MUST be sorted deterministically before JSON serialization:
- **Primary Sort Key**: `type` (alphabetical: `Column` < `Door` < `Space` < `Wall` < `Window`)
- **Secondary Sort Key**: `uuid` (lexicographical string sorting)
- Internal UUID list properties (`related_walls`, `neighbors`, `parent_spaces`, etc.) MUST be sorted lexicographically.

### Rule 5.3: JSON Key Ordering & Encoding
- JSON key-value pairs MUST be serialized with `sort_keys=True` and `indent=4`.
- Character encoding MUST be UTF-8 without Byte Order Mark (BOM).
- Line endings MUST be normalized to Unix LF (`\n`).

---

## 6. Reference Verification Function (Python)

```python
import json
import hashlib

DOMAIN_HASH_SPEC_VERSION = "1.0"

def calculate_domain_content_hash(bim_model: dict) -> str:
    """Calculates byte-level canonical SHA-256 for domain content (v1.0)."""
    domain_payload = {
        "domain_hash_spec": DOMAIN_HASH_SPEC_VERSION,
        "spaces": bim_model.get("spaces", []),
        "walls": bim_model.get("walls", []),
        "windows": bim_model.get("windows", []),
        "columns": bim_model.get("columns", []),
        "doors": bim_model.get("doors", [])
    }
    
    # Sort keys, encode UTF-8 Unix LF
    json_bytes = json.dumps(domain_payload, indent=4, sort_keys=True).replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()
```

