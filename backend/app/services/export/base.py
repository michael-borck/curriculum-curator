"""
Base classes for the export system.

All exporters extend BaseExporter and produce ExportResult instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        buf: BytesIO buffer containing the exported content.
        filename: Suggested filename for the download.
        media_type: MIME type of the exported content.
        metadata: Optional metadata about the export (e.g. warnings, stats).
    """

    buf: BytesIO
    filename: str
    media_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseExporter(ABC):
    """Abstract base class for all export services.

    Subclasses must implement ``export_material`` at minimum.
    Unit-level export (``export_unit``) has a default that raises
    NotImplementedError so it can be added incrementally.
    """

    @abstractmethod
    async def export_material(
        self,
        material_id: str,
        db: Session,
        **kwargs: Any,
    ) -> ExportResult:
        """Export a single material item.

        Args:
            material_id: The WeeklyMaterial or Content ID.
            db: Database session.
            **kwargs: Format-specific options.

        Returns:
            ExportResult with buffer, filename, and media type.
        """
        ...

    async def export_unit(
        self,
        unit_id: str,
        db: Session,
        **kwargs: Any,
    ) -> ExportResult:
        """Export an entire unit.

        Default implementation raises NotImplementedError.
        Override in subclasses that support unit-level export.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support unit-level export"
        )
