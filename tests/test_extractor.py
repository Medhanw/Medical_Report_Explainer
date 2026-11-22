"""
Automated Unit Tests for PDF/TXT Extractor Module.

Verifies:
- Text extraction from valid TXT files.
- Text extraction from valid digital PDF files.
- Detection and error handling for empty files.
- Detection and rejection of scanned/image-only PDFs.
- Rejection of unsupported file extensions.
"""

import os
import pytest
from extractor import ReportTextExtractor, ExtractionError


class TestReportTextExtractor:
    """Test suite for PDF and TXT file extraction logic."""

    @pytest.fixture
    def samples_dir(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_reports")

    def test_extract_from_valid_txt(self, samples_dir):
        """Extracts text correctly from a valid TXT blood report."""
        txt_path = os.path.join(samples_dir, "01_all_values_normal.txt")
        with open(txt_path, "rb") as f:
            data = f.read()

        text = ReportTextExtractor.extract_text(data, "01_all_values_normal.txt")
        assert len(text) > 100
        assert "Hemoglobin" in text
        assert "Platelet Count" in text

    def test_extract_from_valid_pdf(self, samples_dir):
        """Extracts text correctly from a valid digital PDF blood report."""
        pdf_path = os.path.join(samples_dir, "01_all_values_normal.pdf")
        with open(pdf_path, "rb") as f:
            data = f.read()

        text = ReportTextExtractor.extract_text(data, "01_all_values_normal.pdf")
        assert len(text) > 100
        assert "Hemoglobin" in text
        assert "Total Leukocyte Count" in text

    def test_empty_file_rejection(self):
        """Rejects zero-byte files with an explicit ExtractionError."""
        with pytest.raises(ExtractionError) as exc_info:
            ReportTextExtractor.extract_text(b"", "empty.txt")
        assert "empty" in str(exc_info.value).lower()

        with pytest.raises(ExtractionError) as exc_info_pdf:
            ReportTextExtractor.extract_text(b"", "empty.pdf")
        assert "empty" in str(exc_info_pdf.value).lower()

    def test_scanned_image_pdf_rejection(self, samples_dir):
        """Detects scanned / image-only PDFs with no selectable digital text."""
        scanned_pdf_path = os.path.join(samples_dir, "edge_case_scanned_image_only.pdf")
        with open(scanned_pdf_path, "rb") as f:
            data = f.read()

        with pytest.raises(ExtractionError) as exc_info:
            ReportTextExtractor.extract_text(data, "edge_case_scanned_image_only.pdf")
        assert "scanned" in str(exc_info.value).lower() or "unreadable" in str(exc_info.value).lower()

    def test_unsupported_file_extension(self):
        """Rejects non-PDF/TXT extensions."""
        with pytest.raises(ExtractionError) as exc_info:
            ReportTextExtractor.extract_text(b"some content", "report.docx")
        assert "unsupported" in str(exc_info.value).lower()
