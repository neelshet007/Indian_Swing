"""
Universe Badge Lookup — Presentation-layer only.

Loads market universe CSVs once at startup into fast in-memory sets.
Provides O(1) symbol membership lookups without touching DB, strategy,
recommendation, or any calculation layer.

Future universes (NIFTY 100, NIFTY 200, NIFTY 1000, custom watchlists)
can be added by dropping CSV files and registering them in UNIVERSE_SOURCES.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

# ── F&O-eligible indices and stocks ──────────────────────────────────────────
_FNO_INDICES = {
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
    "NIFTY 50", "NIFTY BANK", "NIFTY FIN SERVICE", "NIFTY MID SELECT",
}

# ── Universe source registry ────────────────────────────────────────────────
# Each entry: (universe_name, csv_relative_path, symbol_column_name)
# Add new universes here — no other code changes needed.
UNIVERSE_SOURCES: list[tuple[str, str, str]] = [
    ("NIFTY 500", "config/universe.csv", "Symbol"),
    # Future entries:
    # ("NIFTY 100", "config/nifty100.csv", "Symbol"),
    # ("NIFTY 200", "config/nifty200.csv", "Symbol"),
]


class UniverseBadgeLookup:
    """
    Singleton-pattern badge lookup.
    Loads all configured CSVs once at construction time.
    All public methods are pure reads — zero side-effects on any other system.
    """

    def __init__(self):
        self._universes: dict[str, set[str]] = {}
        self._load_all()

    # ── Loading ──────────────────────────────────────────────────────────────

    def _project_root(self) -> Path:
        """Resolve project root (3 levels up from this file)."""
        return Path(__file__).resolve().parent.parent.parent

    def _load_all(self):
        root = self._project_root()
        for name, rel_path, col in UNIVERSE_SOURCES:
            csv_path = root / rel_path
            self._load_csv(name, csv_path, col)
        logger.info(
            "universe_badge.loaded",
            universes={k: len(v) for k, v in self._universes.items()},
        )

    def _load_csv(self, name: str, path: Path, symbol_col: str):
        if not path.exists():
            logger.warning("universe_badge.csv_not_found", universe=name, path=str(path))
            return
        try:
            symbols: set[str] = set()
            with path.open(mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sym = row.get(symbol_col) or row.get("symbol")
                    if sym:
                        symbols.add(sym.strip().upper())
            self._universes[name] = symbols
            logger.info("universe_badge.csv_loaded", universe=name, count=len(symbols))
        except Exception as e:
            logger.error(f"universe_badge.load_failed: {name}: {e}")

    # ── Public API ───────────────────────────────────────────────────────────

    def get_badges(self, symbol: str) -> list[str]:
        """
        Return list of universe names the symbol belongs to.
        Returns empty list if symbol is not in any universe.
        Never modifies any recommendation or strategy data.
        """
        if not symbol:
            return []
        sym = symbol.strip().upper()
        badges: list[str] = []
        for name, members in self._universes.items():
            if sym in members:
                badges.append(name)
        # F&O eligibility is determined by static index set
        if sym in _FNO_INDICES:
            badges.append("F&O")
        return badges

    def has_badge(self, symbol: str, universe: str) -> bool:
        """Check if symbol belongs to a specific universe."""
        if not symbol:
            return False
        sym = symbol.strip().upper()
        if universe == "F&O":
            return sym in _FNO_INDICES
        return sym in self._universes.get(universe, set())

    def all_universes(self) -> list[str]:
        """List all loaded universe names."""
        names = list(self._universes.keys())
        names.append("F&O")
        return names

    def universe_size(self, name: str) -> int:
        """Return count of symbols in a universe."""
        if name == "F&O":
            return len(_FNO_INDICES)
        return len(self._universes.get(name, set()))


# ── Module-level singleton ───────────────────────────────────────────────────
badge_lookup = UniverseBadgeLookup()
