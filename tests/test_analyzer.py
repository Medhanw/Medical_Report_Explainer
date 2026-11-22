"""
Automated Unit Tests for Pure-Python Numerical Analyzer.

Verifies the 5 required test scenarios and boundary edge cases:
1. All values normal.
2. One high value.
3. One low value.
4. Missing reference range.
5. Multiple blood test parameters with inequalities.
"""

import pytest
from analyzer import MedicalRangeAnalyzer


class TestMedicalRangeAnalyzer:
    """Test suite for pure-Python blood test classification."""

    def test_scenario_1_all_values_normal(self):
        """Scenario 1: All blood test parameters fall strictly within normal boundaries."""
        sample_tests = [
            {"test_name": "Hemoglobin", "measured_value": 15.1, "unit": "g/dL", "reference_range": "13.5 - 17.5"},
            {"test_name": "Total Leukocyte Count", "measured_value": 6800, "unit": "/cumm", "reference_range": "4000 - 11000"},
            {"test_name": "Platelet Count", "measured_value": 250000, "unit": "/cumm", "reference_range": "150000 - 450000"},
            {"test_name": "Hematocrit", "measured_value": 45.2, "unit": "%", "reference_range": "41.0 - 50.0"}
        ]

        results = MedicalRangeAnalyzer.analyze_all_tests(sample_tests)
        summary = MedicalRangeAnalyzer.get_summary_counts(results)

        assert summary["Total"] == 4
        assert summary["Normal"] == 4
        assert summary["High"] == 0
        assert summary["Low"] == 0
        assert summary["Cannot determine"] == 0

        for r in results:
            assert r["status"] == "Normal"
            assert r["status_color"] == "green"

    def test_scenario_2_one_high_value(self):
        """Scenario 2: One elevated parameter (Fasting Glucose > 99) while others are normal."""
        sample_tests = [
            {"test_name": "Fasting Blood Glucose", "measured_value": 142.0, "unit": "mg/dL", "reference_range": "70 - 99"},
            {"test_name": "Serum Creatinine", "measured_value": 0.82, "unit": "mg/dL", "reference_range": "0.5 - 1.1"},
            {"test_name": "Blood Urea Nitrogen", "measured_value": 14.0, "unit": "mg/dL", "reference_range": "7.0 - 20.0"}
        ]

        results = MedicalRangeAnalyzer.analyze_all_tests(sample_tests)
        summary = MedicalRangeAnalyzer.get_summary_counts(results)

        assert summary["Total"] == 3
        assert summary["High"] == 1
        assert summary["Normal"] == 2
        assert summary["Low"] == 0

        glucose_res = next(r for r in results if r["test_name"] == "Fasting Blood Glucose")
        assert glucose_res["status"] == "High"
        assert glucose_res["status_color"] == "red"
        assert "above" in glucose_res["reason"].lower()

    def test_scenario_3_one_low_value(self):
        """Scenario 3: One low parameter (Hemoglobin < 13.5) with other tests normal."""
        sample_tests = [
            {"test_name": "Hemoglobin", "measured_value": 10.2, "unit": "g/dL", "reference_range": "13.5 - 17.5"},
            {"test_name": "Total Leukocyte Count", "measured_value": 7200, "unit": "/cumm", "reference_range": "4000 - 11000"},
            {"test_name": "Platelet Count", "measured_value": 220000, "unit": "/cumm", "reference_range": "150000 - 450000"}
        ]

        results = MedicalRangeAnalyzer.analyze_all_tests(sample_tests)
        summary = MedicalRangeAnalyzer.get_summary_counts(results)

        assert summary["Total"] == 3
        assert summary["Low"] == 1
        assert summary["Normal"] == 2

        hb_res = next(r for r in results if r["test_name"] == "Hemoglobin")
        assert hb_res["status"] == "Low"
        assert hb_res["status_color"] == "blue"
        assert "below" in hb_res["reason"].lower()

    def test_scenario_4_missing_reference_range(self):
        """Scenario 4: Handles missing, null, and 'Not provided' reference ranges correctly."""
        sample_tests = [
            {"test_name": "C-Reactive Protein (CRP)", "measured_value": 3.4, "unit": "mg/L", "reference_range": "Not provided"},
            {"test_name": "Special Antibody Marker", "measured_value": 12.5, "unit": "AU/mL", "reference_range": None},
            {"test_name": "Unknown Peptide", "measured_value": 0.45, "unit": "ug/L", "reference_range": ""},
            {"test_name": "Fasting Blood Sugar", "measured_value": 88.0, "unit": "mg/dL", "reference_range": "70 - 99"}
        ]

        results = MedicalRangeAnalyzer.analyze_all_tests(sample_tests)
        summary = MedicalRangeAnalyzer.get_summary_counts(results)

        assert summary["Total"] == 4
        assert summary["Cannot determine"] == 3
        assert summary["Normal"] == 1

        for r in results[:3]:
            assert r["status"] == "Cannot determine"
            assert r["status_color"] == "gray"
            assert "missing" in r["reason"].lower() or "not provided" in r["reason"].lower()

    def test_scenario_5_multiple_parameters_and_inequalities(self):
        """Scenario 5: Multi-panel including upper/lower limit inequalities (< 100, >= 60)."""
        sample_tests = [
            {"test_name": "HbA1c", "measured_value": 5.9, "unit": "%", "reference_range": "< 5.7"},
            {"test_name": "Total Cholesterol", "measured_value": 225, "unit": "mg/dL", "reference_range": "< 200"},
            {"test_name": "HDL Cholesterol", "measured_value": 55, "unit": "mg/dL", "reference_range": "> 50"},
            {"test_name": "Estimated GFR", "measured_value": 95, "unit": "mL/min", "reference_range": ">= 60"},
            {"test_name": "Serum ALT", "measured_value": 28, "unit": "U/L", "reference_range": "< 35"},
            {"test_name": "Serum Creatinine", "measured_value": 0.75, "unit": "mg/dL", "reference_range": "0.5 - 1.1"}
        ]

        results = MedicalRangeAnalyzer.analyze_all_tests(sample_tests)
        summary = MedicalRangeAnalyzer.get_summary_counts(results)

        # HbA1c 5.9 > 5.7 -> High
        # Total Cholesterol 225 > 200 -> High
        # HDL 55 > 50 -> Normal
        # eGFR 95 >= 60 -> Normal
        # ALT 28 < 35 -> Normal
        # Creatinine 0.75 in 0.5-1.1 -> Normal
        assert summary["Total"] == 6
        assert summary["High"] == 2
        assert summary["Normal"] == 4
        assert summary["Low"] == 0

    def test_sex_specific_reference_ranges(self):
        """Verify sex-specific range resolution for Male vs Female."""
        test_case = {
            "test_name": "Hemoglobin",
            "measured_value": 12.5,
            "unit": "g/dL",
            "reference_range": "Male: 13.5-17.5, Female: 12.0-15.5"
        }

        # For a male patient, 12.5 is LOW (ref 13.5 - 17.5)
        male_eval = MedicalRangeAnalyzer.evaluate_test(
            test_name=test_case["test_name"],
            measured_value=test_case["measured_value"],
            reference_range=test_case["reference_range"],
            unit=test_case["unit"],
            patient_sex="Male"
        )
        assert male_eval["status"] == "Low"

        # For a female patient, 12.5 is NORMAL (ref 12.0 - 15.5)
        female_eval = MedicalRangeAnalyzer.evaluate_test(
            test_name=test_case["test_name"],
            measured_value=test_case["measured_value"],
            reference_range=test_case["reference_range"],
            unit=test_case["unit"],
            patient_sex="Female"
        )
        assert female_eval["status"] == "Normal"

    def test_commas_and_special_formats(self):
        """Handles comma formatted numbers like 150,000 - 450,000."""
        eval_res = MedicalRangeAnalyzer.evaluate_test(
            test_name="Platelet Count",
            measured_value="350,000",
            reference_range="150,000 - 450,000",
            unit="/cumm"
        )
        assert eval_res["status"] == "Normal"
        assert eval_res["parsed_value"] == 350000.0
        assert eval_res["parsed_min"] == 150000.0
        assert eval_res["parsed_max"] == 450000.0
