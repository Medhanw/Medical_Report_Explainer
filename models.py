"""
Pydantic Data Models for Medical Report Explainer.
Enforces strict schema validation for LLM outputs, clinical data parameters,
and numerical analysis results.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ReferenceRangeDetail(BaseModel):
    """Structured clinical reference interval boundaries."""
    low: Optional[float] = Field(None, description="Lower numeric reference threshold")
    high: Optional[float] = Field(None, description="Upper numeric reference threshold")
    display: Optional[str] = Field(None, description="Original raw text display of the reference range")
    sex_specific: Optional[str] = Field(None, description="Gender criteria if applicable (e.g. Male / Female)")
    age_specific: Optional[str] = Field(None, description="Age group criteria if applicable (e.g. Adult / Pediatric)")


class ExtractedBloodTest(BaseModel):
    """Individual blood test parameter extracted from lab report."""
    test_name: str = Field(..., description="Standardized name of the laboratory assay")
    value: Optional[Union[float, int, str]] = Field(None, description="Measured patient value (numeric or qualitative)")
    unit: Optional[str] = Field("", description="Unit of measurement, e.g. g/dL, mg/dL")
    reference_range: Optional[Union[ReferenceRangeDetail, str]] = Field(
        None, description="Biological reference range from the report"
    )

    @field_validator("test_name")
    @classmethod
    def clean_test_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            return "Unnamed Test"
        return cleaned


class PatientDemographics(BaseModel):
    """Patient demographic details extracted from report headers."""
    age: Optional[Union[int, float, str]] = Field(None, description="Patient age if specified")
    sex: Optional[str] = Field(None, description="Patient sex/gender if specified")
    report_date: Optional[str] = Field(None, description="Laboratory collection or report issue date")


class StructuredLabReport(BaseModel):
    """Complete validated report structure extracted by the LLM."""
    patient_info: PatientDemographics = Field(default_factory=PatientDemographics)
    tests: List[ExtractedBloodTest] = Field(default_factory=list)


class AnalyzedTestRecord(BaseModel):
    """Final validated record combining extraction, Python classification, and AI explanation."""
    test_name: str
    measured_value: Optional[Union[float, int, str]] = None
    unit: str = ""
    reference_range_display: str = "Not provided"
    status: str = "Cannot determine"  # Normal, High, Low, Cannot determine
    status_color: str = "gray"
    reason: str = ""
    what_it_measures: str = ""
    explanation: str = ""
    lifestyle_or_next_steps: str = ""
