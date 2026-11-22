"""
Unit Tests for Pydantic Models (models.py).
Verifies strict schema validation, type enforcement, and null handling.
"""

import pytest
from pydantic import ValidationError
from models import (
    StructuredLabReport,
    ExtractedBloodTest,
    ReferenceRangeDetail,
    PatientDemographics,
    AnalyzedTestRecord,
)


class TestPydanticModels:
    """Test suite for data models and schema validation."""

    def test_extracted_blood_test_valid(self):
        """Validates proper instantiation with full attributes."""
        test = ExtractedBloodTest(
            test_name="Hemoglobin",
            value=14.2,
            unit="g/dL",
            reference_range=ReferenceRangeDetail(
                low=13.0,
                high=17.0,
                display="13.0 - 17.0"
            )
        )
        assert test.test_name == "Hemoglobin"
        assert test.value == 14.2
        assert test.unit == "g/dL"
        assert test.reference_range.low == 13.0
        assert test.reference_range.high == 17.0

    def test_extracted_blood_test_string_reference_range(self):
        """Accepts reference_range as raw string when bounds are not segmented."""
        test = ExtractedBloodTest(
            test_name="HbA1c",
            value=5.6,
            unit="%",
            reference_range="< 5.7"
        )
        assert test.test_name == "HbA1c"
        assert test.reference_range == "< 5.7"

    def test_missing_information_as_null(self):
        """Ensures missing parameters gracefully default to None or null without error."""
        test = ExtractedBloodTest(
            test_name="Experimental Marker",
            value=None,
            unit="",
            reference_range=None
        )
        assert test.value is None
        assert test.reference_range is None

    def test_structured_lab_report_validation(self):
        """Validates full report schema containing patient demographics and test list."""
        payload = {
            "patient_info": {
                "age": 42,
                "sex": "Female",
                "report_date": "2026-10-18"
            },
            "tests": [
                {
                    "test_name": "Fasting Blood Glucose",
                    "value": 92.0,
                    "unit": "mg/dL",
                    "reference_range": {
                        "low": 70.0,
                        "high": 99.0,
                        "display": "70 - 99 mg/dL"
                    }
                }
            ]
        }
        report = StructuredLabReport.model_validate(payload)
        assert report.patient_info.age == 42
        assert report.patient_info.sex == "Female"
        assert len(report.tests) == 1
        assert report.tests[0].test_name == "Fasting Blood Glucose"

    def test_analyzed_test_record_creation(self):
        """Validates creation of final analyzed test record with status."""
        rec = AnalyzedTestRecord(
            test_name="Serum Creatinine",
            measured_value=0.85,
            unit="mg/dL",
            reference_range_display="0.5 - 1.1",
            status="Normal",
            status_color="green",
            reason="Value 0.85 is within 0.5 - 1.1",
            what_it_measures="Kidney filtration waste byproduct.",
            explanation="Normal kidney filtration reflected.",
            lifestyle_or_next_steps="Maintain hydration."
        )
        assert rec.status == "Normal"
        assert rec.status_color == "green"
