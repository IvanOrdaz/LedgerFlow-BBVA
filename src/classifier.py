import pdfplumber
import re

MESES_ES = {
    'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
}

def get_clean_lines(page):
    """Agrupa palabras del PDF que comparten la misma altura visual (líneas reales)"""
    words = page.extract_words()
    if not words:
        return []
    words.sort(key=lambda w: (w['top'], w['x0']))
    lines = []
    current_top = words[0]['top']
    current_line = []
    tolerance = 5 # margen en pixeles para textos en la misma fila
    
    for w in words:
        if abs(w['top'] - current_top) <= tolerance:
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
        
        doc_type = None
        if "TARJETA" in full_text.upper() or "PAGO PARA NO GENERAR INTERESES" in full_text.upper():
            doc_type = "CREDIT"
        elif "LIBRETON" in full_text.upper() or "SALDO PROMEDIO" in full_text.upper():
            doc_type = "DEBIT"
        else:
            return None, None

        period_str = None
        # Buscar la fecha contable asociada directamente a la línea de 'Corte'
        for line in first_page_lines:
            line_lower = line.lower()
            if "corte" in line_lower:
                if doc_type == "CREDIT":
                    match = re.search(r'(\d{1,2})-([a-z]{3})-(\d{4})', line_lower)
                    if match:
                        day, month_name, year = match.groups()
                        period_str = f"{year}-{MESES_ES.get(month_name[:3], '12')}"
                        break
                elif doc_type == "DEBIT":
                    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', line_lower)
                    if match:
                        day, month, year = match.groups()
                        period_str = f"{year}-{month}"
                        break
                        
        # Respaldo de seguridad si las columnas desalinearon la palabra 'corte'
        if not period_str:
            if doc_type == "CREDIT":
                matches = re.findall(r'(\d{1,2})-([a-z]{3})-(\d{4})', full_text.lower())
                if matches:
                    day, month_name, year = matches[-1]
                    period_str = f"{year}-{MESES_ES.get(month_name[:3], '12')}"
            else:
                matches = re.findall(r'(\d{2})/(\d{2})/(\d{4})', full_text.lower())
                if matches:
                    day, month, year = matches[-1]
                    period_str = f"{year}-{month}"
                    
        return doc_type, period_str or "9999-12"