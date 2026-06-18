"""
Multi-format grouping heuristic for Mode B (zip → existing unit) imports.

When a lecturer uploads a folder of materials, the same lecture often
appears in several formats — ``lecture_01.pptx``, ``lecture_01.pdf``,
``lecture_01.docx``. Phase 3 of the structured-import plan groups these
so one becomes the editable canonical ``WeeklyMaterial`` and the others
ride along as downloadable source files.

This module is the pure-data half: it takes a list of file paths and
returns groups. No DB, no filesystem, no parser dispatch — the route
layer consumes the groups and does the rest.

Grouping rule (v1, conservative):

1. Two files group iff they share the same parent directory **and** the
   same filename stem (case-insensitive). ``a/lecture_01.pptx`` and
   ``a/lecture_01.pdf`` group; ``a/lecture_01.pptx`` and
   ``b/lecture_01.pdf`` do not (different directory).
2. A file whose stem is unique in its directory is a singleton group.

Canonical ranking within a group: ``PPTX > DOCX > HTML > MD > PDF``.
Files with an unranked extension never win canonical over a ranked one;
between two unranked files, path order breaks the tie.

**Not in v1:** fuzzy stem matching, stem normalisation (e.g. stripping
``-final``/``_v2`` suffixes), or content-similarity hashing. Exact stem
match within a directory only. Conservative wins — a false group is
worse than two singletons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

# Canonical format priority. Lower index = higher priority. The first
# ranked format present in a group becomes the canonical file. Extensions
# not in this list are unranked — they only become canonical when a group
# contains no ranked format at all.
CANONICAL_RANKING: list[str] = ["pptx", "docx", "html", "htm", "md", "pdf"]


@dataclass
class FileGroup:
    """A set of uploaded files representing the same logical material.

    ``canonical`` is the file that will be parsed into the editable
    WeeklyMaterial; ``source_files`` are attached as-is (in original
    upload order, canonical excluded).
    """

    name: str
    """Group name — the shared filename stem (original casing of the
    canonical file's stem)."""

    directory: str
    """POSIX directory the group's files live in ("" for the zip root)."""

    canonical: str
    """Path of the canonical file (the one that gets parsed)."""

    members: list[str] = field(default_factory=list)
    """All file paths in the group, in original input order."""

    @property
    def source_files(self) -> list[str]:
        """Non-canonical members, in original input order."""
        return [p for p in self.members if p != self.canonical]

    @property
    def is_singleton(self) -> bool:
        """True when the group has no attached source files."""
        return len(self.members) == 1


def _ext(path: str) -> str:
    """Lowercased extension without the leading dot (``""`` if none)."""
    return PurePosixPath(path).suffix.lower().lstrip(".")


def _stem(path: str) -> str:
    """Filename stem (no directory, no extension)."""
    return PurePosixPath(path).stem


def _directory(path: str) -> str:
    """POSIX-style parent directory ("" for files at the root)."""
    parent = PurePosixPath(path).parent
    return "" if str(parent) == "." else str(parent)


def _rank(path: str) -> int:
    """Canonical priority for a path — lower is better, unranked is large."""
    ext = _ext(path)
    try:
        return CANONICAL_RANKING.index(ext)
    except ValueError:
        return len(CANONICAL_RANKING)


def select_canonical(paths: list[str]) -> str:
    """Return the canonical path from a group's member paths.

    Picks the highest-ranked format (PPTX > DOCX > HTML > MD > PDF);
    unranked extensions only win when nothing ranked is present. Ties
    (same rank) are broken by original input order.
    """
    if not paths:
        msg = "select_canonical requires at least one path"
        raise ValueError(msg)
    # min() is stable, so equal-rank paths keep input order. Use enumerate
    # so the index is an explicit, deterministic tiebreaker.
    return min(enumerate(paths), key=lambda iv: (_rank(iv[1]), iv[0]))[1]


def group_files(paths: list[str]) -> list[FileGroup]:
    """Group file paths by (directory, case-insensitive stem).

    Returns groups in first-appearance order of each group's key, so the
    preview UI shows them in roughly the order the user laid them out.
    Singletons are returned as one-member groups.

    Input order within each group is preserved (matters for canonical
    tiebreaking and source-file display order).
    """
    # key = (directory, lowercased stem) → ordered member paths
    buckets: dict[tuple[str, str], list[str]] = {}
    order: list[tuple[str, str]] = []

    for path in paths:
        key = (_directory(path), _stem(path).lower())
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(path)

    groups: list[FileGroup] = []
    for key in order:
        members = buckets[key]
        canonical = select_canonical(members)
        groups.append(
            FileGroup(
                # Name from the canonical file's stem to preserve its
                # original casing (the bucket key is lowercased).
                name=_stem(canonical),
                directory=key[0],
                canonical=canonical,
                members=members,
            )
        )
    return groups


__all__ = [
    "CANONICAL_RANKING",
    "FileGroup",
    "group_files",
    "select_canonical",
]
