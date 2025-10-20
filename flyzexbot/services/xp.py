"""Utility helpers for XP-based leveling."""

from __future__ import annotations

from dataclasses import dataclass


def xp_required_for_level(level: int) -> int:
    """Return the cumulative XP required to reach ``level``.

    Level ``0`` is considered the starting point and requires no XP. The
    requirement follows a gently increasing curve so that each level needs
    slightly more XP than the previous one. The first few thresholds are:

    * Level 1 → 10 XP
    * Level 2 → 25 XP
    * Level 3 → 45 XP
    """

    if level <= 0:
        return 0
    # Requirement grows with a quadratic curve that matches the examples above.
    return (5 * level * (level + 3)) // 2


@dataclass(frozen=True)
class LevelProgress:
    """Detailed information about a user's level progression."""

    level: int
    total_xp: int
    current_threshold: int
    next_threshold: int

    @property
    def xp_to_next(self) -> int:
        """How much XP is still needed to reach the next level."""

        return max(0, self.next_threshold - self.total_xp)

    @property
    def xp_into_level(self) -> int:
        """How much XP has been accumulated since reaching the current level."""

        return max(0, self.total_xp - self.current_threshold)


def calculate_level_progress(total_xp: int) -> LevelProgress:
    """Compute the level information for ``total_xp``.

    The function always returns a valid :class:`LevelProgress` instance where the
    ``level`` is zero or a positive integer and ``next_threshold`` is strictly
    greater than ``current_threshold``.
    """

    safe_total = max(0, int(total_xp))
    level = 0
    while safe_total >= xp_required_for_level(level + 1):
        level += 1

    current_threshold = xp_required_for_level(level)
    next_threshold = xp_required_for_level(level + 1)
    return LevelProgress(
        level=level,
        total_xp=safe_total,
        current_threshold=current_threshold,
        next_threshold=next_threshold,
    )
