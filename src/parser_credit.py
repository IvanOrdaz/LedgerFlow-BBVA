import pdfplumber
import re
from classifier import get_clean_lines

def clean_amount(val):
    if not val:
        return 0.0
    cleaned = re.sub(r'[^\d\.\-]', '', str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

# Línea de cargo/abono: termina con +/- $X,XXX.XX
_AMOUNT_RE  = re.compile(r'([\+\-])\s*\$?([\d,]+\.\d{2})\s*$')
_DATE_RE    = re.compile(r'^\d{1,2}-[a-zA-Z]{3}-\d{4}$')
_DIGITAL    = re.compile(r'\s*;\s*Tarjeta Digital\s+\*+\d+\s*', re.IGNORECASE)
_NOISE_LINE = re.compile(
    r'^(IVA\s*:|MXP\s+\$|Capital\s+de\s+promoci|Pago\s+excedente)',
    re.IGNORECASE
)

def parse_credit_pdf(pdf_path):
    data_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = get_clean_lines(page)

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Solo procesar líneas que empiecen con fecha (dd-mes-yyyy)
                if not re.match(r'^\d{1,2}-[a-zA-Z]{3}-\d{4}', line):
                    i += 1
                    continue

                # Debe terminar en +/- $monto para ser transacción regular
                m = _AMOUNT_RE.search(line)
                if not m:
                    i += 1
                    continue

                sign       = m.group(1)
                amount_val = clean_amount(m.group(2))
                cargo = amount_val if sign == '+' else 0.0
                abono = amount_val if sign == '-' else 0.0

                # ── Extraer fecha de operación (primer token) ─────────────
                tokens_raw = line[:m.start()].split()
                fecha_op   = tokens_raw[0] if tokens_raw else ""

                # Quitar los tokens de fecha (op + cargo si hay dos fechas)
                desc_tokens = [t for t in tokens_raw if not _DATE_RE.match(t)]
                description = ' '.join(desc_tokens).strip()

                # Limpiar sufijo "Tarjeta Digital ***XXXX"
                description = _DIGITAL.sub('', description).strip().rstrip(';').strip()

                # Saltar líneas de resumen/pie (pago para no generar, etc.)
                if not description or re.search(r'pago para no', description, re.IGNORECASE):
                    i += 1
                    continue

                # Avanzar sobre líneas de detalle IVA/Capital que siguen
                j = i + 1
                while j < len(lines):
                    nl = lines[j].strip()
                    if not nl:
                        j += 1; continue
                    if re.match(r'^\d{1,2}-[a-zA-Z]{3}-\d{4}', nl): break
                    if any(kw in nl.lower() for kw in
                           ['página', 'total cargos', 'total abonos', 'número de cuenta',
                            'notas:', 'tarjeta titular']):
                        break
                    j += 1
                i = j - 1

                # ── Clasificación MSI ──────────────────────────────────────
                tipo = "Regular"
                if re.search(r'\b\d+\s+DE\s+\d+\b', description.upper()):
                    tipo = "Mensualidad MSI"
                elif re.search(r'\bA\s+\d+\s+MSI\b', description.upper()):
                    tipo = "Cargo MSI"

                data_rows.append({
                    "Fecha Operación":               fecha_op,
                    "Descripción / Establecimiento": description,
                    "Tipo de Cargo":                 tipo,
                    "Cargo (Compra +)":              cargo,
                    "Abono (Pago -)":                abono,
                })
                i += 1

    return data_rows
