"""
Medical Report Explainer - Modern Streamlit Clinical Dashboard.
Problem Statement 51: Generative AI Blood Test Analysis & Education.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from analyzer import MedicalRangeAnalyzer
from config import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_API_KEY,
    MAX_FILE_SIZE_MB,
    MEDICAL_DISCLAIMER,
    OUTPUTS_DIR,
    SAMPLES_DIR,
    SUPPORTED_FILE_EXTENSIONS,
)
from explainer import MedicalReportExplainer
from extractor import GeminiReportExtractor, ReportTextExtractor, ExtractionError
from report_generator import generate_patient_summary_pdf

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Medical Report Explainer | Clinical AI Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS FOR PROFESSIONAL LIGHT MEDICAL THEME
# =============================================================================
st.markdown(
    """
    <style>
    /* Main container background */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top Banner Header */
    .med-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #0D9488 100%);
        padding: 24px 32px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .med-header h1 {
        color: white !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .med-header p {
        color: #E2E8F0;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Disclaimer Box */
    .disclaimer-banner {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 24px;
        color: #991B1B;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    /* Metric KPI Cards */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 18px 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        text-align: center;
    }
    .metric-card .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .metric-card .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 4px;
        color: #64748B;
    }
    
    /* Card color variants */
    .card-total .metric-val { color: #1E3A8A; }
    .card-normal .metric-val { color: #16A34A; }
    .card-high .metric-val { color: #DC2626; }
    .card-low .metric-val { color: #2563EB; }
    .card-undetermined .metric-val { color: #64748B; }

    /* Custom Badges */
    .badge-normal {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #86EFAC;
        display: inline-block;
    }
    .badge-high {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #FCA5A5;
        display: inline-block;
    }
    .badge-low {
        background-color: #DBEAFE;
        color: #1D4ED8;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #93C5FD;
        display: inline-block;
    }
    .badge-undetermined {
        background-color: #F1F5F9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #CBD5E1;
        display: inline-block;
    }

    /* Explanation Card */
    .explanation-box {
        background-color: #FFFFFF;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .explanation-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 8px;
    }

    /* Sidebar aesthetics */
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9;
        border-right: 1px solid #E2E8F0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# HELPER FUNCTIONS & PIPELINE
# =============================================================================
def run_analysis_pipeline(
    file_bytes: bytes,
    file_name: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the complete processing pipeline:
    1. Digital Text Extraction (PyMuPDF / TXT)
    2. LLM Extraction & Pydantic Validation (Gemini)
    3. Python Numerical Range Analysis (MedicalRangeAnalyzer)
    4. AI Patient Explanation Generation (MedicalReportExplainer)
    """
    # Step 1: Text extraction
    raw_text = ReportTextExtractor.extract_text(file_bytes, file_name)

    # Step 2: Structured extraction with Pydantic schema validation
    extractor = GeminiReportExtractor(api_key=api_key, model_name=model_name)
    structured_report = extractor.extract_structured_data(raw_text)

    # Step 3: Pure-Python numerical analysis
    patient_sex = structured_report.patient_info.sex
    patient_age = structured_report.patient_info.age
    analyzed_tests = MedicalRangeAnalyzer.analyze_all_tests(
        tests=structured_report.tests,
        patient_sex=patient_sex,
        patient_age=patient_age,
    )

    # Step 4: AI explanation generation
    explainer = MedicalReportExplainer(api_key=api_key, model_name=model_name)
    explained_tests = explainer.explain_tests(analyzed_tests)

    # Step 5: Summary metrics
    summary_counts = MedicalRangeAnalyzer.get_summary_counts(explained_tests)

    return {
        "raw_text": raw_text,
        "patient_info": structured_report.patient_info.model_dump(),
        "extracted_tests": [t.model_dump() for t in structured_report.tests],
        "explained_tests": explained_tests,
        "summary": summary_counts,
    }


# =============================================================================
# SIDEBAR CONTROLS & API CONFIGURATION
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ System Settings")
    
    # API Key Input
    user_api_key = st.text_input(
        "Google Gemini API Key",
        value=GEMINI_API_KEY,
        type="password",
        help="Reads from .env by default. You can enter or override your Gemini API key here.",
    )
    
    # Model Selection
    selected_model = st.selectbox(
        "Gemini Model",
        options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        index=0,
        help="Select Google Gen AI model for extraction and empathetic explanations.",
    )

    if user_api_key:
        st.success("🟢 API Key Configured", icon="✅")
    else:
        st.info("🟡 Running in Offline Heuristic Fallback Mode. Enter a Gemini API Key to enable live LLM synthesis.", icon="ℹ️")

    st.markdown("---")
    st.markdown("### 🧪 Quick-Load Synthetic Samples")
    st.markdown("Test the 5 required evaluation scenarios with one click:")

    sample_options = {
        "None": None,
        "1. All Normal CBC": "01_all_values_normal.pdf",
        "2. One High Glucose": "02_one_high_value.pdf",
        "3. One Low Hemoglobin": "03_one_low_value.pdf",
        "4. Missing Reference Ranges": "04_missing_reference_range.pdf",
        "5. Multi-Panel (14 tests)": "05_multiple_blood_test_parameters.pdf",
    }
    selected_sample = st.selectbox("Choose a sample report:", list(sample_options.keys()))

    st.markdown("---")
    st.markdown("### 📄 Technical Documentation")
    tech_pdf_path = Path(__file__).parent / "docs" / "Medical_Report_Explainer_Detailed_Report.pdf"
    if tech_pdf_path.exists():
        with open(tech_pdf_path, "rb") as f_pdf:
            st.download_button(
                label="📥 Download Academic Report (15 Pages)",
                data=f_pdf.read(),
                file_name="Medical_Report_Explainer_Detailed_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.caption("Generative AI – Assignment 3 | Problem Statement 51")


# =============================================================================
# MAIN INTERFACE
# =============================================================================

# SECTION A: HEADER & INTRODUCTION
st.markdown(
    """
    <div class="med-header">
        <h1>🩺 Medical Report Explainer</h1>
        <p>Generative AI Blood Test Analysis & Plain-English Patient Education Engine (Problem Statement 51)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# SECTION F: MEDICAL DISCLAIMER CALLOUT
st.markdown(
    f"""
    <div class="disclaimer-banner">
        <b>⚠️ Medical Disclaimer:</b> {MEDICAL_DISCLAIMER}
    </div>
    """,
    unsafe_allow_html=True,
)

# SECTION B: UPLOAD REPORT & SAMPLE DISPATCH
st.markdown("### 📤 Upload Blood Test Report")
st.markdown("Upload your clinical laboratory report in **PDF** or **TXT** format (maximum 10MB):")

col_upload, col_sample_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file",
        type=["pdf", "txt"],
        help="Upload a digital PDF report with selectable text or a plain text document.",
    )

file_bytes_to_process = None
file_name_to_process = None

if uploaded_file is not None:
    file_bytes_to_process = uploaded_file.read()
    file_name_to_process = uploaded_file.name
    with col_sample_info:
        st.info(f"📁 **Uploaded File:** `{file_name_to_process}`\n\n**Size:** `{len(file_bytes_to_process)/1024:.1f} KB`")
elif selected_sample and selected_sample != "None":
    sample_filename = sample_options[selected_sample]
    sample_file_path = SAMPLES_DIR / sample_filename
    if sample_file_path.exists():
        with open(sample_file_path, "rb") as f:
            file_bytes_to_process = f.read()
        file_name_to_process = sample_filename
        with col_sample_info:
            st.success(f"🧪 **Loaded Sample:** `{file_name_to_process}`\n\nScenario: {selected_sample}")

# Analysis Action Button
analyze_clicked = st.button("🔬 Analyze Report", type="primary", use_container_width=True)

if file_bytes_to_process and (analyze_clicked or "analysis_data" in st.session_state):
    # If the user clicked Analyze or has already analyzed this file
    if analyze_clicked or st.session_state.get("current_file") != file_name_to_process:
        with st.spinner("⏳ Extracting text, executing Python numerical rules, and generating explanations..."):
            try:
                results = run_analysis_pipeline(
                    file_bytes=file_bytes_to_process,
                    file_name=file_name_to_process,
                    api_key=user_api_key,
                    model_name=selected_model,
                )
                st.session_state["analysis_data"] = results
                st.session_state["current_file"] = file_name_to_process
                st.success("Analysis complete!")
            except ExtractionError as e:
                st.error(f"❌ Document Error: {str(e)}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Processing Error: {str(e)}")
                st.stop()

    data = st.session_state.get("analysis_data")

    if data:
        summary = data["summary"]
        patient_info = data["patient_info"]
        explained_tests = data["explained_tests"]

        st.markdown("---")
        st.markdown("### 📊 Clinical Dashboard Summary")

        # Patient Info Header
        p_age = patient_info.get("age") or "Not Specified"
        p_sex = patient_info.get("sex") or "Not Specified"
        p_date = patient_info.get("report_date") or "Not Specified"
        st.caption(f"👤 **Patient Demographics:** Age: **{p_age}** | Biological Sex: **{p_sex}** | Report Date: **{p_date}**")

        # SECTION C: METRIC KPI CARDS
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.markdown(
                f"""<div class="metric-card card-total">
                    <div class="metric-val">{summary.get('Total', 0)}</div>
                    <div class="metric-label">Total Tests</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with kpi2:
            st.markdown(
                f"""<div class="metric-card card-normal">
                    <div class="metric-val">{summary.get('Normal', 0)}</div>
                    <div class="metric-label">Normal</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with kpi3:
            st.markdown(
                f"""<div class="metric-card card-high">
                    <div class="metric-val">{summary.get('High', 0)}</div>
                    <div class="metric-label">Elevated / High</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with kpi4:
            st.markdown(
                f"""<div class="metric-card card-low">
                    <div class="metric-val">{summary.get('Low', 0)}</div>
                    <div class="metric-label">Decreased / Low</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with kpi5:
            st.markdown(
                f"""<div class="metric-card card-undetermined">
                    <div class="metric-val">{summary.get('Cannot determine', 0)}</div>
                    <div class="metric-label">Undetermined</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Tab navigation for Results Table vs Charts
        tab_table, tab_charts, tab_raw = st.tabs(["📋 Results Table", "📈 Status Distribution", "🔍 Raw Extracted Text"])

        with tab_table:
            # Build DataFrame for results
            table_rows = []
            for t in explained_tests:
                status = t.get("status", "Cannot determine")
                if status == "Normal":
                    badge = "🟢 Normal"
                elif status == "High":
                    badge = "🔴 High"
                elif status == "Low":
                    badge = "🔵 Low"
                else:
                    badge = "⚪ Undetermined"

                table_rows.append({
                    "Status": badge,
                    "Test Parameter": t.get("test_name"),
                    "Measured Value": t.get("measured_value"),
                    "Unit": t.get("unit") or "-",
                    "Reference Interval": t.get("reference_range") or "Not provided",
                    "Evaluation Note": t.get("reason"),
                })

            df_results = pd.DataFrame(table_rows)
            st.dataframe(df_results, use_container_width=True, hide_index=True)

        with tab_charts:
            chart_data = pd.DataFrame({
                "Classification": ["Normal", "High", "Low", "Undetermined"],
                "Count": [
                    summary.get("Normal", 0),
                    summary.get("High", 0),
                    summary.get("Low", 0),
                    summary.get("Cannot determine", 0),
                ]
            }).set_index("Classification")
            st.bar_chart(chart_data, color="#2563EB", use_container_width=True)

        with tab_raw:
            st.text_area("Extracted Document Text", data["raw_text"], height=200)

        # SECTION D: INDIVIDUAL TEST EXPLANATIONS
        st.markdown("---")
        st.markdown("### 💡 Plain-English Test Explanations")
        st.markdown("Expand any test below to view clear, non-diagnostic clinical explanations and context:")

        for idx, t in enumerate(explained_tests):
            status = t.get("status", "Cannot determine")
            status_icon = "🟢" if status == "Normal" else ("🔴" if status == "High" else ("🔵" if status == "Low" else "⚪"))
            
            exp_label = f"{status_icon} **{t.get('test_name')}**: {t.get('measured_value')} {t.get('unit')} (Reference: {t.get('reference_range')}) — **{status}**"
            
            with st.expander(exp_label, expanded=(status in ["High", "Low"])):
                col_info, col_status = st.columns([3, 1])
                with col_status:
                    if status == "Normal":
                        st.markdown('<span class="badge-normal">Status: Normal</span>', unsafe_allow_html=True)
                    elif status == "High":
                        st.markdown('<span class="badge-high">Status: High</span>', unsafe_allow_html=True)
                    elif status == "Low":
                        st.markdown('<span class="badge-low">Status: Low</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-undetermined">Status: Undetermined</span>', unsafe_allow_html=True)

                with col_info:
                    st.markdown(f"**What it measures:** {t.get('what_it_measures', 'Standard blood analyte.')}")
                    st.markdown(f"**Classification Note:** {t.get('reason')}")

                st.markdown("---")
                col_exp_l, col_exp_r = st.columns(2)
                with col_exp_l:
                    st.markdown(f"**📈 Higher Readings May Indicate:**\n{t.get('elevated_associations', 'Mild elevations can be caused by hydration or diet.')}")
                    st.markdown(f"**📉 Lower Readings May Indicate:**\n{t.get('decreased_associations', 'Mild reductions may be influenced by nutritional factors.')}")
                with col_exp_r:
                    st.markdown(f"**🩺 Clinical Context:**\n{t.get('why_context_matters', 'A single test cannot establish a diagnosis.')}")
                    st.markdown(f"**💬 Next Steps:**\n{t.get('when_to_consult', 'Share these results with your healthcare provider.')}")

        # SECTION E: DOWNLOADS
        st.markdown("---")
        st.markdown("### 📥 Download Results & Reports")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)

        with col_dl1:
            # Download Extracted JSON
            json_str = json.dumps(data["extracted_tests"], indent=2)
            st.download_button(
                label="📄 Download Extracted JSON",
                data=json_str,
                file_name=f"{Path(file_name_to_process).stem}_extracted.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_dl2:
            # Download Analyzed CSV
            csv_df = pd.DataFrame(explained_tests)
            csv_data = csv_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Download Analyzed CSV",
                data=csv_data,
                file_name=f"{Path(file_name_to_process).stem}_analysis.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_dl3:
            # Generate and Download Analysis Summary PDF
            try:
                pdf_summary_path = str(OUTPUTS_DIR / f"{Path(file_name_to_process).stem}_patient_summary.pdf")
                generate_patient_summary_pdf(
                    analyzed_tests=explained_tests,
                    patient_info=patient_info,
                    output_filepath=pdf_summary_path
                )
                with open(pdf_summary_path, "rb") as pdf_file:
                    st.download_button(
                        label="📑 Download Summary PDF",
                        data=pdf_file.read(),
                        file_name=f"{Path(file_name_to_process).stem}_patient_summary.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as e:
                st.warning(f"Summary PDF compilation note: {str(e)}")

else:
    # Instructions when no file is uploaded or analyzed yet
    st.info("👆 Please upload a PDF/TXT blood report above or pick a sample scenario from the sidebar to begin analysis.")

    # Educational Information Cards
    st.markdown("#### 🔍 How It Works")
    col_step1, col_step2, col_step3 = st.columns(3)
    with col_step1:
        st.markdown(
            """
            <div class="explanation-box">
                <div class="explanation-title">1. Document Extraction</div>
                Extracts digital text from uploaded PDF or TXT reports via PyMuPDF. Verifies document legibility and detects scanned files.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_step2:
        st.markdown(
            """
            <div class="explanation-box">
                <div class="explanation-title">2. Python Classification</div>
                Pure-Python mathematical boundary engine determines if values are Normal, High, Low, or Undetermined without LLM hallucination.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_step3:
        st.markdown(
            """
            <div class="explanation-box">
                <div class="explanation-title">3. Empathetic Explanations</div>
                Gemini LLM synthesizes clear, educational explanations of each parameter, its physiological role, and next steps for your physician.
            </div>
            """,
            unsafe_allow_html=True,
        )
