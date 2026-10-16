from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


def build():
    root = Path(__file__).resolve().parents[1]
    source = root / "demo/demo-script.md"
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles["BodyText"].spaceAfter = 7
    styles["Code"].fontSize = 7
    styles["Code"].leading = 10
    styles["Code"].backColor = colors.HexColor("#F0F4F8")
    story = []
    code = None
    for line in source.read_text().splitlines():
        if line.startswith("```"):
            if code is None:
                code = []
            else:
                story.append(Preformatted("\n".join(code), styles["Code"], maxLineLength=94))
                story.append(Spacer(1, 8))
                code = None
        elif code is not None:
            code.append(line)
        elif line.strip():
            level = len(line) - len(line.lstrip("#"))
            style = styles.get(f"Heading{level}", styles["BodyText"]) if level else styles["BodyText"]
            value = line.lstrip("# ") if level else line
            story.append(Paragraph(escape(value), style))
    if code is not None:
        raise ValueError("Unclosed code block")

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#536879"))
        canvas.drawString(0.65 * inch, 0.4 * inch, "ResolveDesk | Presenter guide | 16 October 2026")
        canvas.drawRightString(7.65 * inch, 0.4 * inch, str(document.page))

    SimpleDocTemplate(
        str(root / "demo/demo-script.pdf"),
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.65 * inch,
        title="ResolveDesk - Exact demo script and actions",
        author="ResolveDesk",
    ).build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
