"""
Utility script to generate synthetic test PDFs for the sample reports using PyMuPDF.
Includes valid digital text PDFs and edge case PDFs (scanned image, empty).
"""

import os
import pymupdf as fitz


def create_pdf_from_text(text_content: str, output_path: str, title: str = "Clinical Laboratory Report"):
    """Creates a formatted PDF report with selectable digital text."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size in points
    
    # Title / Header
    rect_header = fitz.Rect(50, 40, 545, 90)
    page.draw_rect(rect_header, color=(0.2, 0.4, 0.7), fill=(0.95, 0.97, 1.0))
    page.insert_text(fitz.Point(70, 70), title, fontsize=16, fontname="helv", color=(0.1, 0.2, 0.5))

    # Body text
    y = 110
    for line in text_content.splitlines():
        if y > 800:
            page = doc.new_page(width=595, height=842)
            y = 50
        page.insert_text(fitz.Point(50, y), line, fontsize=10, fontname="courier", color=(0.1, 0.1, 0.1))
        y += 14

    doc.save(output_path)
    doc.close()
    print(f"Generated PDF: {output_path}")


def create_scanned_image_pdf(output_path: str):
    """Creates a simulated scanned PDF that contains shapes with NO selectable digital text."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(50, 50, 545, 792)
    page.draw_rect(rect, color=(0.7, 0.7, 0.7), fill=(0.93, 0.93, 0.93))
    page.draw_line(fitz.Point(60, 100), fitz.Point(535, 100), color=(0.5, 0.5, 0.5))
    page.draw_line(fitz.Point(60, 200), fitz.Point(535, 200), color=(0.5, 0.5, 0.5))
    doc.save(output_path)
    doc.close()
    print(f"Generated Scanned Simulation PDF: {output_path}")


def create_empty_pdf(output_path: str):
    """Creates a 0-byte empty file."""
    with open(output_path, "wb") as f:
        f.write(b"")
    print(f"Generated Empty PDF: {output_path}")


if __name__ == "__main__":
    samples_dir = os.path.join(os.path.dirname(__file__), "sample_reports")
    os.makedirs(samples_dir, exist_ok=True)

    # Convert all 5 TXT samples to digital PDFs
    for filename in os.listdir(samples_dir):
        if filename.endswith(".txt"):
            txt_path = os.path.join(samples_dir, filename)
            pdf_path = os.path.join(samples_dir, filename.replace(".txt", ".pdf"))
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            title = filename.replace(".txt", "").replace("_", " ").title()
            create_pdf_from_text(content, pdf_path, title=title)

    # Edge cases
    create_scanned_image_pdf(os.path.join(samples_dir, "edge_case_scanned_image_only.pdf"))
    create_empty_pdf(os.path.join(samples_dir, "edge_case_empty_zero_pages.pdf"))
