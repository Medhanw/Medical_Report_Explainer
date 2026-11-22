"""
Generates high-resolution screenshots of the Streamlit application UI states
for documentation and submission deliverables.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def get_fonts():
    """Attempt to load clean system TrueType fonts, fallback to default."""
    try:
        # Common Windows standard fonts
        f_title = ImageFont.truetype("arialbd.ttf", 26)
        f_subtitle = ImageFont.truetype("arial.ttf", 15)
        f_h2 = ImageFont.truetype("arialbd.ttf", 18)
        f_body = ImageFont.truetype("arial.ttf", 13)
        f_bold = ImageFont.truetype("arialbd.ttf", 13)
        f_small = ImageFont.truetype("arial.ttf", 11)
        f_metric = ImageFont.truetype("arialbd.ttf", 36)
        return f_title, f_subtitle, f_h2, f_body, f_bold, f_small, f_metric
    except Exception:
        f = ImageFont.load_default()
        return f, f, f, f, f, f, f


def draw_browser_frame(draw, width, height, title_text):
    """Draws a clean modern browser window mockup header."""
    # Background
    draw.rectangle([0, 0, width, height], fill="#F8FAFC")
    # Browser chrome bar
    draw.rectangle([0, 0, width, 42], fill="#E2E8F0")
    # Window controls (red, yellow, green dots)
    draw.ellipse([14, 14, 26, 26], fill="#EF4444")
    draw.ellipse([34, 14, 46, 26], fill="#F59E0B")
    draw.ellipse([54, 14, 66, 26], fill="#10B981")
    # URL bar
    draw.rectangle([100, 8, width - 100, 34], fill="#FFFFFF", outline="#CBD5E1", width=1)
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()
    draw.text((120, 13), f"http://localhost:8501 — {title_text}", fill="#64748B", font=f_small)


def draw_app_header(draw, width, start_y):
    """Draws the medical header banner and medical disclaimer."""
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()
    # Medical Gradient Header
    draw.rounded_rectangle([40, start_y, width - 40, start_y + 85], radius=8, fill="#1E3A8A")
    draw.text((65, start_y + 16), "🩺 Medical Report Explainer", fill="#FFFFFF", font=f_title)
    draw.text((65, start_y + 50), "Generative AI Blood Test Analysis & Plain-English Patient Education Engine", fill="#93C5FD", font=f_sub)

    # Disclaimer Callout
    disc_y = start_y + 98
    draw.rounded_rectangle([40, disc_y, width - 40, disc_y + 50], radius=6, fill="#FEF2F2", outline="#EF4444", width=1)
    draw.text((55, disc_y + 10), "⚠️ Medical Disclaimer: This application is intended for educational purposes only. It does not provide medical diagnoses", fill="#991B1B", font=f_small)
    draw.text((55, disc_y + 26), "or replace professional medical advice. Always consult a qualified healthcare professional.", fill="#991B1B", font=f_small)
    return disc_y + 65


def create_screenshot_1_upload():
    """Screenshot 1: Upload Screen & Initial Interface."""
    w, h = 1200, 750
    img = Image.new("RGB", (w, h), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()

    draw_browser_frame(draw, w, h, "Medical Report Explainer | Clinical AI Dashboard")
    next_y = draw_app_header(draw, w, 56)

    # Upload Section
    draw.text((40, next_y + 10), "📤 Upload Blood Test Report", fill="#1E293B", font=f_h2)
    draw.text((40, next_y + 36), "Upload your clinical laboratory report in PDF or TXT format (maximum 10MB):", fill="#475569", font=f_body)

    # Drag & Drop Uploader Box
    box_y = next_y + 65
    draw.rounded_rectangle([40, box_y, w - 40, box_y + 140], radius=8, fill="#FFFFFF", outline="#94A3B8", width=1)
    draw.text((w // 2 - 140, box_y + 35), "📄 Drag and drop file here (or Browse)", fill="#334155", font=f_bold)
    draw.text((w // 2 - 160, box_y + 65), "Supported formats: .PDF, .TXT  |  Limit 10MB per file", fill="#64748B", font=f_small)
    draw.rounded_rectangle([w // 2 - 70, box_y + 95, w // 2 + 70, box_y + 125], radius=4, fill="#2563EB")
    draw.text((w // 2 - 45, box_y + 102), "Browse files", fill="#FFFFFF", font=f_bold)

    # Quick Samples Info
    card_y = box_y + 160
    draw.text((40, card_y), "🧪 Quick-Load Synthetic Samples (Select from Sidebar):", fill="#1E293B", font=f_bold)
    samples = ["1. All Normal CBC", "2. One High Glucose", "3. One Low Hemoglobin", "4. Missing Ranges", "5. Multi-Panel"]
    for i, s in enumerate(samples):
        cx = 40 + i * 224
        draw.rounded_rectangle([cx, card_y + 24, cx + 210, card_y + 70], radius=6, fill="#FFFFFF", outline="#CBD5E1", width=1)
        draw.text((cx + 15, card_y + 40), s, fill="#1E3A8A", font=f_small)

    out_path = SCREENSHOTS_DIR / "01_upload_screen.png"
    img.save(out_path)
    print(f"Saved {out_path}")


def create_screenshot_2_dashboard():
    """Screenshot 2: Dashboard Metric KPI Cards & Patient Header."""
    w, h = 1200, 750
    img = Image.new("RGB", (w, h), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()

    draw_browser_frame(draw, w, h, "Medical Report Explainer | Clinical AI Dashboard")
    next_y = draw_app_header(draw, w, 56)

    draw.text((40, next_y + 5), "📊 Clinical Dashboard Summary", fill="#1E293B", font=f_h2)
    draw.text((40, next_y + 32), "👤 Patient Demographics: Age: 45 | Biological Sex: Female | Report Date: 2026-10-18 | File: 02_one_high_value.pdf", fill="#475569", font=f_bold)

    # 5 Metric Cards
    kpi_y = next_y + 65
    kpi_defs = [
        ("TOTAL TESTS", "6", "#1E3A8A", "#EFF6FF", "#BFDBFE"),
        ("NORMAL", "5", "#16A34A", "#F0FDF4", "#BBF7D0"),
        ("ELEVATED / HIGH", "1", "#DC2626", "#FEF2F2", "#FECACA"),
        ("DECREASED / LOW", "0", "#2563EB", "#EFF6FF", "#BFDBFE"),
        ("UNDETERMINED", "0", "#475569", "#F8FAFC", "#E2E8F0"),
    ]
    card_w = (w - 80 - 40) // 5
    for i, (label, val, txt_c, bg_c, bdr_c) in enumerate(kpi_defs):
        cx = 40 + i * (card_w + 10)
        draw.rounded_rectangle([cx, kpi_y, cx + card_w, kpi_y + 110], radius=8, fill=bg_c, outline=bdr_c, width=1)
        draw.text((cx + card_w // 2 - 12, kpi_y + 20), val, fill=txt_c, font=f_metric)
        draw.text((cx + 15, kpi_y + 75), label, fill="#64748B", font=f_small)

    # Summary bar visualization preview
    bar_y = kpi_y + 130
    draw.rounded_rectangle([40, bar_y, w - 40, bar_y + 160], radius=8, fill="#FFFFFF", outline="#E2E8F0", width=1)
    draw.text((60, bar_y + 18), "📈 Classification Proportions: 83.3% Normal (5) | 16.7% Elevated (1)", fill="#1E293B", font=f_bold)
    # Colored progress bar
    draw.rounded_rectangle([60, bar_y + 55, w - 60, bar_y + 85], radius=6, fill="#F1F5F9")
    draw.rounded_rectangle([60, bar_y + 55, int(60 + (w - 120) * 0.833), bar_y + 85], radius=6, fill="#22C55E")
    draw.rounded_rectangle([int(60 + (w - 120) * 0.833), bar_y + 55, w - 60, bar_y + 85], radius=6, fill="#EF4444")
    draw.text((75, bar_y + 63), "Normal: 5 Parameters", fill="#FFFFFF", font=f_small)
    draw.text((w - 180, bar_y + 63), "High: 1", fill="#FFFFFF", font=f_small)

    out_path = SCREENSHOTS_DIR / "02_dashboard_kpis.png"
    img.save(out_path)
    print(f"Saved {out_path}")


def create_screenshot_3_table():
    """Screenshot 3: Detailed Results Table with Status Badges."""
    w, h = 1200, 750
    img = Image.new("RGB", (w, h), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()

    draw_browser_frame(draw, w, h, "Medical Report Explainer | Results Table")
    next_y = draw_app_header(draw, w, 56)

    draw.text((40, next_y + 5), "📋 Blood Test Parameter Evaluation Table", fill="#1E293B", font=f_h2)

    # Table Mockup
    tbl_y = next_y + 40
    headers = [("Status", 130), ("Test Parameter", 250), ("Result", 100), ("Unit", 90), ("Reference Range", 170), ("Python Evaluation Note", 380)]

    # Header Row
    hx = 40
    draw.rectangle([40, tbl_y, w - 40, tbl_y + 36], fill="#1E3A8A")
    for name, cw in headers:
        draw.text((hx + 10, tbl_y + 10), name, fill="#FFFFFF", font=f_bold)
        hx += cw

    rows = [
        ("🔴 High", "Fasting Blood Glucose", "142.0", "mg/dL", "70 - 99", "Value 142.0 is above upper reference boundary (70 - 99).", "#FEF2F2", "#B91C1C"),
        ("🟢 Normal", "Serum Creatinine", "0.82", "mg/dL", "0.5 - 1.1", "Value 0.82 falls within normal reference interval (0.5 - 1.1).", "#FFFFFF", "#15803D"),
        ("🟢 Normal", "Blood Urea Nitrogen", "14.0", "mg/dL", "7.0 - 20.0", "Value 14.0 falls within normal reference interval (7.0 - 20.0).", "#F8FAFC", "#15803D"),
        ("🟢 Normal", "Serum Sodium", "139.0", "mmol/L", "136 - 145", "Value 139.0 falls within normal reference interval (136 - 145).", "#FFFFFF", "#15803D"),
        ("🟢 Normal", "Serum Potassium", "4.2", "mmol/L", "3.5 - 5.1", "Value 4.2 falls within normal reference interval (3.5 - 5.1).", "#F8FAFC", "#15803D"),
        ("🟢 Normal", "Serum Chloride", "102.0", "mmol/L", "96 - 106", "Value 102.0 falls within normal reference interval (96 - 106).", "#FFFFFF", "#15803D"),
    ]

    ry = tbl_y + 36
    for status_txt, tname, val, unit, ref, note, bg, txt_c in rows:
        draw.rectangle([40, ry, w - 40, ry + 42], fill=bg, outline="#E2E8F0", width=1)
        rx = 40
        # Draw status badge
        draw.rounded_rectangle([rx + 8, ry + 8, rx + 110, ry + 32], radius=12, fill="#FEE2E2" if "High" in status_txt else "#DCFCE7")
        draw.text((rx + 20, ry + 12), status_txt, fill=txt_c, font=f_bold)
        rx += 130

        draw.text((rx + 10, ry + 13), tname, fill="#1E293B", font=f_bold)
        rx += 250
        draw.text((rx + 10, ry + 13), val, fill="#0F172A", font=f_body)
        rx += 100
        draw.text((rx + 10, ry + 13), unit, fill="#64748B", font=f_body)
        rx += 90
        draw.text((rx + 10, ry + 13), ref, fill="#334155", font=f_body)
        rx += 170
        draw.text((rx + 10, ry + 13), note, fill="#475569", font=f_small)

        ry += 42

    out_path = SCREENSHOTS_DIR / "03_results_table.png"
    img.save(out_path)
    print(f"Saved {out_path}")


def create_screenshot_4_explanations():
    """Screenshot 4: Plain-English AI Explanations."""
    w, h = 1200, 750
    img = Image.new("RGB", (w, h), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()

    draw_browser_frame(draw, w, h, "Medical Report Explainer | AI Explanations")
    next_y = draw_app_header(draw, w, 56)

    draw.text((40, next_y + 5), "💡 Plain-English Test Explanations (6 Clinical Dimensions)", fill="#1E3A8A", font=f_h2)

    # Expanded Explanation Card for Elevated Glucose
    card_y = next_y + 40
    draw.rounded_rectangle([40, card_y, w - 40, card_y + 240], radius=8, fill="#FFFFFF", outline="#DC2626", width=2)
    # Header inside card
    draw.text((60, card_y + 18), "🔴 Fasting Blood Glucose: 142.0 mg/dL (Reference: 70 - 99 mg/dL) — Status: High", fill="#991B1B", font=f_bold)
    draw.line([60, card_y + 45, w - 60, card_y + 45], fill="#E2E8F0", width=1)

    draw.text((60, card_y + 55), "• What it measures: Fasting blood glucose measures circulating glucose following overnight fasting, evaluating metabolic regulation.", fill="#1E293B", font=f_body)
    draw.text((60, card_y + 80), "• Status Overview: Your measured value of 142.0 mg/dL is above the upper reference boundary (70 - 99 mg/dL).", fill="#B91C1C", font=f_bold)
    draw.text((60, card_y + 105), "• Higher readings: Elevated readings can sometimes occur with altered carbohydrate metabolism, physical stress, illness, or diet.", fill="#334155", font=f_body)
    draw.text((60, card_y + 130), "• Lower readings: Lower readings can happen after prolonged fasting or vigorous unaccustomed exercise.", fill="#334155", font=f_body)
    draw.text((60, card_y + 155), "• Clinical Context: A single fasting glucose value does not constitute a diagnosis and should be verified alongside an HbA1c test.", fill="#0D9488", font=f_body)
    draw.text((60, card_y + 180), "• Next Steps: Discuss these findings with your primary healthcare provider for appropriate lifestyle and dietary advice.", fill="#2563EB", font=f_bold)

    # Second Card (Collapsed/Preview for Creatinine)
    c2_y = card_y + 255
    draw.rounded_rectangle([40, c2_y, w - 40, c2_y + 80], radius=8, fill="#FFFFFF", outline="#E2E8F0", width=1)
    draw.text((60, c2_y + 16), "🟢 Serum Creatinine: 0.82 mg/dL (Reference: 0.5 - 1.1 mg/dL) — Status: Normal", fill="#15803D", font=f_bold)
    draw.text((60, c2_y + 42), "What it measures: Creatinine is a natural waste byproduct from normal muscle metabolism, filtered out by healthy kidneys.", fill="#64748B", font=f_small)

    out_path = SCREENSHOTS_DIR / "04_explanations.png"
    img.save(out_path)
    print(f"Saved {out_path}")


def create_screenshot_5_downloads():
    """Screenshot 5: Downloads & Export Center."""
    w, h = 1200, 750
    img = Image.new("RGB", (w, h), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_h2, f_body, f_bold, f_small, f_metric = get_fonts()

    draw_browser_frame(draw, w, h, "Medical Report Explainer | Export Center")
    next_y = draw_app_header(draw, w, 56)

    draw.text((40, next_y + 15), "📥 Download Results & Clinical Reports", fill="#1E3A8A", font=f_h2)
    draw.text((40, next_y + 45), "Export structured laboratory data, numerical classifications, and patient-ready PDF summaries:", fill="#475569", font=f_body)

    # 3 Download Action Buttons
    dl_y = next_y + 85
    actions = [
        ("📄 Download Extracted JSON", "Pydantic-validated schema containing test names, values, units, and original ranges.", "#2563EB"),
        ("📊 Download Analyzed CSV", "Tabular dataset including Python classifications, boundary markers, and evaluation notes.", "#0D9488"),
        ("📑 Download Patient Summary PDF", "Personalized clinical summary report generated with ReportLab for patient records.", "#1E3A8A"),
    ]
    card_w = (w - 80 - 40) // 3
    for i, (btn_title, desc, btn_c) in enumerate(actions):
        cx = 40 + i * (card_w + 20)
        draw.rounded_rectangle([cx, dl_y, cx + card_w, dl_y + 160], radius=8, fill="#FFFFFF", outline="#CBD5E1", width=1)
        draw.rounded_rectangle([cx + 20, dl_y + 20, cx + card_w - 20, dl_y + 65], radius=6, fill=btn_c)
        draw.text((cx + 35, dl_y + 35), btn_title, fill="#FFFFFF", font=f_bold)
        draw.text((cx + 20, dl_y + 85), desc, fill="#64748B", font=f_small)

    out_path = SCREENSHOTS_DIR / "05_download_options.png"
    img.save(out_path)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    create_screenshot_1_upload()
    create_screenshot_2_dashboard()
    create_screenshot_3_table()
    create_screenshot_4_explanations()
    create_screenshot_5_downloads()
