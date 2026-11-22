"""
Medical Report Explainer - AI Explainer Module.

Translates laboratory parameters and deterministic Python classifications into
patient-friendly, empathetic explanations using Google Gemini API (`google-genai` SDK).
Guarantees clinical safety guardrails: no unauthorized diagnosis, no prescriptions,
and no alarmist exaggeration.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL, MEDICAL_DISCLAIMER


class MedicalReportExplainer:
    """Generates patient-friendly clinical context and non-diagnostic explanations."""

    EXPLANATION_SYSTEM_INSTRUCTION = (
        "You are an empathetic, clear, and reassuring medical education assistant.\n"
        "Your role is to explain laboratory blood tests to patients in everyday English.\n"
        "CRITICAL RULES:\n"
        "1. Never diagnose a medical condition or suggest treatments/prescriptions.\n"
        "2. Do not contradict Python's classification (Normal, High, Low, Cannot determine).\n"
        "3. Use cautious phrasing such as 'can sometimes be associated with'.\n"
        "4. Emphasize that a single test result cannot establish a diagnosis.\n"
        "5. Avoid alarmist language or creating unnecessary fear."
    )

    EXPLANATION_PROMPT_TEMPLATE = """
A patient has uploaded their blood test report. The parameters have been classified by our deterministic Python analysis engine.

For every test in the list below, generate a patient-friendly explanation covering:
1. "what_it_measures": What the test generally measures in plain English.
2. "status_overview": Clear statement whether the result is within the supplied reference range.
3. "elevated_associations": What an elevated result can sometimes be associated with (e.g. hydration, meals, stress, mild inflammation).
4. "decreased_associations": What a decreased result can sometimes be associated with (e.g. dietary shifts, temporary suppression).
5. "why_context_matters": Why clinical context, symptoms, and medical history are essential.
6. "when_to_consult": Advice on discussing this specific result with a qualified healthcare professional.

STRICT FORMAT: Return ONLY a valid JSON array of objects matching this schema:
[
  {{
    "test_name": "Hemoglobin",
    "what_it_measures": "Hemoglobin is an iron-rich protein inside red blood cells that transports oxygen from your lungs to tissues.",
    "status_overview": "Your level is within the expected normal reference range provided by the laboratory.",
    "elevated_associations": "Elevations can sometimes occur with dehydration, smoking, or living at higher altitudes.",
    "decreased_associations": "Lower levels can sometimes be associated with low dietary iron, recent blood loss, or fatigue.",
    "why_context_matters": "A single blood count must always be interpreted alongside symptoms like energy levels and overall health history.",
    "when_to_consult": "Share this report with your physician during your routine check-up."
  }}
]

TESTS TO EXPLAIN:
{tests_json}
"""

    # Comprehensive offline clinical knowledge base for offline operation & tests
    OFFLINE_KB = {
        "hemoglobin": {
            "what_it_measures": "Hemoglobin is an iron-containing protein in red blood cells that carries oxygen throughout the entire body.",
            "elevated_associations": "Elevated levels can sometimes be linked to temporary dehydration, smoking, or adapting to high altitudes.",
            "decreased_associations": "Lower levels can be associated with low iron levels, vitamin deficiencies, or recent blood loss.",
            "why_context_matters": "Oxygen transport capacity is best understood in combination with your daily energy levels and complete red cell indices.",
            "when_to_consult": "Discuss with your physician if you experience unusual fatigue, dizziness, or pale skin."
        },
        "total leukocyte count": {
            "what_it_measures": "White blood cells (leukocytes) are key defenders of the immune system that fight infections and inflammation.",
            "elevated_associations": "Higher counts often represent a natural immune response to a recent cold, physical stress, or minor tissue inflammation.",
            "decreased_associations": "Lower counts can occasionally occur after viral illnesses, vitamin B12 insufficiency, or certain medications.",
            "why_context_matters": "White cell numbers naturally fluctuate day-to-day based on physical exertion, stress, and mild allergies.",
            "when_to_consult": "Check with your doctor if accompanied by fever, chills, or persistent infections."
        },
        "platelet count": {
            "what_it_measures": "Platelets are microscopic cell fragments essential for forming blood clots and preventing bleeding.",
            "elevated_associations": "High platelets can reflect a temporary reactive response to recent inflammation, infection, or iron changes.",
            "decreased_associations": "Lower platelets can occur temporarily after viral infections or due to specific medications.",
            "why_context_matters": "Clotting factors and platelets work together, so single numbers require clinical correlation.",
            "when_to_consult": "Consult a healthcare provider if you notice unusual bruising, bleeding gums, or petechiae."
        },
        "fasting blood glucose": {
            "what_it_measures": "Fasting blood glucose measures the amount of sugar in the blood after an overnight fast, reflecting metabolic processing.",
            "elevated_associations": "Elevations can be related to prediabetes, diabetes, recent illness, poor sleep, or acute physical stress.",
            "decreased_associations": "Dips can occur following prolonged fasting, heavy exercise, or medication interactions.",
            "why_context_matters": "Blood sugar varies with diet, fasting length, and sleep. A follow-up HbA1c test gives a clearer 3-month picture.",
            "when_to_consult": "Consult your physician for tailored dietary guidance or follow-up glycemic testing."
        },
        "fasting blood sugar": {
            "what_it_measures": "Fasting blood sugar measures circulating glucose following overnight fasting.",
            "elevated_associations": "Elevated readings can suggest altered glucose metabolism, stress, or carbohydrate intake.",
            "decreased_associations": "Lower readings can happen after vigorous exercise or skipping meals.",
            "why_context_matters": "A single fasting glucose value does not constitute a diagnosis and should be verified.",
            "when_to_consult": "Discuss with your doctor to explore lifestyle habits or confirmation tests."
        },
        "serum creatinine": {
            "what_it_measures": "Creatinine is a natural byproduct of normal muscle metabolism that is filtered and cleared by healthy kidneys.",
            "elevated_associations": "Mild elevations can occur with dehydration, heavy protein meals, strenuous weightlifting, or reduced kidney clearance.",
            "decreased_associations": "Lower levels are common in individuals with lower muscle mass or during pregnancy.",
            "why_context_matters": "Hydration status and muscle mass strongly influence creatinine levels at any given time.",
            "when_to_consult": "Share with your doctor to evaluate kidney filtration rate (eGFR) and hydration."
        },
        "blood urea nitrogen": {
            "what_it_measures": "BUN measures the amount of nitrogen in your blood that comes from the waste product urea.",
            "elevated_associations": "Higher BUN can occur with low water intake, high dietary protein, or reduced renal filtration.",
            "decreased_associations": "Low BUN is generally benign and may occur with low-protein diets or high fluid intake.",
            "why_context_matters": "BUN is typically reviewed alongside creatinine to differentiate hydration from kidney changes.",
            "when_to_consult": "Discuss your overall hydration and kidney panel during your regular checkup."
        },
        "total cholesterol": {
            "what_it_measures": "Total cholesterol evaluates the combined circulating lipid particles (LDL, HDL, and VLDL) in your bloodstream.",
            "elevated_associations": "Elevated cholesterol can be related to dietary saturated fats, physical activity patterns, and genetics.",
            "decreased_associations": "Very low levels can occur with malnutrition or liver metabolic variations.",
            "why_context_matters": "Cardiovascular risk depends on HDL, LDL, triglycerides, blood pressure, and family history together.",
            "when_to_consult": "Review your complete lipid profile with your doctor to discuss heart-healthy nutrition."
        },
        "triglycerides": {
            "what_it_measures": "Triglycerides are the most common type of fat in your blood, storing unused calories for future energy.",
            "elevated_associations": "Higher levels can occur after meals rich in simple sugars or alcohol, or with insulin resistance.",
            "decreased_associations": "Low levels are typically healthy and associated with active, low-fat diets.",
            "why_context_matters": "Triglycerides fluctuate quickly based on recent meals and fasting duration.",
            "when_to_consult": "Discuss healthy lifestyle and dietary adjustments with your physician."
        },
        "hba1c": {
            "what_it_measures": "HbA1c measures the percentage of your hemoglobin coated with sugar, showing average blood glucose over the past 2-3 months.",
            "elevated_associations": "Higher levels indicate consistently elevated blood sugar levels over several weeks.",
            "decreased_associations": "Lower levels indicate tight glycemic control or occasionally rapid red cell turnover.",
            "why_context_matters": "HbA1c provides a steady three-month average without being swayed by day-to-day fluctuations.",
            "when_to_consult": "Consult your doctor for personalized dietary planning and metabolic monitoring."
        }
    }

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or DEFAULT_GEMINI_MODEL

    def _call_gemini(self, prompt: str) -> str:
        """Execute Gemini model invocation."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Try google.genai
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e_genai:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                model = legacy_genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=self.EXPLANATION_SYSTEM_INSTRUCTION
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e_legacy:
                raise RuntimeError(f"Gemini API explanation request failed: {str(e_genai)} / {str(e_legacy)}")

        raise RuntimeError("Empty response received from Gemini.")

    def explain_tests(self, analyzed_tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate structured, patient-friendly explanations for all analyzed tests.
        """
        if not analyzed_tests:
            return []

        payload = [
            {
                "test_name": t.get("test_name"),
                "measured_value": str(t.get("measured_value")),
                "unit": t.get("unit"),
                "reference_range": str(t.get("reference_range")),
                "python_classification": t.get("status"),
                "python_reason": t.get("reason")
            }
            for t in analyzed_tests
        ]

        # Attempt Gemini LLM generation if API key is provided
        if self.api_key and self.api_key.strip():
            try:
                prompt = self.EXPLANATION_PROMPT_TEMPLATE.format(tests_json=json.dumps(payload, indent=2))
                raw_response = self._call_gemini(prompt)

                cleaned = raw_response.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)

                explanations = json.loads(cleaned)
                if isinstance(explanations, list) and len(explanations) > 0:
                    exp_map = {
                        item.get("test_name", "").lower(): item 
                        for item in explanations if isinstance(item, dict)
                    }

                    merged: List[Dict[str, Any]] = []
                    for t in analyzed_tests:
                        name_key = t.get("test_name", "").lower()
                        match = exp_map.get(name_key)
                        if match:
                            merged_item = dict(t)
                            merged_item["what_it_measures"] = match.get("what_it_measures", "Standard clinical analyte.")
                            merged_item["status_overview"] = match.get("status_overview", t.get("reason", ""))
                            merged_item["elevated_associations"] = match.get("elevated_associations", "Can be influenced by diet or hydration.")
                            merged_item["decreased_associations"] = match.get("decreased_associations", "Can be influenced by physiological factors.")
                            merged_item["why_context_matters"] = match.get("why_context_matters", "Isolated values need clinical correlation.")
                            merged_item["when_to_consult"] = match.get("when_to_consult", "Discuss with your healthcare provider.")
                            merged_item["explanation"] = (
                                f"{merged_item['status_overview']}\n\n"
                                f"• **What it measures**: {merged_item['what_it_measures']}\n"
                                f"• **Higher readings**: {merged_item['elevated_associations']}\n"
                                f"• **Lower readings**: {merged_item['decreased_associations']}\n"
                                f"• **Clinical Context**: {merged_item['why_context_matters']}\n"
                                f"• **Next Steps**: {merged_item['when_to_consult']}"
                            )
                            merged.append(merged_item)
                        else:
                            merged.append(self._fallback_single_explanation(t))
                    return merged
            except Exception:
                pass

        # Offline heuristic fallback
        return [self._fallback_single_explanation(t) for t in analyzed_tests]

    def _fallback_single_explanation(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Produce safe educational explanation from built-in medical heuristics."""
        item = dict(test)
        name_lower = (test.get("test_name") or "").lower()
        status = test.get("status", "Cannot determine")
        val = test.get("measured_value")
        unit = test.get("unit") or ""
        ref = test.get("reference_range") or "Not provided"

        # Search matching key in offline knowledge base
        matched_kb = None
        for key in self.OFFLINE_KB:
            if key in name_lower:
                matched_kb = self.OFFLINE_KB[key]
                break

        if matched_kb:
            item["what_it_measures"] = matched_kb["what_it_measures"]
            item["elevated_associations"] = matched_kb["elevated_associations"]
            item["decreased_associations"] = matched_kb["decreased_associations"]
            item["why_context_matters"] = matched_kb["why_context_matters"]
            item["when_to_consult"] = matched_kb["when_to_consult"]
        else:
            item["what_it_measures"] = f"{test.get('test_name', 'This parameter')} is a standard laboratory analyte evaluated during blood testing."
            item["elevated_associations"] = "Elevations can sometimes occur with temporary dehydration, dietary changes, recent illness, or stress."
            item["decreased_associations"] = "Lower readings may be associated with nutritional factors, hydration, or natural physiological variations."
            item["why_context_matters"] = "A single blood test cannot establish a diagnosis and must be viewed alongside your overall symptoms."
            item["when_to_consult"] = "Share these laboratory results with your doctor for professional medical interpretation."

        if status == "Normal":
            item["status_overview"] = f"Your measured value of {val} {unit} falls safely within the reference interval ({ref})."
        elif status == "High":
            item["status_overview"] = f"Your measured value of {val} {unit} is above the upper reference boundary ({ref})."
        elif status == "Low":
            item["status_overview"] = f"Your measured value of {val} {unit} is below the lower reference boundary ({ref})."
        else:
            item["status_overview"] = f"Your result of {val} {unit} could not be automatically compared because the reference range is {ref}."

        item["explanation"] = (
            f"{item['status_overview']}\n\n"
            f"• **What it measures**: {item['what_it_measures']}\n"
            f"• **Higher readings**: {item['elevated_associations']}\n"
            f"• **Lower readings**: {item['decreased_associations']}\n"
            f"• **Clinical Context**: {item['why_context_matters']}\n"
            f"• **Next Steps**: {item['when_to_consult']}"
        )
        item["lifestyle_or_next_steps"] = item["when_to_consult"]
        return item
