import logging
from typing import Iterable, List, Tuple


logger = logging.getLogger("KaRar-SpatialIndex")


try:
    from rtree import index as index  # type: ignore
    HAS_RTREE = True
except ImportError:
    HAS_RTREE = False

    class _FallbackIndex:
        """Deterministic in-memory spatial index fallback when rtree is unavailable."""

        def __init__(self):
            self._entries: List[Tuple[int, Tuple[float, float, float, float]]] = []

        def insert(self, identifier: int, bounds: Tuple[float, float, float, float]):
            self._entries.append((identifier, bounds))

        def intersection(self, bounds: Tuple[float, float, float, float]) -> Iterable[int]:
            qminx, qminy, qmaxx, qmaxy = bounds
            matches: List[int] = []
            for identifier, (minx, miny, maxx, maxy) in self._entries:
                if maxx < qminx or qmaxx < minx or maxy < qminy or qmaxy < miny:
                    continue
                matches.append(identifier)
            return matches

    class index:  # pylint: disable=invalid-name
        Index = _FallbackIndex

    logger.warning("rtree not available; using deterministic in-memory spatial index fallback.")