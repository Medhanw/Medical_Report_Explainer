"""
Medical Report Explainer - Python Numerical Analyzer Module.

This module is strictly responsible for rule-based numerical evaluation of
blood test parameters against reference ranges. It enforces the requirement
that LLMs are NOT allowed to decide the numerical classification.

Classifications:
- Normal: value falls within the provided reference interval.
- High: value exceeds the upper reference boundary.
- Low: value is below the lower reference boundary.
- Cannot determine: reference range or value is missing, ambiguous, or unsupported.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from models import ExtractedBloodTest, ReferenceRangeDetail, AnalyzedTestRecord


class MedicalRangeAnalyzer:
    """
    Pure-Python parser and evaluator for laboratory measured values against
    clinical reference ranges.
    """

    # Common qualitative negative/normal markers
    QUALITATIVE_NORMAL = {"negative", "non-reactive", "not detected", "nil", "normal", "absent", "clear"}
    QUALITATIVE_ABNORMAL = {"positive", "reactive", "detected", "present", "abnormal"}

    @staticmethod
    def clean_string(text: Optional[str]) -> str:
        """Sanitize text by stripping whitespaces and normalizing dashes."""
        if not text:
            return ""
        sanitized = re.sub(r"[—–−]", "-", str(text).strip())
        return sanitized

    @classmethod
    def extract_numeric_value(cls, val: Any) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract floating-point number and any prefix qualifier (e.g., '<', '>')
        from a measured value representation.
        Returns: (numeric_value, operator_prefix)
        """
        if val is None:
            return None, None
        
        if isinstance(val, (int, float)):
            if math.isnan(val):
                return None, None
            return float(val), None

        text = cls.clean_string(str(val))
        if not text:
            return None, None

        # Check for operators like '< 0.5' or '> 100' or '<= 5.7'
        op_match = re.match(r"^([<>]=?|≤|≥)?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\b", text)
        if op_match:
            op, num_str = op_match.groups()
            cleaned_num = num_str.replace(",", "")
            try:
                num = float(cleaned_num)
                op_normalized = "<=" if op == "≤" else (">=" if op == "≥" else op)
                return num, op_normalized
            except ValueError:
                pass

        # Search for any decimal or integer number
        general_match = re.search(r"[-+]?[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?", text)
        if general_match:
            cleaned_num = general_match.group(0).replace(",", "")
            try:
                return float(cleaned_num), None
            except ValueError:
                pass

        return None, None

    @classmethod
    def resolve_sex_or_age_specific_range(
        cls, 
        range_str: str, 
        patient_sex: Optional[str] = None, 
        patient_age: Optional[Union[int, float, str]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Extract specific reference range if the string splits ranges by Male/Female or Adult/Child.
        Returns (resolved_range_str, note)
        """
        cleaned = cls.clean_string(range_str)
        if not cleaned:
            return "", "Reference range is empty or not specified."

        # Check for Male / Female markers
        male_pattern = re.search(r"(?:Male|Men|M)\s*[:=]\s*([0-9.<>=\-\s–to]+)", cleaned, re.IGNORECASE)
        female_pattern = re.search(r"(?:Female|Women|F|Fem)\s*[:=]\s*([0-9.<>=\-\s–to]+)", cleaned, re.IGNORECASE)

        if male_pattern or female_pattern:
            norm_sex = patient_sex.strip().upper() if isinstance(patient_sex, str) else None
            if norm_sex in ["M", "MALE", "MAN"]:
                if male_pattern:
                    return male_pattern.group(1).strip(), "Using Male reference range as per patient profile."
            elif norm_sex in ["F", "FEMALE", "WOMAN"]:
                if female_pattern:
                    return female_pattern.group(1).strip(), "Using Female reference range as per patient profile."
            else:
                return cleaned, "Report contains sex-specific ranges, but patient sex is unspecified."

        return cleaned, None

    @classmethod
    def parse_reference_range(
        cls, 
        range_str: str
    ) -> Tuple[Optional[float], Optional[float], str]:
        """
        Parse reference range string into (min_val, max_val, interpretation_type).
        """
        cleaned = cls.clean_string(range_str)
        if not cleaned:
            return None, None, "unparseable"

        # Missing indicators
        if cleaned.lower() in {"none", "null", "n/a", "na", "not provided", "not established", "unknown", "-", "nil"}:
            return None, None, "unparseable"

        # 1. Upper limit pattern: '< 100', '<= 5.7', 'Up to 200', 'Less than 150'
        upper_match = re.search(r"^(?:<|<=|≤|up to|less than)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
        if upper_match:
            try:
                max_val = float(upper_match.group(1).replace(",", ""))
                return None, max_val, "upper_limit"
            except ValueError:
                pass

        # 2. Lower limit pattern: '> 60', '>= 60', 'Greater than 40', 'More than 50'
        lower_match = re.search(r"^(?:>|>=|≥|greater than|more than)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
        if lower_match:
            try:
                min_val = float(lower_match.group(1).replace(",", ""))
                return min_val, None, "lower_limit"
            except ValueError:
                pass

        # 3. Standard interval: '13.5 - 17.5' or '13.5 to 17.5'
        range_match = re.search(
            r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:-|to)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)",
            cleaned,
            re.IGNORECASE
        )
        if range_match:
            try:
                min_val = float(range_match.group(1).replace(",", ""))
                max_val = float(range_match.group(2).replace(",", ""))
                if min_val > max_val:
                    min_val, max_val = max_val, min_val
                return min_val, max_val, "bounded"
            except ValueError:
                pass

        return None, None, "unparseable"

    @classmethod
    def evaluate_test(
        cls,
        test_name: str,
        measured_value: Any,
        reference_range: Any,
        unit: Optional[str] = None,
        patient_sex: Optional[str] = None,
        patient_age: Optional[Union[int, float, str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single blood test parameter.
        Returns a dictionary with status, status_color, reason, and parsed metrics.
        """
        # Extract display string for reference range
        raw_range_str = ""
        low_bound = None
        high_bound = None
        if isinstance(reference_range, ReferenceRangeDetail):
            raw_range_str = reference_range.display or ""
            low_bound = reference_range.low
            high_bound = reference_range.high
        elif isinstance(reference_range, dict):
            raw_range_str = reference_range.get("display") or ""
            low_bound = reference_range.get("low")
            high_bound = reference_range.get("high")
        elif reference_range is not None:
            raw_range_str = cls.clean_string(str(reference_range))

        raw_val_str = cls.clean_string(str(measured_value) if measured_value is not None else "")

        result: Dict[str, Any] = {
            "test_name": test_name or "Unknown Test",
            "measured_value": measured_value,
            "unit": unit or "",
            "reference_range": raw_range_str or "Not provided",
            "status": "Cannot determine",
            "status_color": "gray",
            "reason": "",
            "parsed_value": None,
            "parsed_min": None,
            "parsed_max": None
        }

        # Check for missing measured value
        if not raw_val_str or raw_val_str.lower() in {"none", "null", "n/a", "pending", "not tested", ""}:
            result["status"] = "Cannot determine"
            result["reason"] = "Measured value is missing or unrecorded in the report."
            return result

        # Check for categorical qualitative values (e.g. Negative / Positive)
        val_lower = raw_val_str.lower()
        range_lower = raw_range_str.lower()
        if val_lower in cls.QUALITATIVE_NORMAL:
            if not raw_range_str or any(qn in range_lower for qn in cls.QUALITATIVE_NORMAL):
                result["status"] = "Normal"
                result["status_color"] = "green"
                result["reason"] = f"Result '{raw_val_str}' matches standard negative/normal qualitative criteria."
                return result

        if val_lower in cls.QUALITATIVE_ABNORMAL:
            result["status"] = "High"
            result["status_color"] = "red"
            result["reason"] = f"Result '{raw_val_str}' indicates an abnormal/reactive qualitative finding."
            return result

        # Extract numeric value
        num_val, val_op = cls.extract_numeric_value(measured_value)
        if num_val is None:
            result["status"] = "Cannot determine"
            result["reason"] = f"Measured value '{raw_val_str}' could not be parsed as a numerical value."
            return result

        result["parsed_value"] = num_val

        # Check for missing reference range
        if not raw_range_str or raw_range_str.lower() in {"none", "null", "n/a", "na", "not provided", "unknown", "-", "nil"}:
            result["status"] = "Cannot determine"
            result["reason"] = "Reference range is missing or not provided in the report."
            return result

        # Resolve sex/age specifics if present
        resolved_range, demog_note = cls.resolve_sex_or_age_specific_range(
            raw_range_str, patient_sex=patient_sex, patient_age=patient_age
        )

        min_val, max_val, r_type = cls.parse_reference_range(resolved_range)
        
        # If regex didn't parse but Pydantic had low/high bounds, use them
        if r_type == "unparseable":
            if low_bound is not None and high_bound is not None:
                min_val, max_val = low_bound, high_bound
                r_type = "bounded"
            elif high_bound is not None:
                max_val = high_bound
                r_type = "upper_limit"
            elif low_bound is not None:
                min_val = low_bound
                r_type = "lower_limit"

        result["parsed_min"] = min_val
        result["parsed_max"] = max_val

        if r_type == "unparseable":
            result["status"] = "Cannot determine"
            result["reason"] = f"Reference range '{raw_range_str}' could not be reliably interpreted into numerical boundaries."
            return result

        note_suffix = f" ({demog_note})" if demog_note else ""
        eps = 1e-6  # Inclusive boundary margin for float stability

        # 1. Bounded range: [min_val, max_val]
        if r_type == "bounded" and min_val is not None and max_val is not None:
            if num_val < (min_val - eps):
                result["status"] = "Low"
                result["status_color"] = "blue"
                result["reason"] = f"Value {num_val} is below the lower reference boundary ({min_val} - {max_val}){note_suffix}."
            elif num_val > (max_val + eps):
                result["status"] = "High"
                result["status_color"] = "red"
                result["reason"] = f"Value {num_val} is above the upper reference boundary ({min_val} - {max_val}){note_suffix}."
            else:
                result["status"] = "Normal"
                result["status_color"] = "green"
                result["reason"] = f"Value {num_val} falls within the normal reference interval ({min_val} - {max_val}){note_suffix}."
            return result

        # 2. Upper limit: <= max_val
        if r_type == "upper_limit" and max_val is not None:
            if num_val <= (max_val + eps):
                result["status"] = "Normal"
                result["status_color"] = "green"
                result["reason"] = f"Value {num_val} is within acceptable threshold (<= {max_val}){note_suffix}."
            else:
                result["status"] = "High"
                result["status_color"] = "red"
                result["reason"] = f"Value {num_val} exceeds upper reference boundary of {max_val}{note_suffix}."
            return result

        # 3. Lower limit: >= min_val
        if r_type == "lower_limit" and min_val is not None:
            if num_val >= (min_val - eps):
                result["status"] = "Normal"
                result["status_color"] = "green"
                result["reason"] = f"Value {num_val} satisfies minimum requirement (>= {min_val}){note_suffix}."
            else:
                result["status"] = "Low"
                result["status_color"] = "blue"
                result["reason"] = f"Value {num_val} is below lower reference boundary of {min_val}{note_suffix}."
            return result

        result["status"] = "Cannot determine"
        result["reason"] = f"Reference range '{raw_range_str}' could not be definitively classified."
        return result

    @classmethod
    def analyze_all_tests(
        cls, 
        tests: Union[List[Dict[str, Any]], List[ExtractedBloodTest]], 
        patient_sex: Optional[str] = None, 
        patient_age: Optional[Union[int, float, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a list of extracted blood tests (either dictionaries or ExtractedBloodTest Pydantic models).
        """
        analyzed_results = []
        for test in tests:
            if isinstance(test, ExtractedBloodTest):
                t_name = test.test_name
                val = test.value
                unit = test.unit
                ref_range = test.reference_range
            elif isinstance(test, dict):
                t_name = test.get("test_name", "")
                val = test.get("value") if "value" in test else test.get("measured_value")
                unit = test.get("unit", "")
                ref_range = test.get("reference_range")
            else:
                continue

            analysis = cls.evaluate_test(
                test_name=t_name,
                measured_value=val,
                reference_range=ref_range,
                unit=unit,
                patient_sex=patient_sex,
                patient_age=patient_age
            )
            analyzed_results.append(analysis)
        return analyzed_results

    @classmethod
    def get_summary_counts(cls, analyzed_tests: List[Dict[str, Any]]) -> Dict[str, int]:
        """Compute aggregate counts for dashboard metric cards."""
        counts = {
            "Total": len(analyzed_tests),
            "Normal": 0,
            "High": 0,
            "Low": 0,
            "Cannot determine": 0
        }
        for item in analyzed_tests:
            st = item.get("status", "Cannot determine")
            if st in counts:
                counts[st] += 1
            else:
                counts["Cannot determine"] += 1
        return counts
