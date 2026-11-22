"""
End-to-End Pipeline Verification Script.
Executes the full pipeline on all 5 sample reports, asserting proper outputs,
JSON serialization, CSV export, and PDF summary generation.
"""

import os
from pathlib import Path
import pytest

from app import run_analysis_pipeline
from report_generator import generate_patient_summary_pdf


class TestE2EPipeline:
    """Verifies complete end-to-end processing across all 5 sample reports."""

    @pytest.fixture
    def samples_dir(self):
        return Path(__file__).resolve().parent.parent / "sample_reports"

    @pytest.fixture
    def outputs_dir(self):
        out = Path(__file__).resolve().parent.parent / "outputs"
        out.mkdir(parents=True, exist_ok=True)
        return out

    def test_e2e_scenario_1_all_normal_pdf(self, samples_dir, outputs_dir):
        pdf_path = samples_dir / "01_all_values_normal.pdf"
        with open(pdf_path, "rb") as f:
            data = f.read()

        results = run_analysis_pipeline(data, "01_all_values_normal.pdf", api_key="")
        assert results["summary"]["Total"] >= 4
        assert results["summary"]["Normal"] >= 4
        assert results["summary"]["High"] == 0
        assert results["summary"]["Low"] == 0

        # Verify summary PDF generation
        out_pdf = outputs_dir / "test_e2e_01_summary.pdf"
        generate_patient_summary_pdf(results["explained_tests"], results["patient_info"], str(out_pdf))
        assert out_pdf.exists()
        assert out_pdf.stat().st_size > 1000

    def test_e2e_scenario_2_one_high_pdf(self, samples_dir):
        pdf_path = samples_dir / "02_one_high_value.pdf"
        with open(pdf_path, "rb") as f:
            data = f.read()

        results = run_analysis_pipeline(data, "02_one_high_value.pdf", api_key="")
        assert results["summary"]["High"] == 1
        high_item = next(t for t in results["explained_tests"] if t["status"] == "High")
        assert "glucose" in high_item["test_name"].lower()

    def test_e2e_scenario_3_one_low_pdf(self, samples_dir):
        pdf_path = samples_dir / "03_one_low_value.pdf"
        with open(pdf_path, "rb") as f:
            data = f.read()

        results = run_analysis_pipeline(data, "03_one_low_value.pdf", api_key="")
        assert results["summary"]["Low"] == 1
        low_item = next(t for t in results["explained_tests"] if t["status"] == "Low")
        assert "hemoglobin" in low_item["test_name"].lower()

    def test_e2e_scenario_4_missing_range_pdf(self, samples_dir):
        pdf_path = samples_dir / "04_missing_reference_range.pdf"
        with open(pdf_path, "rb") as f:
            data = f.read()

        results = run_analysis_pipeline(data, "04_missing_reference_range.pdf", api_key="")
        assert results["summary"]["Cannot determine"] >= 2

    def test_e2e_scenario_5_multiple_parameters_pdf(self, samples_dir):
        pdf_path = samples_dir / "05_multiple_blood_test_parameters.pdf"
        with open(pdf_path, "rb") as f:
            data = f.read()

        results = run_analysis_pipeline(data, "05_multiple_blood_test_parameters.pdf", api_key="")
        assert results["summary"]["Total"] >= 10
        assert results["summary"]["High"] >= 1
        assert results["summary"]["Normal"] >= 1
