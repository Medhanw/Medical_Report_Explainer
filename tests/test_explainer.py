"""
Unit Tests for AI Medical Explainer Module (explainer.py).
Verifies clinical guardrails, offline heuristic explanations,
non-diagnostic language, and mandatory disclaimers.
"""

import pytest
from explainer import MedicalReportExplainer
from config import MEDICAL_DISCLAIMER


class TestMedicalReportExplainer:
    """Test suite for explanation generation and clinical safety rules."""

    def test_explainer_initialization(self):
        """Initializes with default or custom configuration."""
        explainer = MedicalReportExplainer(api_key="test_key", model_name="gemini-1.5-flash")
        assert explainer.api_key == "test_key"
        assert explainer.model_name == "gemini-1.5-flash"

    def test_offline_fallback_explanation_generation(self):
        """Generates comprehensive explanations even without Gemini API key."""
        explainer = MedicalReportExplainer(api_key="")
        mock_analyzed_tests = [
            {
                "test_name": "Hemoglobin",
                "measured_value": 15.1,
                "unit": "g/dL",
                "reference_range": "13.5 - 17.5",
                "status": "Normal",
                "reason": "Value is within normal limits."
            },
            {
                "test_name": "Fasting Blood Glucose",
                "measured_value": 142.0,
                "unit": "mg/dL",
                "reference_range": "70 - 99",
                "status": "High",
                "reason": "Value exceeds upper limit."
            }
        ]

        explained = explainer.explain_tests(mock_analyzed_tests)
        assert len(explained) == 2

        hb = explained[0]
        assert "what_it_measures" in hb
        assert "oxygen" in hb["what_it_measures"].lower()
        assert hb["status"] == "Normal"

        glu = explained[1]
        assert "what_it_measures" in glu
        assert "glucose" in glu["what_it_measures"].lower() or "sugar" in glu["what_it_measures"].lower()
        assert glu["status"] == "High"

    def test_non_diagnostic_language_guardrail(self):
        """Ensures explanations avoid diagnostic claims like 'You have diabetes'."""
        explainer = MedicalReportExplainer(api_key="")
        test_case = [{
            "test_name": "Fasting Blood Sugar",
            "measured_value": 160.0,
            "unit": "mg/dL",
            "reference_range": "70 - 99",
            "status": "High",
            "reason": "Exceeds upper reference boundary."
        }]

        explained = explainer.explain_tests(test_case)[0]
        explanation_body = explained["explanation"]

        # Must not state definitive disease diagnosis
        assert "you have diabetes" not in explanation_body.lower()
        assert "you are diagnosed with" not in explanation_body.lower()
        # Must recommend consulting a doctor
        assert "doctor" in explanation_body.lower() or "physician" in explanation_body.lower() or "healthcare" in explanation_body.lower()

    def test_medical_disclaimer_content(self):
        """Ensures universal medical disclaimer contains key clinical caveats."""
        assert "educational purposes only" in MEDICAL_DISCLAIMER.lower()
        assert "does not provide medical diagnoses" in MEDICAL_DISCLAIMER.lower()
        assert "consult a qualified healthcare professional" in MEDICAL_DISCLAIMER.lower()
