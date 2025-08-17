"""
PDF parsing service for extracting and analyzing course content
"""

import io
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import pdfplumber
from pypdf import PdfReader


class ExtractionMethod(str, Enum):
    """PDF extraction methods"""

    PYPDF = "pypdf"  # Fast, basic text extraction
    PDFPLUMBER = "pdfplumber"  # Better table extraction
    PYMUPDF = "pymupdf"  # Best layout preservation
    AUTO = "auto"  # Automatically choose best method


@dataclass
class ExtractedPage:
    """Extracted page data"""

    page_number: int
    text: str
    tables: list[list[list[str]]] | None = None
    images: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class PDFMetadata:
    """PDF document metadata"""

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: str | None = None
    modification_date: str | None = None
    page_count: int = 0
    has_forms: bool = False
    has_annotations: bool = False
    is_encrypted: bool = False


@dataclass
class ExtractedDocument:
    """Complete extracted document"""

    metadata: PDFMetadata
    pages: list[ExtractedPage]
    full_text: str
    toc: list[dict[str, Any]] | None = None  # Table of contents
    extraction_method: str = ""
    extraction_errors: list[str] | None = None


class PDFParserService:
    """Service for parsing PDF documents"""

    def __init__(self):
        """Initialize PDF parser service"""
        self.errors: list[str] = []

    async def extract_from_file(
        self, file_path: str | Path, method: ExtractionMethod = ExtractionMethod.AUTO
    ) -> ExtractedDocument:
        """
        Extract content from a PDF file

        Args:
            file_path: Path to PDF file
            method: Extraction method to use

        Returns:
            ExtractedDocument with all extracted content
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        with file_path.open("rb") as f:
            return await self.extract_from_bytes(f.read(), method)

    async def extract_from_bytes(
        self, pdf_bytes: bytes, method: ExtractionMethod = ExtractionMethod.AUTO
    ) -> ExtractedDocument:
        """
        Extract content from PDF bytes

        Args:
            pdf_bytes: PDF file content as bytes
            method: Extraction method to use

        Returns:
            ExtractedDocument with all extracted content
        """
        self.errors = []

        # Determine best extraction method if auto
        if method == ExtractionMethod.AUTO:
            method = self._determine_best_method(pdf_bytes)

        # Extract based on method
        if method == ExtractionMethod.PYPDF:
            return self._extract_with_pypdf(pdf_bytes)
        if method == ExtractionMethod.PDFPLUMBER:
            return self._extract_with_pdfplumber(pdf_bytes)
        # PYMUPDF
        return self._extract_with_pymupdf(pdf_bytes)

    def _determine_best_method(self, pdf_bytes: bytes) -> ExtractionMethod:
        """
        Determine the best extraction method based on PDF characteristics

        Args:
            pdf_bytes: PDF content

        Returns:
            Best extraction method to use
        """
        try:
            # Quick check with pypdf
            reader = PdfReader(io.BytesIO(pdf_bytes))

            # Check for forms or complex layouts
            has_forms = bool(reader.get_form_text_fields())
            page_count = len(reader.pages)

            # Simple heuristics
            if has_forms:
                return ExtractionMethod.PDFPLUMBER
            if page_count > 50:
                return ExtractionMethod.PYPDF  # Faster for large docs
            return ExtractionMethod.PYMUPDF  # Best quality

        except Exception:
            return ExtractionMethod.PYMUPDF  # Default to most robust

    def _extract_with_pypdf(self, pdf_bytes: bytes) -> ExtractedDocument:
        """Extract using pypdf (fast, basic)"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))

            # Extract metadata
            metadata = self._extract_pypdf_metadata(reader)

            # Extract pages
            pages = []
            full_text_parts = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                pages.append(
                    ExtractedPage(
                        page_number=i + 1, text=text, metadata={"method": "pypdf"}
                    )
                )
                full_text_parts.append(text)

            return ExtractedDocument(
                metadata=metadata,
                pages=pages,
                full_text="\n\n".join(full_text_parts),
                extraction_method="pypdf",
                extraction_errors=self.errors if self.errors else None,
            )

        except Exception as e:
            self.errors.append(f"pypdf extraction error: {e!s}")
            raise

    def _extract_pypdf_metadata(self, reader: PdfReader) -> PDFMetadata:
        """Extract metadata using pypdf"""
        info = reader.metadata if reader.metadata else {}

        return PDFMetadata(
            title=info.get("/Title", None),
            author=info.get("/Author", None),
            subject=info.get("/Subject", None),
            creator=info.get("/Creator", None),
            producer=info.get("/Producer", None),
            creation_date=str(info.get("/CreationDate", "")),
            modification_date=str(info.get("/ModDate", "")),
            page_count=len(reader.pages),
            has_forms=bool(reader.get_form_text_fields()),
            is_encrypted=reader.is_encrypted,
        )

    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> ExtractedDocument:
        """Extract using pdfplumber (good for tables)"""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                # Extract metadata
                metadata = PDFMetadata(
                    title=pdf.metadata.get("Title"),
                    author=pdf.metadata.get("Author"),
                    subject=pdf.metadata.get("Subject"),
                    creator=pdf.metadata.get("Creator"),
                    producer=pdf.metadata.get("Producer"),
                    creation_date=str(pdf.metadata.get("CreationDate", "")),
                    modification_date=str(pdf.metadata.get("ModDate", "")),
                    page_count=len(pdf.pages),
                )

                # Extract pages with tables
                pages = []
                full_text_parts = []

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    tables = page.extract_tables()

                    # Convert tables to list format
                    table_data = None
                    if tables:
                        table_data = [
                            [[str(cell) if cell else "" for cell in row] for row in table]
                            for table in tables
                        ]

                    pages.append(
                        ExtractedPage(
                            page_number=i + 1,
                            text=text if text else "",
                            tables=table_data,
                            metadata={"method": "pdfplumber"},
                        )
                    )

                    if text:
                        full_text_parts.append(text)

                return ExtractedDocument(
                    metadata=metadata,
                    pages=pages,
                    full_text="\n\n".join(full_text_parts),
                    extraction_method="pdfplumber",
                    extraction_errors=self.errors if self.errors else None,
                )

        except Exception as e:
            self.errors.append(f"pdfplumber extraction error: {e!s}")
            raise

    def _extract_with_pymupdf(self, pdf_bytes: bytes) -> ExtractedDocument:
        """Extract using PyMuPDF (best layout preservation)"""
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            # Extract metadata
            metadata = PDFMetadata(
                title=doc.metadata.get("title"),
                author=doc.metadata.get("author"),
                subject=doc.metadata.get("subject"),
                creator=doc.metadata.get("creator"),
                producer=doc.metadata.get("producer"),
                creation_date=doc.metadata.get("creationDate"),
                modification_date=doc.metadata.get("modDate"),
                page_count=doc.page_count,
                has_annotations=any(page.first_annot for page in doc),
            )

            # Extract table of contents
            toc = doc.get_toc()
            toc_data = (
                [{"level": item[0], "title": item[1], "page": item[2]} for item in toc]
                if toc
                else None
            )

            # Extract pages with enhanced formatting
            pages = []
            full_text_parts = []

            for i, page in enumerate(doc):
                # Extract text with layout preservation
                text = page.get_text("text")

                # Extract text blocks for structure analysis
                blocks = page.get_text("blocks")
                block_data = [
                    {
                        "bbox": block[:4],  # Bounding box
                        "text": block[4],
                        "block_no": block[5] if len(block) > 5 else None,
                    }
                    for block in blocks
                    if len(block) >= 5  # Text block
                ]

                # Extract images
                image_list = page.get_images()
                images = None
                if image_list:
                    images = [
                        {
                            "index": img[0],
                            "name": img[7] if len(img) > 7 else f"image_{img[0]}",
                        }
                        for img in image_list
                    ]

                pages.append(
                    ExtractedPage(
                        page_number=i + 1,
                        text=text,
                        images=images,
                        metadata={"method": "pymupdf", "blocks": block_data},
                    )
                )

                if text:
                    full_text_parts.append(text)

            doc.close()

            return ExtractedDocument(
                metadata=metadata,
                pages=pages,
                full_text="\n\n".join(full_text_parts),
                toc=toc_data,
                extraction_method="pymupdf",
                extraction_errors=self.errors if self.errors else None,
            )

        except Exception as e:
            self.errors.append(f"pymupdf extraction error: {e!s}")
            raise

    async def extract_structure(
        self, document: ExtractedDocument
    ) -> dict[str, Any]:
        """
        Analyze and extract document structure

        Args:
            document: Extracted document

        Returns:
            Document structure analysis
        """
        structure: dict[str, Any] = {
            "sections": [],
            "headings": [],
            "lists": [],
            "tables_count": 0,
            "images_count": 0,
            "estimated_reading_time_minutes": 0,
        }

        # Extract headings and sections
        heading_pattern = re.compile(
            (
                r"^(#{1,6}\s+.+|"
                r"Chapter\s+\d+|"
                r"Section\s+\d+|"
                r"Unit\s+\d+|"
                r"Module\s+\d+|"
                r"Week\s+\d+|"
                r"Topic\s+\d+|"
                r"Learning\s+Outcome|"
                r"Assessment|"
                r"References|"
                r"Bibliography)"
            ),
            re.MULTILINE | re.IGNORECASE,
        )

        for match in heading_pattern.finditer(document.full_text):
            structure["headings"].append(
                {"text": match.group().strip(), "position": match.start()}
            )

        # Count tables and images
        for page in document.pages:
            if page.tables:
                structure["tables_count"] += len(page.tables)
            if page.images:
                structure["images_count"] += len(page.images)

        # Estimate reading time (200 words per minute)
        word_count = len(document.full_text.split())
        structure["estimated_reading_time_minutes"] = max(1, word_count // 200)

        # Identify sections based on TOC or headings
        if document.toc:
            structure["sections"] = [
                {"title": item["title"], "page": item["page"], "level": item["level"]}
                for item in document.toc
            ]

        return structure

    async def extract_learning_content(
        self, document: ExtractedDocument
    ) -> dict[str, Any]:
        """
        Extract learning-specific content from document

        Args:
            document: Extracted document

        Returns:
            Learning content analysis
        """
        content = {
            "learning_outcomes": [],
            "topics": [],
            "assessments": [],
            "readings": [],
            "activities": [],
            "prerequisites": None,
            "schedule": None,
        }

        text = document.full_text.lower()

        # Extract learning outcomes
        lo_pattern = re.compile(
            (
                r"(learning\s+outcome[s]?|"
                r"course\s+outcome[s]?|"
                r"unit\s+outcome[s]?|"
                r"objective[s]?)"
                r"[:\s]*([^.!?]*[.!?]){1,5}"
            ),
            re.IGNORECASE | re.MULTILINE,
        )

        for match in lo_pattern.finditer(text):
            content["learning_outcomes"].append(match.group().strip())

        # Extract assessment information
        assessment_pattern = re.compile(
            (
                r"(assignment[s]?|"
                r"quiz[zes]?|"
                r"exam[s]?|"
                r"test[s]?|"
                r"project[s]?|"
                r"presentation[s]?)"
                r"[:\s]*([^.!?]*[.!?]){1,3}"
            ),
            re.IGNORECASE | re.MULTILINE,
        )

        for match in assessment_pattern.finditer(text):
            content["assessments"].append(match.group().strip())

        # Extract weekly topics if present
        week_pattern = re.compile(
            r"week\s+(\d+)[:\s]*([^\\n]*)", re.IGNORECASE | re.MULTILINE
        )

        for match in week_pattern.finditer(text):
            content["topics"].append(
                {"week": int(match.group(1)), "topic": match.group(2).strip()}
            )

        return content

    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Fix common OCR issues
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")

        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^\d+$", "", text, flags=re.MULTILINE)

        # Clean up spacing around punctuation
        text = re.sub(r"\s+([.,;:!?])", r"\1", text)
        text = re.sub(r"([.,;:!?])(?=[A-Za-z])", r"\1 ", text)

        return text.strip()

    async def convert_to_markdown(self, document: ExtractedDocument) -> str:  # noqa: PLR0912
        """
        Convert extracted document to Markdown format

        Args:
            document: Extracted document

        Returns:
            Markdown formatted text
        """
        markdown_parts = []

        # Add metadata as frontmatter
        markdown_parts.append("---")
        if document.metadata.title:
            markdown_parts.append(f"title: {document.metadata.title}")
        if document.metadata.author:
            markdown_parts.append(f"author: {document.metadata.author}")
        if document.metadata.subject:
            markdown_parts.append(f"subject: {document.metadata.subject}")
        markdown_parts.append(f"pages: {document.metadata.page_count}")
        markdown_parts.append("---\n")

        # Add table of contents if available
        if document.toc:
            markdown_parts.append("## Table of Contents\n")
            for item in document.toc:
                indent = "  " * (item["level"] - 1)
                markdown_parts.append(f"{indent}- {item['title']} (p. {item['page']})")
            markdown_parts.append("\n")

        # Process each page
        for page in document.pages:
            # Add page marker
            markdown_parts.append(f"\n<!-- Page {page.page_number} -->\n")

            # Add text content
            if page.text:
                cleaned_text = self.clean_extracted_text(page.text)
                # Try to identify and format headings
                lines = cleaned_text.split("\n")
                for text_line in lines:
                    line = text_line.strip()
                    if not line:
                        continue

                    # Check if line looks like a heading
                    if (
                        line.isupper() or line.startswith(("Chapter", "Section", "Unit", "Module"))
                    ):
                        markdown_parts.append(f"## {line}\n")
                    else:
                        markdown_parts.append(f"{line}\n")

            # Add tables if present
            if page.tables:
                for i, table in enumerate(page.tables):
                    markdown_parts.append(f"\n### Table {i + 1}\n")
                    markdown_parts.append(self._table_to_markdown(table))

            # Note images if present
            if page.images:
                markdown_parts.append(
                    f"\n*Note: Page contains {len(page.images)} image(s)*\n"
                )

        return "\n".join(markdown_parts)

    def _table_to_markdown(self, table: list[list[str]]) -> str:
        """Convert table data to Markdown format"""
        if not table or not table[0]:
            return ""

        markdown_lines = []

        # Header row
        header = table[0]
        markdown_lines.append("| " + " | ".join(str(cell) for cell in header) + " |")

        # Separator
        markdown_lines.append("|" + "|".join([" --- " for _ in header]) + "|")

        # Data rows
        markdown_lines.extend(
            "| " + " | ".join(str(cell) for cell in row) + " |"
            for row in table[1:]
        )

        return "\n".join(markdown_lines) + "\n"


# Singleton instance
pdf_parser_service = PDFParserService()

