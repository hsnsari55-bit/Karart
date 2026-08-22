"""Deterministic, read-only drawing-region audit for multi-drawing DXF modelspaces.

This module is an evidence generator between parsing and geometry processing.  It does
not select walls or repair geometry; selected floor-view entities are passed through
the frozen Geometry/Topology/Validator chain in isolated workspaces. Classification is
deliberately fail-closed: uncertain candidates remain ``ambiguous`` for human review.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import html
import io
import json
import math
import re
import statistics
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from backend.spatial_index import index

try:
    import ezdxf
except ImportError:  # pragma: no cover - exercised by CLI environment validation
    ezdxf = None


SCHEMA_VERSION = "karar.drawing-region-audit/2.0"
REQUIRED_SOURCE_SHA256 = "289b586570f0d915cae1707ccb234b84bd0527bd1412189b5b238811aa9a721c"
STRUCTURAL_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE"}
ANNOTATION_TYPES = {"TEXT", "MTEXT"}
CLASS_NAMES = ("floor_plan", "section", "elevation", "roof_plan", "site_plan")
FRAME_LAYER_KEY = "CERCEVE"
MAIN_SCALE = "Ö:1/50"
SITE_SCALE = "Ö:1/200"
EXPECTED_AB_VIEWS = (
    ("FLOOR_PLAN", "1.BODRUM KAT PLANI", "topology_candidate"),
    ("FLOOR_PLAN", "ZEMİN KAT PLANI", "topology_candidate"),
    ("FLOOR_PLAN", "1.NORMAL KAT PLANI", "topology_candidate"),
    ("FLOOR_PLAN", "Ç.A.P. KAT PLANI", "topology_candidate"),
    ("ROOF_PLAN", "ÇATI PLANI", "roof/reference"),
    ("SECTION", "A-A KESİT", "reference"),
    ("SECTION", "B-B KESİT", "reference"),
    ("ELEVATION", "ÖN", "reference"),
    ("ELEVATION", "SOL YAN", "reference"),
    ("ELEVATION", "ARKA", "reference"),
    ("ELEVATION", "SAĞ YAN", "reference"),
    ("POOL_PROJECT", "HAVUZ PROJESİ", "separate_reference"),
)


def _q(value: float) -> float:
    """Canonical coordinate precision in normalized millimetres."""
    return round(float(value), 4)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _normalize_exact_text(value: str) -> str:
    """Preserve recoverable Turkish text while canonicalizing layout whitespace."""
    value = unicodedata.normalize("NFC", value or "").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", value).strip()


def _normalize_text(value: str) -> str:
    """ASCII-ish matching key; never use this lossy value as displayed evidence."""
    value = _normalize_exact_text(value).translate(str.maketrans({"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G"}))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.upper().replace("�", "?")
    return re.sub(r"[^A-Z0-9?]+", " ", value).strip()


@dataclass(frozen=True)
class AuditEntity:
    source_id: str
    entity_type: str
    layer: str
    bounds: Tuple[float, float, float, float]
    role: str = "structural"
    text: str = ""
    length: float = 0.0
    is_closed: bool = False
    render_points: Tuple[Tuple[float, float], ...] = ()
    root_source_id: str = ""
    insert_ancestry: Tuple[str, ...] = ()

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.bounds[0] + self.bounds[2]) / 2.0, (self.bounds[1] + self.bounds[3]) / 2.0)

    def fingerprint(self) -> str:
        raw = "|".join(
            [
                self.source_id,
                self.entity_type,
                self.layer,
                *(f"{_q(value):.4f}" for value in self.bounds),
                _normalize_text(self.text),
                "closed" if self.is_closed else "open",
                self.root_source_id,
                "/".join(self.insert_ancestry),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class RegionCandidate:
    members: List[AuditEntity]
    annotations: List[AuditEntity] = field(default_factory=list)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return (
            min(entity.bounds[0] for entity in self.members),
            min(entity.bounds[1] for entity in self.members),
            max(entity.bounds[2] for entity in self.members),
            max(entity.bounds[3] for entity in self.members),
        )


@dataclass(frozen=True)
class SourceTitle:
    anchor: AuditEntity
    scope: str
    exact_title: str
    drawing_type: str
    view_name: str
    scale: str
    routing_role: str


@dataclass(frozen=True)
class FrameCandidate:
    frame_id: str
    bounds: Tuple[float, float, float, float]
    source_entity_ids: Tuple[str, ...]
    evidence: str = "closed_cerceve_inset_group"


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[max(left_root, right_root)] = min(left_root, right_root)


class DrawingRegionAudit:
    """Extract, score, and serialize drawing candidates without mutating the DXF."""

    def __init__(self, min_structural_entities: int = 8):
        self.min_structural_entities = min_structural_entities

    @staticmethod
    def _scale_factor(doc: Any) -> Tuple[int, float]:
        insunits = int(doc.header.get("$INSUNITS", 0))
        return insunits, {1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0}.get(insunits, 1.0)

    @staticmethod
    def _entity_geometry(entity: Any, scale: float) -> Optional[Tuple[Tuple[float, float, float, float], float, bool, Tuple[Tuple[float, float], ...]]]:
        kind = entity.dxftype()
        points: List[Tuple[float, float]] = []
        render_points: List[Tuple[float, float]] = []
        length = 0.0
        is_closed = kind == "CIRCLE"
        try:
            if kind == "LINE":
                points = [(entity.dxf.start.x, entity.dxf.start.y), (entity.dxf.end.x, entity.dxf.end.y)]
                render_points = points
            elif kind == "LWPOLYLINE":
                points = [(point[0], point[1]) for point in entity.get_points("xy")]
                render_points = points
                is_closed = bool(entity.closed)
            elif kind == "POLYLINE":
                points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
                render_points = points
                is_closed = bool(entity.is_closed)
            elif kind in {"ARC", "CIRCLE"}:
                center, radius = entity.dxf.center, abs(float(entity.dxf.radius))
                points = [(center.x - radius, center.y - radius), (center.x + radius, center.y + radius)]
                start = 0.0 if kind == "CIRCLE" else float(entity.dxf.start_angle)
                end = 360.0 if kind == "CIRCLE" else float(entity.dxf.end_angle)
                sweep = (end - start) % 360.0
                if kind == "CIRCLE" or sweep == 0.0:
                    sweep = 360.0
                segment_count = max(8, int(math.ceil(48.0 * sweep / 360.0)))
                render_points = [
                    (center.x + radius * math.cos(math.radians(start + sweep * step / segment_count)),
                     center.y + radius * math.sin(math.radians(start + sweep * step / segment_count)))
                    for step in range(segment_count + 1)
                ]
                length = 2.0 * math.pi * radius
                is_closed = kind == "CIRCLE"
            elif kind == "ELLIPSE":
                center = entity.dxf.center
                major = entity.dxf.major_axis
                radius = math.hypot(major.x, major.y)
                points = [(center.x - radius, center.y - radius), (center.x + radius, center.y + radius)]
                tolerance = max(radius / 48.0, 1e-6)
                render_points = [(point.x, point.y) for point in entity.flattening(tolerance, segments=16)]
                is_closed = math.isclose(float(entity.dxf.start_param), 0.0) and math.isclose(float(entity.dxf.end_param), 2.0 * math.pi)
            elif kind == "SPLINE":
                control_points = list(entity.control_points)
                if control_points:
                    points = [(point.x, point.y) for point in control_points]
                    xs = [point.x for point in control_points]
                    ys = [point.y for point in control_points]
                    tolerance = max(math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 48.0, 1e-6)
                    render_points = [(point.x, point.y) for point in entity.flattening(tolerance, segments=8)]
            if not points:
                return None
            scaled = [(x * scale, y * scale) for x, y in points]
            if length == 0.0 and len(scaled) > 1:
                length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(scaled, scaled[1:]))
            xs, ys = [point[0] for point in scaled], [point[1] for point in scaled]
            scaled_render = tuple((_q(x * scale), _q(y * scale)) for x, y in (render_points or points))
            return ((_q(min(xs)), _q(min(ys)), _q(max(xs)), _q(max(ys))), _q(length * scale if kind in {"ARC", "CIRCLE"} else length), is_closed, scaled_render)
        except (AttributeError, TypeError, ValueError):
            return None

    def _audit_entity(
        self,
        entity: Any,
        scale: float,
        source_id: str,
        root_source_id: str,
        ancestry: Tuple[str, ...],
    ) -> Optional[AuditEntity]:
        kind = entity.dxftype()
        layer = str(getattr(entity.dxf, "layer", "0"))
        if kind in STRUCTURAL_TYPES:
            geometry = self._entity_geometry(entity, scale)
            if geometry is None:
                return None
            bounds, length, is_closed, render_points = geometry
            return AuditEntity(
                source_id, kind, layer, bounds, "structural", length=length,
                is_closed=is_closed, render_points=render_points,
                root_source_id=root_source_id, insert_ancestry=ancestry,
            )
        if kind in ANNOTATION_TYPES:
            try:
                insertion = entity.dxf.insert
                text = entity.plain_text() if hasattr(entity, "plain_text") else entity.dxf.text
                point = (_q(insertion.x * scale), _q(insertion.y * scale))
                return AuditEntity(
                    source_id, kind, layer, (*point, *point), "annotation",
                    _normalize_exact_text(str(text)), root_source_id=root_source_id,
                    insert_ancestry=ancestry,
                )
            except (AttributeError, TypeError, ValueError):
                return None
        return None

    def _expand_entity(
        self,
        entity: Any,
        scale: float,
        root_source_id: str,
        source_id: str,
        ancestry: Tuple[str, ...],
        ignored: Counter,
        depth: int = 0,
    ) -> List[AuditEntity]:
        kind = entity.dxftype()
        if kind != "INSERT":
            converted = self._audit_entity(entity, scale, source_id, root_source_id, ancestry)
            if converted is None:
                ignored[f"invalid_{kind}" if kind in STRUCTURAL_TYPES | ANNOTATION_TYPES else kind] += 1
                return []
            return [converted]
        if depth >= 16:
            ignored["INSERT_depth_guard"] += 1
            return []
        block_name = str(getattr(entity.dxf, "name", "<unnamed>"))
        if block_name in ancestry:
            ignored["INSERT_cycle_guard"] += 1
            return []
        try:
            virtual = list(entity.virtual_entities())
        except Exception:  # ezdxf raises several transform-specific exception types
            ignored["invalid_INSERT"] += 1
            return []
        expanded: List[AuditEntity] = []
        next_ancestry = ancestry + (block_name,)
        for ordinal, child in enumerate(virtual):
            child_id = f"{source_id}/v{ordinal:06d}"
            expanded.extend(self._expand_entity(child, scale, root_source_id, child_id, next_ancestry, ignored, depth + 1))
        return expanded

    def read_dxf(self, source_path: Path) -> Tuple[List[AuditEntity], Dict[str, Any]]:
        if ezdxf is None:
            raise ImportError("ezdxf is required for drawing-region audit")
        doc = ezdxf.readfile(source_path)
        insunits, scale = self._scale_factor(doc)
        entities: List[AuditEntity] = []
        ignored = Counter()
        for ordinal, entity in enumerate(doc.modelspace()):
            handle = str(getattr(entity.dxf, "handle", "") or f"ordinal-{ordinal:08d}")
            entities.extend(self._expand_entity(entity, scale, handle, handle, (), ignored))
        entities.sort(key=lambda item: item.fingerprint())
        return entities, {
            "dxf_version": str(doc.dxfversion),
            "insunits": insunits,
            "normalized_unit": "mm",
            "unit_scale_to_mm": scale,
            "modelspace_entity_count": len(doc.modelspace()),
            "audited_entity_count": len(entities),
            "ignored_entity_counts": dict(sorted(ignored.items())),
        }

    @staticmethod
    def _parse_title(anchor: AuditEntity) -> Optional[SourceTitle]:
        exact = _normalize_exact_text(anchor.text)
        key = _normalize_text(exact)
        if "VAZIYET PLANI" in key:
            return SourceTitle(anchor, "site", exact, "SITE_PLAN", "VAZİYET PLANI", SITE_SCALE, "site/reference_evidence")
        scope = "A" if "A BLOK" in key else "B" if "B BLOK" in key else None
        if scope is None:
            return None
        matched: Optional[Tuple[str, str, str]] = None
        if "HAVUZ" in key and "PROJE" in key:
            matched = EXPECTED_AB_VIEWS[-1]
        elif "A A" in key and "KES" in key:
            matched = EXPECTED_AB_VIEWS[5]
        elif "B B" in key and "KES" in key:
            matched = EXPECTED_AB_VIEWS[6]
        elif "SOL YAN" in key:
            matched = EXPECTED_AB_VIEWS[8]
        elif "SAG YAN" in key:
            matched = EXPECTED_AB_VIEWS[10]
        elif "ARKA" in key and "KAT PLANI" not in key:
            matched = EXPECTED_AB_VIEWS[9]
        elif re.search(r"(^| )ON( |$)", key) and "KAT PLANI" not in key:
            matched = EXPECTED_AB_VIEWS[7]
        elif "1 BODRUM" in key and "KAT PLANI" in key:
            matched = EXPECTED_AB_VIEWS[0]
        elif "ZEMIN" in key and "KAT PLANI" in key:
            matched = EXPECTED_AB_VIEWS[1]
        elif "1 NORMAL" in key and "KAT PLANI" in key:
            matched = EXPECTED_AB_VIEWS[2]
        elif ("C A P" in key or "? A P" in key) and "KAT PLANI" in key:
            matched = EXPECTED_AB_VIEWS[3]
        elif "CATI PLANI" in key or "?ATI PLANI" in key:
            matched = EXPECTED_AB_VIEWS[4]
        if matched is None:
            return None
        drawing_type, view_name, routing_role = matched
        return SourceTitle(anchor, scope, exact, drawing_type, view_name, MAIN_SCALE, routing_role)

    @staticmethod
    def _contains(bounds: Tuple[float, float, float, float], point: Tuple[float, float], tolerance: float = 0.5) -> bool:
        return bounds[0] - tolerance <= point[0] <= bounds[2] + tolerance and bounds[1] - tolerance <= point[1] <= bounds[3] + tolerance

    @staticmethod
    def _rect_contains(outer: Tuple[float, float, float, float], inner: Tuple[float, float, float, float], tolerance: float = 0.5) -> bool:
        return outer[0] - tolerance <= inner[0] and outer[1] - tolerance <= inner[1] and outer[2] + tolerance >= inner[2] and outer[3] + tolerance >= inner[3]

    @staticmethod
    def _intersects(left: Tuple[float, float, float, float], right: Tuple[float, float, float, float]) -> bool:
        return not (left[2] < right[0] or right[2] < left[0] or left[3] < right[1] or right[3] < left[1])

    @staticmethod
    def _frame_candidates(entities: Sequence[AuditEntity]) -> List[FrameCandidate]:
        cerceve_polylines = sorted(
            (
                entity for entity in entities
                if entity.role == "structural" and _normalize_text(entity.layer) == FRAME_LAYER_KEY
                and entity.entity_type in {"LWPOLYLINE", "POLYLINE"}
                and entity.bounds[2] - entity.bounds[0] >= 500.0
                and entity.bounds[3] - entity.bounds[1] >= 500.0
            ),
            key=lambda entity: (entity.bounds, entity.source_id),
        )
        rectangles = [entity for entity in cerceve_polylines if entity.is_closed]
        groups: List[List[AuditEntity]] = []
        for rectangle in rectangles:
            cx, cy = rectangle.center
            match = next((group for group in groups if abs(group[0].center[0] - cx) <= 1.0 and abs(group[0].center[1] - cy) <= 1.0
                          and abs((group[0].bounds[2] - group[0].bounds[0]) - (rectangle.bounds[2] - rectangle.bounds[0])) <= 50.0
                          and abs((group[0].bounds[3] - group[0].bounds[1]) - (rectangle.bounds[3] - rectangle.bounds[1])) <= 50.0), None)
            if match is None:
                groups.append([rectangle])
            else:
                match.append(rectangle)
        candidates: List[FrameCandidate] = []
        for group in groups:
            if len(group) < 3:
                continue
            outer = max(group, key=lambda entity: (entity.bounds[2] - entity.bounds[0]) * (entity.bounds[3] - entity.bounds[1]))
            ids = tuple(sorted(entity.source_id for entity in group))
            frame_id = "frame-" + hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()[:16]
            candidates.append(FrameCandidate(frame_id, outer.bounds, ids))

        # The three site sheets use an actual open outer CERCEVE polyline and a
        # closed inset polyline instead of the three closed insets used by the
        # A/B cells. Reconstruct only tightly nested, independently evidenced
        # pairs; unrelated open CERCEVE geometry cannot become a frame.
        used_outer_ids = {source_id for candidate in candidates for source_id in candidate.source_entity_ids}
        for outer in (entity for entity in cerceve_polylines if not entity.is_closed and entity.source_id not in used_outer_ids):
            nested = []
            for inner in rectangles:
                if not DrawingRegionAudit._rect_contains(outer.bounds, inner.bounds, 0.5):
                    continue
                margins = (
                    inner.bounds[0] - outer.bounds[0], inner.bounds[1] - outer.bounds[1],
                    outer.bounds[2] - inner.bounds[2], outer.bounds[3] - inner.bounds[3],
                )
                if all(0.0 <= margin <= 100.0 for margin in margins):
                    nested.append(inner)
            if len(nested) != 1:
                continue
            inner = nested[0]
            ids = tuple(sorted((outer.source_id, inner.source_id)))
            frame_id = "frame-" + hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()[:16]
            candidates.append(FrameCandidate(frame_id, outer.bounds, ids, "open_cerceve_outer_with_closed_inset"))
        return sorted(candidates, key=lambda frame: (frame.bounds, frame.frame_id))

    @staticmethod
    def _pool_separator(frame: FrameCandidate, titles: Sequence[SourceTitle], entities: Sequence[AuditEntity]) -> Optional[AuditEntity]:
        if len(titles) != 2:
            return None
        low_y, high_y = sorted(title.anchor.center[1] for title in titles)
        width = frame.bounds[2] - frame.bounds[0]
        matches = []
        for entity in entities:
            if entity.entity_type != "LINE" or _normalize_text(entity.layer) != FRAME_LAYER_KEY:
                continue
            x1, y1, x2, y2 = entity.bounds
            if low_y < y1 < high_y and abs(y2 - y1) <= 0.5 and x2 - x1 >= width * 0.8 and DrawingRegionAudit._rect_contains(frame.bounds, entity.bounds, 1.0):
                matches.append(entity)
        return min(matches, key=lambda entity: (abs(entity.center[1] - (low_y + high_y) / 2.0), entity.source_id)) if matches else None

    def build_source_views(self, entities: Sequence[AuditEntity]) -> Dict[str, Any]:
        titles = sorted(filter(None, (self._parse_title(entity) for entity in entities if entity.role == "annotation")), key=lambda title: (title.scope, title.view_name, title.anchor.source_id))
        expected = {(scope, view_name) for scope in ("A", "B") for _, view_name, _ in EXPECTED_AB_VIEWS}
        actual_keys = [(title.scope, title.view_name) for title in titles if title.scope in {"A", "B"}]
        duplicate_keys = sorted(key for key, count in Counter(actual_keys).items() if count != 1)
        missing_keys = sorted(expected - set(actual_keys))
        site_titles = [title for title in titles if title.scope == "site"]
        if missing_keys or duplicate_keys or len(site_titles) != 3:
            return {"status": "blocked", "reason": "title_catalog_mismatch", "missing": missing_keys, "duplicate_or_conflicting": duplicate_keys, "site_count": len(site_titles), "views": []}

        frames = self._frame_candidates(entities)
        logical: List[Tuple[SourceTitle, FrameCandidate]] = []
        conflicts: List[Dict[str, Any]] = []
        for frame in frames:
            anchored = [title for title in titles if self._contains(frame.bounds, title.anchor.center)]
            if not anchored:
                continue
            if len(anchored) == 1:
                logical.append((anchored[0], frame))
                continue
            if len(anchored) == 2 and all(title.drawing_type == "POOL_PROJECT" for title in anchored):
                separator = self._pool_separator(frame, anchored, entities)
                if separator is None:
                    conflicts.append({"frame_id": frame.frame_id, "reason": "pool_separator_missing", "title_ids": sorted(title.anchor.source_id for title in anchored)})
                    continue
                split_y = separator.center[1]
                for title in anchored:
                    bounds = (frame.bounds[0], frame.bounds[1] if title.anchor.center[1] < split_y else split_y, frame.bounds[2], split_y if title.anchor.center[1] < split_y else frame.bounds[3])
                    suffix = "lower" if title.anchor.center[1] < split_y else "upper"
                    logical.append((title, FrameCandidate(f"{frame.frame_id}-{suffix}", bounds, frame.source_entity_ids + (separator.source_id,), "closed_cerceve_group_with_actual_separator")))
            else:
                conflicts.append({"frame_id": frame.frame_id, "reason": "multiple_title_anchors", "title_ids": sorted(title.anchor.source_id for title in anchored)})
        mapped_ids = [title.anchor.source_id for title, _ in logical]
        unmapped = sorted(title.anchor.source_id for title in titles if title.anchor.source_id not in mapped_ids)
        if conflicts or unmapped or len(logical) != 27:
            return {"status": "blocked", "reason": "frame_association_conflict", "conflicts": conflicts, "unmapped_title_ids": unmapped, "views": []}

        frame_source_ids = {source_id for _, frame in logical for source_id in frame.source_entity_ids}
        structural = [entity for entity in entities if entity.role == "structural" and entity.source_id not in frame_source_ids]
        ownership: Dict[str, List[str]] = {}
        crossing: Dict[str, List[str]] = {}
        for entity in structural:
            contained = [frame.frame_id for _, frame in logical if self._rect_contains(frame.bounds, entity.bounds)]
            intersected = [frame.frame_id for _, frame in logical if self._intersects(frame.bounds, entity.bounds) and frame.frame_id not in contained]
            if contained:
                ownership[entity.source_id] = contained
            if intersected:
                crossing[entity.source_id] = intersected
        views = []
        for title, frame in logical:
            assigned_ids = sorted(source_id for source_id, owners in ownership.items() if owners == [frame.frame_id])
            multiply_ids = sorted(source_id for source_id, owners in ownership.items() if frame.frame_id in owners and len(owners) > 1)
            crossing_ids = sorted(source_id for source_id, frames_for_entity in crossing.items() if frame.frame_id in frames_for_entity)
            stable_key = f"{title.scope}|{title.drawing_type}|{title.view_name}|{title.anchor.source_id}|{'|'.join(frame.source_entity_ids)}"
            views.append({
                "view_id": "source-view-" + hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16],
                "scope": title.scope, "exact_normalized_title": title.exact_title,
                "drawing_type": title.drawing_type, "level_or_view_name": title.view_name,
                "scale": title.scale, "frame_id": frame.frame_id,
                "frame_bounds_mm": {"min_x": frame.bounds[0], "min_y": frame.bounds[1], "max_x": frame.bounds[2], "max_y": frame.bounds[3]},
                "assigned_entity_ids": assigned_ids, "assigned_entity_count": len(assigned_ids),
                "crossing_entity_ids": crossing_ids, "multiply_assignable_entity_ids": multiply_ids,
                "evidence": [frame.evidence, f"title_anchor:{title.anchor.source_id}"],
                "confidence": 1.0, "routing_role": title.routing_role,
            })
        views.sort(key=lambda view: (view["scope"], view["drawing_type"], view["level_or_view_name"], view["view_id"]))
        assigned_once = {source_id for source_id, owners in ownership.items() if len(owners) == 1}
        multiply = sorted(source_id for source_id, owners in ownership.items() if len(owners) > 1)
        unassigned = sorted(entity.source_id for entity in structural if entity.source_id not in ownership and entity.source_id not in crossing)
        routing = Counter(view["drawing_type"] for view in views)
        return {
            "status": "ready_for_review", "reason": None, "views": views,
            "summary": {"view_count": len(views), "floor_plan_count": routing["FLOOR_PLAN"], "routing_type_counts": dict(sorted(routing.items()))},
            "assignment": {"assigned_once_count": len(assigned_once), "multiply_assignable_entity_ids": multiply, "crossing_entity_ids": sorted(crossing), "unassigned_entity_ids": unassigned},
        }

    @staticmethod
    def _entity_signature(entity: AuditEntity, origin_x: float = 0.0, origin_y: float = 0.0, mirror_x: Optional[float] = None) -> Tuple[Any, ...]:
        points = entity.render_points or ((entity.bounds[0], entity.bounds[1]), (entity.bounds[2], entity.bounds[3]))
        normalized = []
        for x, y in points:
            local_x, local_y = _q(x - origin_x), _q(y - origin_y)
            normalized.append((_q(mirror_x - local_x) if mirror_x is not None else local_x, local_y))
        if entity.is_closed and len(normalized) > 1:
            if normalized[0] == normalized[-1]:
                normalized.pop()
            rotations = [tuple(normalized[index:] + normalized[:index]) for index in range(len(normalized))]
            reversed_points = list(reversed(normalized))
            rotations.extend(tuple(reversed_points[index:] + reversed_points[:index]) for index in range(len(reversed_points)))
            canonical_points = min(rotations)
        else:
            forward = tuple(normalized)
            reverse = tuple(reversed(normalized))
            canonical_points = min(forward, reverse)
        return entity.entity_type, _normalize_text(entity.layer), entity.is_closed, canonical_points

    def compare_ab_views(self, source_views: Dict[str, Any], entities: Sequence[AuditEntity]) -> List[Dict[str, Any]]:
        """Classify A/B evidence without merging or deduplicating either source view."""
        if source_views.get("status") != "ready_for_review":
            return []
        entity_by_id = {entity.source_id: entity for entity in entities}
        indexed = {(view["scope"], view["drawing_type"], view["level_or_view_name"]): view for view in source_views["views"] if view["scope"] in {"A", "B"}}
        comparisons = []
        for drawing_type, view_name, _ in EXPECTED_AB_VIEWS:
            left, right = indexed[("A", drawing_type, view_name)], indexed[("B", drawing_type, view_name)]
            left_entities = [entity_by_id[item] for item in left["assigned_entity_ids"] if item in entity_by_id]
            right_entities = [entity_by_id[item] for item in right["assigned_entity_ids"] if item in entity_by_id]
            classification = "not-proven"
            evidence = "insufficient_comparable_geometry"
            if left_entities and right_entities:
                absolute_left = sorted(self._entity_signature(item) for item in left_entities)
                absolute_right = sorted(self._entity_signature(item) for item in right_entities)
                lb, rb = left["frame_bounds_mm"], right["frame_bounds_mm"]
                local_left = sorted(self._entity_signature(item, lb["min_x"], lb["min_y"]) for item in left_entities)
                local_right = sorted(self._entity_signature(item, rb["min_x"], rb["min_y"]) for item in right_entities)
                width = _q(rb["max_x"] - rb["min_x"])
                mirrored_right = sorted(self._entity_signature(item, rb["min_x"], rb["min_y"], width) for item in right_entities)
                if absolute_left == absolute_right:
                    classification, evidence = "exact", "absolute_geometry_signature_equal"
                elif local_left == local_right:
                    classification, evidence = "translation-equivalent", "frame_local_geometry_signature_equal"
                elif local_left == mirrored_right:
                    classification, evidence = "mirror-candidate", "frame_local_x_mirror_signature_equal"
                else:
                    classification, evidence = "different", "canonical_geometry_signatures_differ"
            comparisons.append({
                "drawing_type": drawing_type, "level_or_view_name": view_name,
                "a_view_id": left["view_id"], "b_view_id": right["view_id"],
                "classification": classification, "evidence": evidence,
                "a_entity_count": len(left_entities), "b_entity_count": len(right_entities),
                "deduplication_performed": False,
            })
        return comparisons

    @staticmethod
    def _geometry_input(view: Dict[str, Any], entity_by_id: Dict[str, AuditEntity]) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """Serialize only assigned source entities to the frozen GeometryEngine contract."""
        converted: List[Dict[str, Any]] = []
        rejected: Counter = Counter()
        for source_id in view["assigned_entity_ids"]:
            entity = entity_by_id.get(source_id)
            if entity is None:
                rejected["missing_source_entity"] += 1
                continue
            if entity.entity_type not in {"LINE", "LWPOLYLINE", "POLYLINE"}:
                rejected[f"unsupported_{entity.entity_type}"] += 1
                continue
            points = entity.render_points
            if len(points) < 2:
                rejected["insufficient_render_points"] += 1
                continue
            common = {
                "source_id": entity.source_id,
                "type": entity.entity_type,
                "layer": entity.layer,
                "block_name": entity.insert_ancestry[-1] if entity.insert_ancestry else "modelspace",
            }
            if entity.entity_type == "LINE":
                common.update({
                    "start": {"x": _q(points[0][0]), "y": _q(points[0][1])},
                    "end": {"x": _q(points[-1][0]), "y": _q(points[-1][1])},
                })
            else:
                common.update({
                    "vertices": [{"x": _q(x), "y": _q(y)} for x, y in points],
                    "closed": bool(entity.is_closed),
                })
            converted.append(common)
        bounds = view["frame_bounds_mm"]
        payload = {
            "bounding_box": {key: _q(bounds[key]) for key in ("min_x", "min_y", "max_x", "max_y")},
            "entities": sorted(converted, key=lambda item: item["source_id"]),
        }
        return payload, dict(sorted(rejected.items()))

    @staticmethod
    def _graph_diagnostics(graph: Dict[str, Any], min_loop_area: float) -> Dict[str, Any]:
        nodes, edges, loops = graph.get("nodes", []), graph.get("edges", []), graph.get("loops", [])
        node_ids = [int(node.get("id", index)) for index, node in enumerate(nodes)]
        adjacency = {node_id: set() for node_id in node_ids}
        degrees = Counter({node_id: 0 for node_id in node_ids})
        for edge in edges:
            start, end = int(edge["from"]), int(edge["to"])
            if start in adjacency and end in adjacency:
                adjacency[start].add(end)
                adjacency[end].add(start)
                degrees[start] += 2 if start == end else 1
                if start != end:
                    degrees[end] += 1
        unvisited, component_count = set(node_ids), 0
        while unvisited:
            component_count += 1
            stack = [unvisited.pop()]
            while stack:
                for neighbor in adjacency[stack.pop()] & unvisited:
                    unvisited.remove(neighbor)
                    stack.append(neighbor)
        tiny = sorted(loop.get("id", index) for index, loop in enumerate(loops) if float(loop.get("area", 0.0)) <= min_loop_area)
        dangling = sorted(node_id for node_id, degree in degrees.items() if degree == 1)
        return {
            "component_count": component_count,
            "dangling_node_count": len(dangling), "dangling_node_ids": dangling,
            "tiny_sliver_loop_count": len(tiny), "tiny_sliver_loop_ids": tiny,
        }

    @staticmethod
    def _topology_snapshot(graph: Dict[str, Any], include_connectors: bool = False) -> Dict[str, Any]:
        """Return the deterministic topology evidence subset used by the AG-04 safety gate."""
        snapshot = {
            "nodes": copy.deepcopy(graph.get("nodes", [])),
            "edges": copy.deepcopy(graph.get("edges", [])),
            "loops": copy.deepcopy(graph.get("loops", [])),
        }
        if include_connectors:
            snapshot.update(
                {
                    "logical_connectors": copy.deepcopy(graph.get("logical_connectors", [])),
                    "logical_connector_rejections": copy.deepcopy(
                        graph.get("logical_connector_rejections", [])
                    ),
                }
            )
        return snapshot

    @staticmethod
    def _snapshot_sha256(snapshot: Dict[str, Any]) -> str:
        return hashlib.sha256(_canonical_json(snapshot).encode("utf-8")).hexdigest()

    @staticmethod
    def _health_evidence(report: Dict[str, Any]) -> Dict[str, Any]:
        """Strip the reporter timestamp while retaining all deterministic diagnostics."""
        return {
            key: copy.deepcopy(report[key])
            for key in ("status", "counts", "graph_metrics", "loop_metrics", "checks", "issues", "diagnostics")
        }

    @staticmethod
    def _validator_outcome(validator: Any, graph: Dict[str, Any]) -> Dict[str, Any]:
        from backend.topology_validator import TopologyValidationError

        try:
            validator.validate(graph)
            return {"status": "VALIDATOR_PASS", "failed_checks": []}
        except TopologyValidationError as exc:
            return {"status": "VALIDATOR_FAIL", "failed_checks": [str(exc)]}

    def qualify_floor_topology(
        self,
        source_views: Dict[str, Any],
        entities: Sequence[AuditEntity],
        include_transient_connectors: bool = False,
    ) -> List[Dict[str, Any]]:
        """Run isolated floor qualification; optionally add an AG-04 candidate projection."""
        if source_views.get("status") != "ready_for_review":
            return []

        from backend.constraint_solver import ConstraintSolver
        from backend.geometry_engine import GeometryEngine
        from backend.topology_engine import TopologyEngine
        from backend.topology_health_report import TopologyHealthReporter
        from backend.topology_validator import TopologyValidator
        from backend.transient_boundary_connectors import generate_logical_connectors

        entity_by_id = {entity.source_id: entity for entity in entities}
        results = []
        for view in (item for item in source_views["views"] if item["drawing_type"] == "FLOOR_PLAN"):
            raw_input, conversion_reasons = self._geometry_input(view, entity_by_id)
            result = {
                "view_id": view["view_id"], "scope": view["scope"], "level_or_view_name": view["level_or_view_name"],
                "assigned_source_entity_count": len(view["assigned_entity_ids"]),
                "geometry_input_entity_count": len(raw_input["entities"]),
                "geometry_conversion_rejected_count": sum(conversion_reasons.values()),
                "geometry_conversion_rejection_reasons": conversion_reasons,
                "geometry_accepted_entity_count": 0, "geometry_rejected_entity_count": 0,
                "geometry_rejection_reasons": {}, "wall_segment_count": 0, "input_segment_count": 0,
                "node_count": 0, "edge_count": 0, "loop_count": 0, "component_count": 0,
                "dangling_node_count": 0, "dangling_node_ids": [],
                "tiny_sliver_loop_count": 0, "tiny_sliver_loop_ids": [],
                "configured_tolerances_unchanged": {}, "geometry_stats": {}, "topology_stats": {},
                "geometry_sha256": "", "topology_sha256": "",
                "status": "NOT_EVALUATED", "failed_checks": [], "downstream": {"executed": False},
            }
            with tempfile.TemporaryDirectory(prefix="karar-source-view-topology-") as temporary:
                root = Path(temporary)
                (root / "outputs").mkdir()
                (root / "outputs" / "dxf_raw.json").write_text(_canonical_json(raw_input), encoding="utf-8", newline="")

                class _IsolatedPaths:
                    @staticmethod
                    def get_path(category: str, name: str) -> str:
                        return str(root / category / name)

                    @staticmethod
                    def get_relative_path(path: str) -> str:
                        return Path(path).name

                try:
                    geometry = GeometryEngine()
                    geometry.path_manager = _IsolatedPaths()
                    walls = geometry.run()
                    accepted = int(geometry.stats["initial_entities"])
                    rejected = len(raw_input["entities"]) - accepted
                    result.update({
                        "geometry_accepted_entity_count": accepted,
                        "geometry_rejected_entity_count": rejected,
                        "geometry_rejection_reasons": {"non_wall_layer": rejected},
                        "wall_segment_count": len(walls), "input_segment_count": len(walls),
                        "geometry_stats": {key: value for key, value in geometry.stats.items() if key != "processing_time_ms"},
                        "geometry_sha256": geometry.stats.get("geometry_sha256", ""),
                    })
                    topology = TopologyEngine()
                    configured = {"snap_tolerance_mm": float(topology.snap_tolerance), "min_segment_length_mm": float(topology.min_segment_length)}
                    result["configured_tolerances_unchanged"] = configured
                    topology.path_manager = _IsolatedPaths()
                    graph = topology.run() or {"nodes": [], "edges": [], "loops": []}
                    validator = TopologyValidator(report_output_path=str(root / "outputs" / "topology_validation_report.json"))
                    result.update(self._graph_diagnostics(graph, validator.min_loop_area))
                    result.update({
                        "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]), "loop_count": len(graph["loops"]),
                        "topology_stats": {key: value for key, value in topology.stats.items() if key != "processing_time_ms"},
                        "topology_sha256": topology.stats.get("topology_sha256", ""),
                    })
                    baseline_outcome = self._validator_outcome(validator, graph)
                    result.update(baseline_outcome)

                    if include_transient_connectors:
                        baseline_snapshot = self._topology_snapshot(graph)
                        baseline_health = self._health_evidence(TopologyHealthReporter().build_report(graph))
                        assigned_sources = [
                            entity_by_id[source_id]
                            for source_id in view["assigned_entity_ids"]
                            if source_id in entity_by_id
                        ]
                        generation = generate_logical_connectors(graph, assigned_sources)
                        candidate_input = copy.deepcopy(graph)
                        candidate_input["logical_connectors"] = generation["logical_connectors"]

                        solver = ConstraintSolver()
                        solver.path_manager = _IsolatedPaths()
                        candidate_graph = solver.run(candidate_input)
                        physical_graph_unchanged = all(
                            candidate_graph.get(key, []) == graph.get(key, [])
                            for key in ("nodes", "edges", "loops")
                        )
                        candidate_health = self._health_evidence(
                            TopologyHealthReporter().build_report(candidate_graph)
                        )
                        if physical_graph_unchanged:
                            candidate_validator = TopologyValidator(
                                report_output_path=str(
                                    root / "outputs" / "topology_validation_candidate_report.json"
                                )
                            )
                            candidate_outcome = self._validator_outcome(
                                candidate_validator, candidate_graph
                            )
                        else:
                            candidate_outcome = {
                                "status": "NOT_EVALUATED",
                                "failed_checks": ["PHYSICAL_GRAPH_CHANGED_BY_TRANSIENT_CONNECTOR_HANDOFF"],
                            }

                        candidate_snapshot = self._topology_snapshot(
                            candidate_graph, include_connectors=True
                        )
                        result.update(
                            {
                                "baseline": {
                                    **baseline_outcome,
                                    "snapshot_sha256": self._snapshot_sha256(baseline_snapshot),
                                    "health": baseline_health,
                                },
                                "candidate": {
                                    **candidate_outcome,
                                    "snapshot_sha256": self._snapshot_sha256(candidate_snapshot),
                                    "physical_graph_unchanged": physical_graph_unchanged,
                                    "logical_connectors": candidate_graph.get(
                                        "logical_connectors", []
                                    ),
                                    "logical_connector_generation_rejections": generation[
                                        "rejections"
                                    ],
                                    "logical_connector_validation_rejections": candidate_graph.get(
                                        "logical_connector_rejections", []
                                    ),
                                    "health": candidate_health,
                                },
                            }
                        )
                except Exception as exc:
                    result["failed_checks"] = [f"Pipeline not evaluated: {type(exc).__name__}: {exc}"]
            results.append(result)
        return sorted(results, key=lambda item: item["view_id"])

    @staticmethod
    def _thresholds(structural: Sequence[AuditEntity]) -> Dict[str, float]:
        positive = sorted(entity.length for entity in structural if entity.length > 1e-6)
        median = statistics.median(positive) if positive else 1000.0
        deviations = sorted(abs(value - median) for value in positive)
        mad = statistics.median(deviations) if deviations else 0.0
        # Local connectivity cannot grow without bound on drawings containing grid lines.
        proximity = min(max(median * 0.20, 100.0), 500.0)
        annotation_distance = min(max(median * 1.50, 750.0), 3000.0)
        spans = sorted(max(entity.bounds[2] - entity.bounds[0], entity.bounds[3] - entity.bounds[1]) for entity in structural)
        span_p95 = DrawingRegionAudit._percentile(spans, 0.95) if spans else 0.0
        median_span = statistics.median(spans) if spans else 0.0
        # A connector much larger than ordinary local geometry is retained as
        # evidence, but cannot merge otherwise independent drawing graphs. The
        # robust basis prevents one frame from inflating its own cutoff in small
        # samples; shape/closure remains an additional mandatory condition.
        robust_span_basis = min(span_p95, median_span * 3.0)
        bridge_span = max(2000.0, robust_span_basis * 3.0)
        return {
            "positive_length_count": len(positive),
            "median_length_mm": _q(median),
            "mad_length_mm": _q(mad),
            "structural_proximity_mm": _q(proximity),
            "annotation_attachment_mm": _q(annotation_distance),
            "span_p95_mm": _q(span_p95),
            "median_span_mm": _q(median_span),
            "robust_span_basis_mm": _q(robust_span_basis),
            "bridge_suppression_span_mm": _q(bridge_span),
        }

    @staticmethod
    def _percentile(values: Sequence[float], fraction: float) -> float:
        if not values:
            return 0.0
        position = (len(values) - 1) * fraction
        lower = int(math.floor(position))
        upper = int(math.ceil(position))
        if lower == upper:
            return float(values[lower])
        weight = position - lower
        return float(values[lower] * (1.0 - weight) + values[upper] * weight)

    @staticmethod
    def _is_bridge_context(entity: AuditEntity, span_threshold: float) -> bool:
        width = entity.bounds[2] - entity.bounds[0]
        height = entity.bounds[3] - entity.bounds[1]
        span = max(width, height)
        aspect = span / max(min(width, height), 1e-9)
        return span > span_threshold and (entity.is_closed or aspect >= 20.0)

    @staticmethod
    def _expanded(bounds: Tuple[float, float, float, float], amount: float) -> Tuple[float, float, float, float]:
        return bounds[0] - amount, bounds[1] - amount, bounds[2] + amount, bounds[3] + amount

    def extract_candidates(self, entities: Sequence[AuditEntity]) -> Tuple[List[RegionCandidate], Dict[str, Any]]:
        structural = sorted((entity for entity in entities if entity.role == "structural"), key=lambda item: item.fingerprint())
        annotations = sorted((entity for entity in entities if entity.role == "annotation"), key=lambda item: item.fingerprint())
        thresholds = self._thresholds(structural)
        proximity = thresholds["structural_proximity_mm"]
        bridge_span = thresholds["bridge_suppression_span_mm"]
        connectors = [entity for entity in structural if not self._is_bridge_context(entity, bridge_span)]
        suppressed = [entity for entity in structural if self._is_bridge_context(entity, bridge_span)]
        thresholds["connectivity_entity_count"] = len(connectors)
        thresholds["bridge_context_entity_count"] = len(suppressed)
        spatial = index.Index()
        for identifier, entity in enumerate(connectors):
            spatial.insert(identifier, entity.bounds)
        union = _UnionFind(len(connectors))
        for identifier, entity in enumerate(connectors):
            for other in sorted(spatial.intersection(self._expanded(entity.bounds, proximity))):
                if other > identifier:
                    union.union(identifier, other)
        groups: Dict[int, List[AuditEntity]] = {}
        for identifier, entity in enumerate(connectors):
            groups.setdefault(union.find(identifier), []).append(entity)
        candidates = [RegionCandidate(sorted(group, key=lambda item: item.fingerprint())) for group in groups.values() if len(group) >= self.min_structural_entities]
        candidates.sort(key=lambda candidate: (candidate.bounds, [member.fingerprint() for member in candidate.members]))

        attachment = thresholds["annotation_attachment_mm"]
        for annotation in annotations:
            x, y = annotation.center
            matches: List[Tuple[float, int]] = []
            for candidate_index, candidate in enumerate(candidates):
                min_x, min_y, max_x, max_y = candidate.bounds
                dx = max(min_x - x, 0.0, x - max_x)
                dy = max(min_y - y, 0.0, y - max_y)
                distance = math.hypot(dx, dy)
                if distance <= attachment:
                    matches.append((distance, candidate_index))
            if matches:
                _, selected = min(matches)
                candidates[selected].annotations.append(annotation)
        return candidates, thresholds

    @staticmethod
    def _classify(candidate: RegionCandidate) -> Dict[str, Any]:
        texts = sorted({_normalize_text(entity.text) for entity in candidate.annotations if entity.text.strip()})
        joined = " | ".join(texts)
        keywords = {
            "floor_plan": ("MUTFAK", "SALON", "BANYO", "Y ODASI", "HOL", "KAT PLANI", "ZEMIN KAT"),
            "section": ("KESIT", "KES?T", "A A", "B B"),
            "elevation": ("GORUNUS", "G?R?N??", "CEPHE", "ON GOR", "ARKA GOR", "YAN GOR"),
            "roof_plan": ("CATI", "C?ATI", "ÇATI", "ROOF"),
            "site_plan": ("VAZIYET", "SITE PLAN", "PARSEL"),
        }
        scores = {name: 0.0 for name in CLASS_NAMES}
        evidence: Dict[str, List[str]] = {name: [] for name in CLASS_NAMES}
        for name, terms in keywords.items():
            for term in terms:
                normalized_term = _normalize_text(term)
                if normalized_term and normalized_term in joined:
                    scores[name] += 1.0
                    evidence[name].append(term)
        types = Counter(entity.entity_type for entity in candidate.members)
        closed_count = sum(1 for entity in candidate.members if entity.is_closed)
        if closed_count / max(len(candidate.members), 1) >= 0.08:
            scores["floor_plan"] += 0.25
            evidence["floor_plan"].append("closed_geometry_density>=0.08")
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        best_name, best_score = ranked[0]
        margin = best_score - ranked[1][1]
        strong_classes = [name for name, score in ranked if score >= 1.0]
        conflicting = len(strong_classes) >= 2
        status = "candidate" if best_score >= 1.0 and margin >= 0.5 and not conflicting else "ambiguous"
        ambiguity_reason = None
        if conflicting:
            ambiguity_reason = "conflicting_drawing_type_evidence"
        elif status == "ambiguous":
            ambiguity_reason = "insufficient_or_low_margin_evidence"
        return {
            "status": status,
            "predicted_type": best_name if status == "candidate" else None,
            "confidence": _q(min(best_score / 3.0, 1.0)) if status == "candidate" else 0.0,
            "score_margin": _q(margin),
            "ambiguity_reason": ambiguity_reason,
            "scores": {name: _q(scores[name]) for name in CLASS_NAMES},
            "evidence": {name: sorted(evidence[name]) for name in CLASS_NAMES if evidence[name]},
            "structural_type_counts": dict(sorted(types.items())),
        }

    def build_report(self, source_path: Path, entities: Sequence[AuditEntity], metadata: Dict[str, Any], source_display_path: Optional[str] = None) -> Dict[str, Any]:
        candidates, thresholds = self.extract_candidates(entities)
        source_views = self.build_source_views(entities)
        ab_comparisons = self.compare_ab_views(source_views, entities)
        floor_topology = self.qualify_floor_topology(
            source_views, entities, include_transient_connectors=True
        )
        assigned = {member.fingerprint() for candidate in candidates for member in candidate.members}
        structural = [entity for entity in entities if entity.role == "structural"]
        bridge_context = sorted(
            (entity for entity in structural if self._is_bridge_context(entity, thresholds["bridge_suppression_span_mm"])),
            key=lambda entity: entity.fingerprint(),
        )
        regions = []
        for candidate in candidates:
            fingerprints = sorted(member.fingerprint() for member in candidate.members)
            region_id = "region-" + hashlib.sha256("\n".join(fingerprints).encode("ascii")).hexdigest()[:16]
            bounds = candidate.bounds
            classification = self._classify(candidate)
            regions.append(
                {
                    "region_id": region_id,
                    "bounds_mm": {"min_x": _q(bounds[0]), "min_y": _q(bounds[1]), "max_x": _q(bounds[2]), "max_y": _q(bounds[3])},
                    "width_mm": _q(bounds[2] - bounds[0]),
                    "height_mm": _q(bounds[3] - bounds[1]),
                    "structural_entity_count": len(candidate.members),
                    "annotation_count": len(candidate.annotations),
                    "layers": dict(sorted(Counter(member.layer for member in candidate.members).items())),
                    "nearby_texts": sorted({annotation.text.strip() for annotation in candidate.annotations if annotation.text.strip()}),
                    "source_entity_ids": sorted(member.source_id for member in candidate.members),
                    "_render_geometry": [
                        {
                            "source_id": member.source_id,
                            "closed": member.is_closed,
                            "points_mm": [list(point) for point in (member.render_points or ((member.bounds[0], member.bounds[1]), (member.bounds[2], member.bounds[3])))],
                        }
                        for member in sorted(candidate.members, key=lambda item: item.fingerprint())
                    ],
                    "classification": classification,
                }
            )
        regions.sort(key=lambda region: (region["bounds_mm"]["min_x"], region["bounds_mm"]["min_y"], region["region_id"]))
        return {
            "schema_version": SCHEMA_VERSION,
            "audit_mode": "read_only_evidence_only",
            "source": {"path": source_display_path or source_path.name, "sha256": _sha256(source_path), **metadata},
            "source_view_status": (
                "SOURCE_VIEWS_READY_FOR_REVIEW"
                if source_views.get("status") == "ready_for_review"
                else f"BLOCKED_SOURCE_VIEW_ISOLATION_{source_views.get('reason', 'UNKNOWN').upper()}"
            ),
            "source_views": source_views,
            "ab_comparisons": ab_comparisons,
            "floor_topology_qualification": floor_topology,
            "_source_render_geometry": [
                {
                    "source_id": entity.source_id,
                    "closed": entity.is_closed,
                    "points_mm": [list(point) for point in (entity.render_points or ((entity.bounds[0], entity.bounds[1]), (entity.bounds[2], entity.bounds[3])))],
                }
                for entity in sorted(entities, key=lambda item: item.fingerprint())
                if entity.role == "structural"
            ],
            "threshold_policy": {"basis": "median_length_and_p95_span_with_bounded_mm_limits", **thresholds},
            "bridge_context": {
                "entity_count": len(bridge_context),
                "source_entity_ids": [entity.source_id for entity in bridge_context],
                "policy": "retained_as_evidence_but_excluded_from_connectivity",
            },
            "invariants": {
                "structural_entity_count": len(structural),
                "assigned_structural_entity_count": len(assigned),
                "unassigned_structural_entity_count": len(structural) - len(assigned),
                "bridge_context_entity_count": len(bridge_context),
                "duplicate_structural_assignment_count": sum(len(candidate.members) for candidate in candidates) - len(assigned),
                "cross_region_edges_created": 0,
            },
            "summary": {
                "region_count": len(regions),
                "candidate_count": sum(region["classification"]["status"] == "candidate" for region in regions),
                "ambiguous_count": sum(region["classification"]["status"] == "ambiguous" for region in regions),
            },
            "regions": regions,
        }

    @staticmethod
    def _csv(report: Dict[str, Any]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["region_id", "status", "predicted_type", "confidence", "score_margin", "entity_count", "annotation_count", "min_x_mm", "min_y_mm", "max_x_mm", "max_y_mm", "evidence"])
        for region in report["regions"]:
            classification, bounds = region["classification"], region["bounds_mm"]
            evidence = ";".join(f"{name}:{'|'.join(values)}" for name, values in sorted(classification["evidence"].items()))
            writer.writerow([region["region_id"], classification["status"], classification["predicted_type"] or "", classification["confidence"], classification["score_margin"], region["structural_entity_count"], region["annotation_count"], bounds["min_x"], bounds["min_y"], bounds["max_x"], bounds["max_y"], evidence])
        return output.getvalue()

    @staticmethod
    def _svg(report: Dict[str, Any]) -> str:
        regions = report["regions"]
        if not regions:
            return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><text x="20" y="30">No drawing regions detected</text></svg>\n'
        min_x = min(region["bounds_mm"]["min_x"] for region in regions)
        min_y = min(region["bounds_mm"]["min_y"] for region in regions)
        max_x = max(region["bounds_mm"]["max_x"] for region in regions)
        max_y = max(region["bounds_mm"]["max_y"] for region in regions)
        plot_width, legend_width, height, margin = 1200.0, 420.0, 800.0, 30.0
        width = plot_width + legend_width
        scale = min((plot_width - 2 * margin) / max(max_x - min_x, 1.0), (height - 2 * margin) / max(max_y - min_y, 1.0))
        palette = ("#55d6be", "#ffd166", "#ef476f", "#118ab2", "#c77dff", "#f8961e", "#90be6d", "#f9844a", "#43aa8b", "#577590", "#e0aaff", "#4cc9f0")
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">',
            '<rect width="100%" height="100%" fill="#101820"/>',
            f'<rect x="{plot_width:.0f}" width="{legend_width:.0f}" height="100%" fill="#17232d"/>',
            '<g id="drawing-geometry" fill="none" stroke-linecap="round" stroke-linejoin="round">',
        ]
        for region_index, region in enumerate(regions):
            color = palette[region_index % len(palette)]
            lines.append(f'<g id="{region["region_id"]}" data-status="{region["classification"]["status"]}" stroke="{color}" stroke-width="0.75">')
            for primitive in region.get("_render_geometry", []):
                transformed = [
                    (margin + (point[0] - min_x) * scale, height - margin - (point[1] - min_y) * scale)
                    for point in primitive["points_mm"]
                ]
                if len(transformed) < 2:
                    continue
                points = " ".join(f"{x:.3f},{y:.3f}" for x, y in transformed)
                tag = "polygon" if primitive["closed"] else "polyline"
                lines.append(f'<{tag} points="{points}"/>')
            lines.append("</g>")
        lines.extend(["</g>", f'<g id="region-legend" font-family="monospace" font-size="11"><text x="{plot_width + 20:.0f}" y="28" fill="#ffffff" font-size="15" font-weight="bold">DRAWING REGIONS</text>'])
        for region_index, region in enumerate(regions):
            color = palette[region_index % len(palette)]
            classification = region["classification"]
            label = classification["predicted_type"] or "AMBIGUOUS"
            y = 54 + region_index * 38
            lines.append(f'<line x1="{plot_width + 20:.0f}" y1="{y:.0f}" x2="{plot_width + 48:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="4"/>')
            lines.append(f'<text x="{plot_width + 60:.0f}" y="{y + 4:.0f}" fill="#ffffff">{html.escape(region["region_id"])} · {html.escape(label)}</text>')
            lines.append(f'<text x="{plot_width + 60:.0f}" y="{y + 19:.0f}" fill="#9fb3c2">status={classification["status"]} · entities={region["structural_entity_count"]}</text>')
        lines.append("</g>")
        lines.append("</svg>")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _source_views_csv(report: Dict[str, Any]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow([
            "view_id", "scope", "exact_normalized_title", "drawing_type", "level_or_view_name", "scale",
            "routing_role", "frame_id", "min_x_mm", "min_y_mm", "max_x_mm", "max_y_mm",
            "assigned_entity_count", "crossing_entity_count", "multiply_assignable_entity_count", "confidence", "evidence",
        ])
        for view in report["source_views"].get("views", []):
            bounds = view["frame_bounds_mm"]
            writer.writerow([
                view["view_id"], view["scope"], view["exact_normalized_title"], view["drawing_type"],
                view["level_or_view_name"], view["scale"], view["routing_role"], view["frame_id"],
                bounds["min_x"], bounds["min_y"], bounds["max_x"], bounds["max_y"],
                view["assigned_entity_count"], len(view["crossing_entity_ids"]), len(view["multiply_assignable_entity_ids"]),
                view["confidence"], ";".join(view["evidence"]),
            ])
        return output.getvalue()

    @staticmethod
    def _source_views_xml(report: Dict[str, Any]) -> str:
        root = ET.Element("sourceViewAudit", {"schemaVersion": SCHEMA_VERSION, "status": report["source_view_status"]})
        ET.SubElement(root, "source", {"path": str(report["source"]["path"]), "sha256": report["source"]["sha256"]})
        views_node = ET.SubElement(root, "sourceViews", {"count": str(len(report["source_views"].get("views", [])))})
        for view in report["source_views"].get("views", []):
            node = ET.SubElement(views_node, "sourceView", {
                "id": view["view_id"], "scope": view["scope"], "drawingType": view["drawing_type"],
                "levelOrView": view["level_or_view_name"], "scale": view["scale"], "routingRole": view["routing_role"],
                "assignedCount": str(view["assigned_entity_count"]), "crossingCount": str(len(view["crossing_entity_ids"])),
                "multiplyAssignableCount": str(len(view["multiply_assignable_entity_ids"])),
            })
            ET.SubElement(node, "exactNormalizedTitle").text = view["exact_normalized_title"]
            ET.SubElement(node, "frameBounds", {key: str(value) for key, value in view["frame_bounds_mm"].items()})
        comparisons_node = ET.SubElement(root, "abComparisons", {"count": str(len(report["ab_comparisons"]))})
        for comparison in report["ab_comparisons"]:
            ET.SubElement(comparisons_node, "comparison", {
                "drawingType": comparison["drawing_type"], "levelOrView": comparison["level_or_view_name"],
                "aViewId": comparison["a_view_id"], "bViewId": comparison["b_view_id"],
                "classification": comparison["classification"], "evidence": comparison["evidence"],
                "deduplicationPerformed": "false",
            })
        topology_node = ET.SubElement(root, "floorTopologyQualification", {"count": str(len(report["floor_topology_qualification"]))})
        for item in report["floor_topology_qualification"]:
            ET.SubElement(topology_node, "floorView", {
                "viewId": item["view_id"], "status": item["status"], "inputSegmentCount": str(item.get("input_segment_count", 0)),
                "nodeCount": str(item.get("node_count", 0)), "edgeCount": str(item.get("edge_count", 0)), "loopCount": str(item.get("loop_count", 0)),
            })
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"

    @staticmethod
    def _source_views_svg(report: Dict[str, Any]) -> str:
        views = report["source_views"].get("views", [])
        geometry = report.get("_source_render_geometry", [])
        if not geometry and not views:
            return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><text x="20" y="30">No source-view evidence</text></svg>\n'
        bounds_items = [view["frame_bounds_mm"] for view in views]
        points = [point for primitive in geometry for point in primitive["points_mm"]]
        min_x = min([point[0] for point in points] + [item["min_x"] for item in bounds_items])
        min_y = min([point[1] for point in points] + [item["min_y"] for item in bounds_items])
        max_x = max([point[0] for point in points] + [item["max_x"] for item in bounds_items])
        max_y = max([point[1] for point in points] + [item["max_y"] for item in bounds_items])
        plot_width, legend_width, margin = 1250.0, 650.0, 30.0
        height = max(900.0, 70.0 + len(views) * 29.0)
        width = plot_width + legend_width
        scale = min((plot_width - 2 * margin) / max(max_x - min_x, 1.0), (height - 2 * margin) / max(max_y - min_y, 1.0))

        def transform(x: float, y: float) -> Tuple[float, float]:
            return margin + (x - min_x) * scale, height - margin - (y - min_y) * scale

        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">',
            '<rect width="100%" height="100%" fill="#101820"/>',
            f'<rect x="{plot_width:.0f}" width="{legend_width:.0f}" height="100%" fill="#17232d"/>',
            '<g id="source-geometry" fill="none" stroke="#a9bac7" stroke-opacity="0.18" stroke-width="0.45">',
        ]
        for primitive in geometry:
            transformed = [transform(point[0], point[1]) for point in primitive["points_mm"]]
            if len(transformed) < 2:
                continue
            coordinates = " ".join(f"{x:.3f},{y:.3f}" for x, y in transformed)
            tag = "polygon" if primitive["closed"] else "polyline"
            lines.append(f'<{tag} data-source-id="{html.escape(primitive["source_id"])}" points="{coordinates}"/>')
        lines.append("</g>")
        lines.append('<g id="detected-frames" fill="none" stroke="#ffcc33" stroke-width="1.2">')
        for view in views:
            bounds = view["frame_bounds_mm"]
            x1, y1 = transform(bounds["min_x"], bounds["max_y"])
            x2, y2 = transform(bounds["max_x"], bounds["min_y"])
            lines.append(f'<rect data-view-id="{view["view_id"]}" x="{x1:.3f}" y="{y1:.3f}" width="{x2-x1:.3f}" height="{y2-y1:.3f}"/>')
        lines.extend(["</g>", f'<g id="source-view-legend" font-family="monospace" font-size="10"><text x="{plot_width + 18:.0f}" y="28" fill="#ffffff" font-size="15" font-weight="bold">SOURCE VIEWS · {html.escape(report["source_view_status"])}</text>'])
        for ordinal, view in enumerate(views):
            y = 52 + ordinal * 29
            primary = f'{view["view_id"]} · {view["scope"]} · {view["drawing_type"]} · {view["routing_role"]}'
            secondary = f'{view["exact_normalized_title"]} · assigned={view["assigned_entity_count"]} · crossing={len(view["crossing_entity_ids"])}'
            lines.append(f'<text x="{plot_width + 18:.0f}" y="{y:.0f}" fill="#ffdd66">{html.escape(primary)}</text>')
            lines.append(f'<text x="{plot_width + 18:.0f}" y="{y + 13:.0f}" fill="#b7c8d4">{html.escape(secondary)}</text>')
        lines.extend(["</g>", "</svg>"])
        return "\n".join(lines) + "\n"

    def write_artifacts(self, report: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        public_report = {
            **{key: value for key, value in report.items() if key != "_source_render_geometry"},
            "regions": [
                {key: value for key, value in region.items() if key != "_render_geometry"}
                for region in report["regions"]
            ],
        }
        artifacts = {
            "regions.json": _canonical_json(public_report),
            "regions.svg": self._svg(report),
            "region_evidence.csv": self._csv(report),
            "source_views.json": _canonical_json({
                "schema_version": report["schema_version"], "source": report["source"],
                "status": report["source_view_status"], "source_views": report["source_views"],
                "ab_comparisons": report["ab_comparisons"], "floor_topology_qualification": report["floor_topology_qualification"],
            }),
            "source_views.csv": self._source_views_csv(report),
            "source_views.xml": self._source_views_xml(report),
            "source_views.svg": self._source_views_svg(report),
        }
        for name, content in artifacts.items():
            (output_dir / name).write_text(content, encoding="utf-8", newline="")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "manifest_name": "drawing_region_audit",
            "source": {"path": report["source"]["path"], "sha256": report["source"]["sha256"]},
            "files": {name: {"sha256": _sha256(output_dir / name), "size_bytes": (output_dir / name).stat().st_size} for name in sorted(artifacts)},
        }
        (output_dir / "manifest.json").write_text(_canonical_json(manifest), encoding="utf-8", newline="")
        return manifest

    def run(self, source_path: Path, output_dir: Path, required_source_sha: Optional[str] = REQUIRED_SOURCE_SHA256) -> Dict[str, Any]:
        source_display_path = source_path.as_posix()
        source_path = source_path.resolve()
        before = _sha256(source_path)
        if required_source_sha is not None and before != required_source_sha:
            raise RuntimeError(f"Source SHA-256 mismatch: expected {required_source_sha}, got {before}")
        entities, metadata = self.read_dxf(source_path)
        report = self.build_report(source_path, entities, metadata, source_display_path=source_display_path)
        after = _sha256(source_path)
        if before != after:
            raise RuntimeError("Source DXF changed during read-only audit")
        if report["source_views"].get("status") != "ready_for_review":
            raise RuntimeError(report["source_view_status"])
        self.write_artifacts(report, output_dir)
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic read-only DXF drawing-region audit")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/drawing_regions/proje"))
    args = parser.parse_args()
    report = DrawingRegionAudit().run(args.source, args.output)
    print(json.dumps({"output": args.output.as_posix(), **report["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()