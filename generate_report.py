"""
CivicAgent PK — Official Complaint Resolution Report Generator
================================================================

Converts a processed AI response (complaint classification + auto-generated
official reply) into a clean, professional, downloadable PDF report for
Pakistani municipal/government officers.

Features
--------
- Bilingual support: English (LTR) and Urdu (RTL) in the same document,
  using arabic_reshaper + python-bidi to correctly shape and reorder
  Urdu text so it renders right-to-left instead of as disconnected/
  reversed glyphs. Note: ReportLab has no OpenType shaping engine, so
  the Urdu font must ship pre-composed "Arabic Presentation Form"
  glyphs (Amiri does; most Nastaliq fonts, incl. Noto Nastaliq Urdu,
  rely on OpenType substitution instead and will render as blank/
  broken text here) — this script uses Amiri for that reason.
- Official letterhead layout with reference number, dates, and status.
- Structured "AI Classification" block: matched department, rule/section,
  and confidence score.
- Official reply rendered in both languages.
- Numbered footer with generation timestamp + AI-assistance disclaimer,
  as required for any AI-generated content going to a government office.

Dependencies
------------
    pip install reportlab arabic-reshaper python-bidi

Fonts (must ship alongside this script in a ./fonts folder, or pass
custom paths to CivicComplaintPDFGenerator):
    - NotoSans-Regular.ttf   (English body text)
    - NotoSans-Bold.ttf      (English headings)
    - Amiri-Regular.ttf      (Urdu/Arabic-script text)
  All are free/open fonts: Noto Sans (SIL OFL, Google Noto Project,
  https://fonts.google.com/noto) and Amiri (SIL OFL,
  https://www.amirifont.org/).

Usage
-----
    python generate_report.py

  or import it:

    from generate_report import ComplaintRecord, CivicComplaintPDFGenerator

    record = ComplaintRecord(...)
    CivicComplaintPDFGenerator().generate(record, "output.pdf")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _URDU_SHAPING_AVAILABLE = True
except ImportError:
    _URDU_SHAPING_AVAILABLE = False


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class ComplaintRecord:
    """Holds one complaint's data as handed off by the CivicAgent PK
    NLP/classification pipeline, ready for report rendering."""

    reference_no: str
    date_submitted: str                  # e.g. "2026-09-10"
    date_processed: str                  # e.g. "2026-09-12"
    citizen_name: str
    citizen_contact: str
    submission_channel: str              # e.g. "WhatsApp Bot", "Web Portal"
    detected_language: str               # "Urdu" | "English" | "Mixed"

    complaint_text_en: str
    complaint_text_ur: str = ""          # optional, leave blank if not available

    matched_department: str = ""         # e.g. "Water & Sanitation Agency (WASA)"
    matched_rule_reference: str = ""     # e.g. "Local Govt Act 2013, Sec. 96(2)"
    ai_category: str = ""                # e.g. "Sewerage Blockage"
    ai_priority: str = ""                # "High" | "Medium" | "Low"
    ai_confidence: Optional[float] = None  # 0-1

    official_reply_en: str = ""
    official_reply_ur: str = ""

    assigned_officer: str = ""
    resolution_deadline: str = ""
    status: str = "Forwarded to Department"


# --------------------------------------------------------------------------
# Footer / page-numbering canvas
# --------------------------------------------------------------------------

class _NumberedCanvas(canvas.Canvas):
    """Adds 'Page X of Y' plus a standing AI-disclaimer footer on every page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total_pages)
            super().showPage()
        super().save()

    def _draw_footer(self, total_pages):
        import textwrap

        width, _ = A4
        left_x, right_x = 20 * mm, width - 20 * mm
        usable_width = right_x - left_x

        self.setStrokeColor(colors.HexColor("#01411C"))
        self.setLineWidth(0.6)
        self.line(left_x, 20 * mm, right_x, 20 * mm)

        # Row 1: generation timestamp (left) + page count (right) — kept on
        # their own row, well clear of the disclaimer, so they never overlap.
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawString(
            left_x, 15.5 * mm,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} PKT",
        )
        self.drawRightString(
            right_x, 15.5 * mm, f"Page {self._pageNumber} of {total_pages}",
        )

        # Row 2: AI-disclaimer, word-wrapped to the usable width so it never
        # runs into the margin or collides with other footer text.
        self.setFont("Helvetica", 7.5)
        disclaimer = (
            "This report was generated by CivicAgent PK, an AI-assisted "
            "complaint processing system. The auto-drafted reply must be "
            "reviewed and countersigned by an authorized officer before "
            "being issued to the citizen."
        )
        chars_per_line = max(20, int(usable_width / (pdfmetrics.stringWidth("x", "Helvetica", 7.5))))
        wrapped = textwrap.wrap(disclaimer, width=chars_per_line)
        y = 11.5 * mm
        for line in wrapped:
            self.drawString(left_x, y, line)
            y -= 3.6 * mm


# --------------------------------------------------------------------------
# PDF generator
# --------------------------------------------------------------------------

class CivicComplaintPDFGenerator:
    """Builds a single professional PDF report from a ComplaintRecord."""

    BRAND_GREEN = colors.HexColor("#01411C")
    LIGHT_GREEN = colors.HexColor("#E9F3EC")
    GREY_TEXT = colors.HexColor("#333333")

    def __init__(
        self,
        font_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
        department_name: str = "Government of Pakistan — Municipal Services",
        system_name: str = "CivicAgent PK",
    ):
        self.font_dir = font_dir
        self.department_name = department_name
        self.system_name = system_name
        self._urdu_font_ok = self._register_fonts()
        self.styles = self._build_styles()

    # -- setup -------------------------------------------------------

    def _register_fonts(self) -> bool:
        """Registers NotoSans (English) and NotoNastaliqUrdu (Urdu).
        Returns True if Urdu rendering is fully available."""
        try:
            pdfmetrics.registerFont(
                TTFont("NotoSans", os.path.join(self.font_dir, "NotoSans-Regular.ttf"))
            )
            pdfmetrics.registerFont(
                TTFont("NotoSans-Bold", os.path.join(self.font_dir, "NotoSans-Bold.ttf"))
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not load NotoSans fonts required for report text. "
                f"Expected them in: {self.font_dir}. Original error: {exc}"
            )

        try:
            pdfmetrics.registerFont(
                TTFont("UrduText", os.path.join(self.font_dir, "Amiri-Regular.ttf"))
            )
            return _URDU_SHAPING_AVAILABLE
        except Exception:
            # English-only fallback: report still generates, Urdu sections
            # are simply skipped rather than rendered incorrectly.
            return False

    def _build_styles(self):
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name="ReportTitle", fontName="NotoSans-Bold", fontSize=15,
            textColor=self.BRAND_GREEN, spaceAfter=2, alignment=TA_LEFT,
        ))
        styles.add(ParagraphStyle(
            name="ReportSubtitle", fontName="NotoSans", fontSize=9.5,
            textColor=self.GREY_TEXT, spaceAfter=6,
        ))
        styles.add(ParagraphStyle(
            name="SectionHeading", fontName="NotoSans-Bold", fontSize=11,
            textColor=colors.white, backColor=self.BRAND_GREEN,
            spaceBefore=12, spaceAfter=6, leftIndent=6, borderPadding=4,
        ))
        styles.add(ParagraphStyle(
            name="BodyEN", fontName="NotoSans", fontSize=10, leading=15,
            textColor=self.GREY_TEXT, alignment=TA_LEFT, spaceAfter=6,
        ))
        styles.add(ParagraphStyle(
            name="BodyUR", fontName="UrduText", fontSize=12.5, leading=22,
            textColor=self.GREY_TEXT, alignment=TA_RIGHT, spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name="LabelSmall", fontName="NotoSans-Bold", fontSize=8.5,
            textColor=self.BRAND_GREEN,
        ))
        styles.add(ParagraphStyle(
            name="LabelUrdu", fontName="UrduText", fontSize=10,
            textColor=self.BRAND_GREEN, alignment=TA_RIGHT,
        ))
        styles.add(ParagraphStyle(
            name="ValueSmall", fontName="NotoSans", fontSize=9.5,
            textColor=self.GREY_TEXT,
        ))
        return styles

    @staticmethod
    def _shape_urdu(text: str) -> str:
        """Reshapes+reorders a short single-line Urdu string (e.g. a label).
        Not safe for multi-line body text — see _shape_urdu_paragraph."""
        if not text or not _URDU_SHAPING_AVAILABLE:
            return text
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)

    @staticmethod
    def _shape_urdu_paragraph(text: str, font_name: str, font_size: float, max_width: float) -> str:
        """Reshapes and line-wraps a longer Urdu passage for correct
        multi-line rendering.

        python-bidi's get_display() only produces a correct result for
        one visual line at a time. Reordering the *whole* paragraph
        first and then letting ReportLab's Paragraph auto-wrap it (which
        wraps left-to-right on the already-reordered string) silently
        flips the order of the wrapped lines. To avoid that, this method
        wraps the text itself — measuring the reshaped (still
        logical-order) string against max_width — and only then
        bidi-reorders each finished line individually, joining the
        result with explicit <br/> tags.
        """
        if not text or not _URDU_SHAPING_AVAILABLE:
            return text

        reshaped = arabic_reshaper.reshape(text)
        words = reshaped.split(" ")
        lines, current = [], ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        visual_lines = [get_display(line) for line in lines]
        return "<br/>".join(visual_lines)

    # -- layout helpers ------------------------------------------------

    def _letterhead(self, record: ComplaintRecord) -> list:
        flow = [
            Paragraph(self.department_name, self.styles["ReportTitle"]),
            Paragraph(
                f"Automated Complaint Resolution Report &nbsp;|&nbsp; "
                f"Generated by {self.system_name}",
                self.styles["ReportSubtitle"],
            ),
            HRFlowable(width="100%", thickness=1.2, color=self.BRAND_GREEN, spaceAfter=10),
        ]
        return flow

    def _meta_table(self, record: ComplaintRecord) -> Table:
        def cell(label, value):
            return [
                Paragraph(label, self.styles["LabelSmall"]),
                Paragraph(value or "—", self.styles["ValueSmall"]),
            ]

        rows_data = [
            ("Reference No.", record.reference_no, "Status", record.status),
            ("Date Submitted", record.date_submitted, "Date Processed", record.date_processed),
            ("Citizen", record.citizen_name, "Contact", record.citizen_contact),
            ("Channel", record.submission_channel, "Language Detected", record.detected_language),
        ]

        table_data = []
        for l1, v1, l2, v2 in rows_data:
            r1 = cell(l1, v1)
            r2 = cell(l2, v2)
            table_data.append([r1[0], r1[1], r2[0], r2[1]])

        t = Table(table_data, colWidths=[32 * mm, 55 * mm, 32 * mm, 51 * mm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), self.LIGHT_GREEN),
            ("BOX", (0, 0), (-1, -1), 0.5, self.BRAND_GREEN),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    def _classification_table(self, record: ComplaintRecord) -> Table:
        confidence = (
            f"{record.ai_confidence * 100:.1f}%"
            if record.ai_confidence is not None else "—"
        )
        data = [
            [Paragraph("Matched Department", self.styles["LabelSmall"]),
             Paragraph("AI Category", self.styles["LabelSmall"]),
             Paragraph("Priority", self.styles["LabelSmall"]),
             Paragraph("Confidence", self.styles["LabelSmall"])],
            [Paragraph(record.matched_department or "—", self.styles["ValueSmall"]),
             Paragraph(record.ai_category or "—", self.styles["ValueSmall"]),
             Paragraph(record.ai_priority or "—", self.styles["ValueSmall"]),
             Paragraph(confidence, self.styles["ValueSmall"])],
        ]
        t = Table(data, colWidths=[52.5 * mm, 45 * mm, 25 * mm, 27.5 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEE1")),
            ("BOX", (0, 0), (-1, -1), 0.5, self.BRAND_GREEN),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    # -- main entry point ------------------------------------------------

    def generate(self, record: ComplaintRecord, output_path: str) -> str:
        """Builds the PDF and writes it to output_path. Returns output_path."""

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=12 * mm, bottomMargin=24 * mm,
            leftMargin=20 * mm, rightMargin=20 * mm,
            title=f"CivicAgent PK Report {record.reference_no}",
            author=self.system_name,
        )

        story = []
        story += self._letterhead(record)

        story.append(Paragraph("COMPLAINT SUMMARY", self.styles["SectionHeading"]))
        story.append(self._meta_table(record))
        story.append(Spacer(1, 6))

        story.append(Paragraph("AI CLASSIFICATION &amp; RULE MATCH", self.styles["SectionHeading"]))
        story.append(self._classification_table(record))
        if record.matched_rule_reference:
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                f"<b>Applicable Rule / Regulation:</b> {record.matched_rule_reference}",
                self.styles["BodyEN"],
            ))
        story.append(Spacer(1, 4))

        story.append(Paragraph("ORIGINAL COMPLAINT", self.styles["SectionHeading"]))
        if record.complaint_text_en:
            story.append(Paragraph("English", self.styles["LabelSmall"]))
            story.append(Paragraph(record.complaint_text_en, self.styles["BodyEN"]))
        if record.complaint_text_ur and self._urdu_font_ok:
            story.append(Paragraph("اردو", self.styles["LabelUrdu"]))
            wrapped = self._shape_urdu_paragraph(
                record.complaint_text_ur, "UrduText",
                self.styles["BodyUR"].fontSize, doc.width - 14,
            )
            story.append(Paragraph(wrapped, self.styles["BodyUR"]))
        story.append(Spacer(1, 4))

        story.append(Paragraph("OFFICIAL AI-DRAFTED REPLY", self.styles["SectionHeading"]))
        if record.official_reply_en:
            story.append(Paragraph("English", self.styles["LabelSmall"]))
            story.append(Paragraph(record.official_reply_en, self.styles["BodyEN"]))
        if record.official_reply_ur and self._urdu_font_ok:
            story.append(Paragraph("اردو", self.styles["LabelUrdu"]))
            wrapped = self._shape_urdu_paragraph(
                record.official_reply_ur, "UrduText",
                self.styles["BodyUR"].fontSize, doc.width - 14,
            )
            story.append(Paragraph(wrapped, self.styles["BodyUR"]))
        story.append(Spacer(1, 6))

        story.append(Paragraph("ACTION &amp; FOLLOW-UP", self.styles["SectionHeading"]))
        followup = Table([
            [Paragraph("Assigned Officer", self.styles["LabelSmall"]),
             Paragraph(record.assigned_officer or "Pending assignment", self.styles["ValueSmall"])],
            [Paragraph("Resolution Deadline", self.styles["LabelSmall"]),
             Paragraph(record.resolution_deadline or "—", self.styles["ValueSmall"])],
        ], colWidths=[45 * mm, 110 * mm])
        followup.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, self.BRAND_GREEN),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.white),
            ("BACKGROUND", (0, 0), (-1, -1), self.LIGHT_GREEN),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(followup)
        story.append(Spacer(1, 6))

        story.append(Paragraph(
            "_____________________________<br/>Authorized Officer Signature &amp; Stamp",
            self.styles["BodyEN"],
        ))

        doc.build(story, canvasmaker=_NumberedCanvas)
        return output_path


# --------------------------------------------------------------------------
# Demo / manual run
# --------------------------------------------------------------------------

if __name__ == "__main__":
    sample = ComplaintRecord(
        reference_no="CAK-2026-004471",
        date_submitted="2026-09-10",
        date_processed="2026-09-12",
        citizen_name="Ali Raza (sample)",
        citizen_contact="+92-3XX-XXXXXXX",
        submission_channel="WhatsApp Bot",
        detected_language="Mixed (Urdu + English)",
        complaint_text_en=(
            "There has been an open sewerage leak on Street 14, Gulshan-e-Iqbal "
            "Block 6 for the past five days. It is causing a health hazard for "
            "nearby residents, especially children."
        ),
        complaint_text_ur=(
            "گزشتہ پانچ دنوں سے گلشن اقبال بلاک چھ، گلی نمبر چودہ میں سیوریج کا پانی "
            "کھلا بہہ رہا ہے۔ یہ قریبی رہائشیوں، خاص طور پر بچوں کے لیے صحت کا خطرہ بن رہا ہے۔"
        ),
        matched_department="Water & Sanitation Agency (WASA) — Karachi",
        matched_rule_reference="Sindh Local Government Act 2013, Sec. 96(2)(f) — Sanitation & Public Health",
        ai_category="Sewerage Blockage / Leak",
        ai_priority="High",
        ai_confidence=0.94,
        official_reply_en=(
            "Dear Resident, your complaint has been received and verified. It has "
            "been forwarded to WASA Karachi under the applicable public health "
            "regulation. A field team is expected to inspect the site within 3 "
            "working days. You will be notified upon resolution."
        ),
        official_reply_ur=(
            "معزز شہری، آپ کی شکایت موصول اور تصدیق ہو چکی ہے۔ اسے متعلقہ ادارے واسا کراچی "
            "کو صحت عامہ کے ضوابط کے تحت بھجوا دیا گیا ہے۔ متعلقہ ٹیم تین کاروباری دنوں "
            "میں جائے وقوعہ کا معائنہ کرے گی۔ حل ہونے پر آپ کو مطلع کیا جائے گا۔"
        ),
        assigned_officer="Executive Engineer, WASA Zone-III",
        resolution_deadline="2026-09-15",
        status="Forwarded to Department",
    )

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sample_complaint_report.pdf"
    )
    generator = CivicComplaintPDFGenerator()
    generator.generate(sample, out_path)
    print(f"Report generated: {out_path}")
