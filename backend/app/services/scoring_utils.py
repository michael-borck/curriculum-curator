"""
Shared scoring utilities used by analytics and UDL services.

Extracted to avoid duplication of identical scoring logic.
"""

import math
from collections import Counter


def score_to_stars(score: float) -> float:
    """Convert 0-100 score to 0-5 star rating."""
    thresholds = [
        (95, 5.0),
        (90, 4.5),
        (85, 4.0),
        (80, 3.5),
        (70, 3.0),
        (55, 2.5),
        (40, 2.0),
        (20, 1.0),
    ]
    for threshold, stars in thresholds:
        if score >= threshold:
            return stars
    return 0.0


def score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def shannon_diversity(items: list[str]) -> float:
    """Shannon diversity index normalised to 0-100."""
    if not items:
        return 0.0
    counts = Counter(items)
    total = len(items)
    num_types = len(counts)
    if num_types <= 1:
        return 0.0 if total <= 1 else 20.0

    entropy = -sum(
        (c / total) * math.log(c / total) for c in counts.values() if c > 0
    )
    max_entropy = math.log(num_types)
    evenness = entropy / max_entropy if max_entropy > 0 else 0
    return round(evenness * 100.0, 2)


def balance_score(values: list[float]) -> float:
    """Calculate balance score (100 = perfectly even, 0 = maximally uneven)."""
    non_zero = [v for v in values if v > 0]
    if len(non_zero) < 2:
        return 50.0  # Not enough data
    mean = sum(non_zero) / len(non_zero)
    if mean == 0:
        return 50.0
    std_dev = math.sqrt(sum((x - mean) ** 2 for x in non_zero) / len(non_zero))
    cv = std_dev / mean
    return max(0.0, min(100.0, 100.0 - cv * 100.0))


def spread_score(values: list[int], total_slots: int) -> float:
    """Score how evenly values are spread across slots (0-100)."""
    if not values:
        return 0.0
    if len(values) == 1:
        return 50.0  # Single item can't be "spread"

    unique = sorted(set(values))
    if len(unique) == 1:
        return 0.0  # All in same slot

    # Calculate gaps between consecutive items
    gaps = [unique[i + 1] - unique[i] for i in range(len(unique) - 1)]
    ideal_gap = total_slots / (len(unique) + 1)
    if ideal_gap == 0:
        return 50.0

    mean_gap = sum(gaps) / len(gaps)
    deviation = abs(mean_gap - ideal_gap) / ideal_gap
    # Also reward using more of the semester range
    range_coverage = (unique[-1] - unique[0]) / total_slots
    return max(0.0, min(100.0, (1.0 - deviation * 0.5) * 50 + range_coverage * 50))
