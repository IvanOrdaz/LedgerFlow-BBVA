import pdfplumber
import re

MESES_ES = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
}

def get_clean_lines(page):
    """Agrupa palabras del PDF que comparten la misma altura visual (líneas reales)."""
    words = page.extract_words()
    if not words:
        return []
    words.sort(key=lambda w: (w['top'], w['x0']))
    lines = []
    current_top = words[0]['top']
    current_line = []
    for w in words:
        if abs(w['top'] - current_top) <= 5:
            current_line.append(w)
        else:
            current_line.sort(key=lambda x: x['x0'])
            lines.append(" ".join([x['text'] for x in current_line]))
            current_top = w['top']
            current_line = [w]
    if current_line:
        current_line.sort(key=lambda x: x['x0'])
        lines.append(" ".join([x['text'] for x in current_line]))
    return lines

def analyze_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return None, None

        first_page_lines = get_clean_lines(pdf.pages[0])
        full_text = "\n".join(first_page_lines)

        # ── Classify doc type ─────────────────────────────────────────
        doc_type = None
        fu = full_text.upper()
        if "TARJETA" in fu or "PAGO PARA NO GENERAR INTERESES" in fu or "TARJETA ORO" in fu:
            doc_type = "CREDIT"
        elif "LIBRETON" in fu or "SALDO PROMEDIO" in fu:
            doc_type = "DEBIT"
        else:
            return None, None

        # ── Extract period ─────────────────────────────────────────────
        period_str = None

        for line in first_page_lines:
            ll = line.lower()
            if "corte" in ll:
                if doc_type == "CREDIT":
                    m = re.search(r'(\d{1,2})-([a-z]{3})-(\d{4})', ll)
                    if m:
                        period_str = f"{m.group(3)}-{MESES_ES.get(m.group(2)[:3], '12')}"
                        break
                elif doc_type == "DEBIT":
                    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', ll)
                    if m:
                        period_str = f"{m.group(3)}-{m.group(2)}"
                        break

        # Fallback: scan full text
        if not period_str:
            if doc_type == "CREDIT":
                matches = re.findall(r'(\d{1,2})-([a-z]{3})-(\d{4})', full_text.lower())
                if matches:
                    d, mn, y = matches[-1]
                    period_str = f"{y}-{MESES_ES.get(mn[:3], '12')}"
            else:
                matches = re.findall(r'(\d{2})/(\d{2})/(\d{4})', full_text.lower())
                if matches:
                    d, m, y = matches[-1]
                    period_str = f"{y}-{m}"

        return doc_type, period_str or "9999-12"
