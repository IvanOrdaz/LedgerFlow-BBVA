import pdfplumber
import re

def clean_amount(val):
    if not val:
        return 0.0
    cleaned = re.sub(r'[^\d\.\-]', '', str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

# ── X-position column boundaries (px) – BBVA Libreton NOMINA layout ─────────
CARGO_MIN_X  = 370;  CARGO_MAX_X  = 415
ABONO_MIN_X  = 415;  ABONO_MAX_X  = 462
SALDO_OP_MIN = 462;  SALDO_OP_MAX = 548
DESC_MAX_X   = 318

_FOOTER_KW = (
    'PAGINA', 'BBVA MEXICO', 'Av. Paseo de la Reforma',
    'Total de Mov', 'TOTAL IMPORTE', 'Saldo Global',
    'Estado de Cuenta de Apartados', 'La GAT Real',
    'Le informamos',
)
# Regex for tokens that are clearly technical codes (not human text)
_TECH_TOKEN = re.compile(
    r'^(\d|MBAN|BBAN)',          # starts with digit or known bank code prefix
    re.IGNORECASE
)

def _is_noise_line(text):
    """Return True if a continuation line is purely technical noise."""
    if not text:
        return True
    first_char = text[0]
    if first_char.isdigit():
        return True                           # starts with digit
    tokens = text.split()
    if tokens and _TECH_TOKEN.match(tokens[0]):
        return True                           # starts with MBAN / BBAN etc.
    # Skip if every token is all-alphanumeric with no spaces inside and long
    if all(re.match(r'^[A-Z0-9]{8,}$', t) for t in tokens):
        return True
    return False

def parse_debit_pdf(pdf_path):
    data_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            if not words:
                continue
            words.sort(key=lambda w: (w['top'], w['x0']))

            # ── Group into visual lines ───────────────────────────────────
            lines = []
            cur_top, cur_line = words[0]['top'], []
            for w in words:
                if abs(w['top'] - cur_top) <= 5:
                    cur_line.append(w)
                else:
                    lines.append(sorted(cur_line, key=lambda x: x['x0']))
                    cur_top, cur_line = w['top'], [w]
            if cur_line:
                lines.append(sorted(cur_line, key=lambda x: x['x0']))

            i = 0
            while i < len(lines):
                lw   = lines[i]
                ltxt = ' '.join(w['text'] for w in lw)

                if not re.match(r'^\d{2}/[A-Z]{3}', ltxt.strip()):
                    i += 1
                    continue

                # ── Dates ─────────────────────────────────────────────────
                dt = [w for w in lw if re.match(r'^\d{2}/[A-Z]{3}$', w['text'])]
                if not dt:
                    i += 1
                    continue
                date_oper = dt[0]['text']
                date_liq  = dt[1]['text'] if len(dt) >= 2 else date_oper

                # ── Amounts by x-column on the date line ──────────────────
                cargo = abono = saldo = 0.0
                for w in lw:
                    t = w['text']
                    if not re.search(r'\d+[,\d]*\.\d{2}', t):
                        continue
                    v, x = clean_amount(t), w['x0']
                    if v <= 0:
                        continue
                    if   CARGO_MIN_X  <= x < CARGO_MAX_X:  cargo = v
                    elif ABONO_MIN_X  <= x < ABONO_MAX_X:  abono = v
                    elif SALDO_OP_MIN <= x < SALDO_OP_MAX: saldo = v

                # ── Description from left portion of date line ────────────
                desc_parts = [
                    w['text'] for w in lw
                    if w['x0'] < DESC_MAX_X
                    and not re.match(r'^\d{2}/[A-Z]{3}$', w['text'])
                ]
                description = ' '.join(desc_parts).strip()

                # ── Continuation lines: only clean human-readable text ─────
                j = i + 1
                while j < len(lines):
                    nw  = lines[j]
                    nt  = ' '.join(w['text'] for w in nw).strip()

                    if re.match(r'^\d{2}/[A-Z]{3}', nt): break
                    if any(kw in nt for kw in _FOOTER_KW):  break

                    left = [w for w in nw if w['x0'] < DESC_MAX_X]
                    if left:
                        ct = ' '.join(w['text'] for w in left).strip()
                        if not _is_noise_line(ct):
                            description += ' ' + ct
                    j += 1

                i = j - 1
                description = re.sub(r'\s+', ' ', description).strip()

                if not description or 'total' in description.lower():
                    i += 1
                    continue

                data_rows.append({
                    "Fecha Operación":        date_oper,
                    "Fecha Liquidación":      date_liq,
                    "Descripción / Concepto": description,
                    "Cargo (Retiro -)":       cargo,
                    "Abono (Depósito +)":     abono,
                    "Saldo Resultante":       saldo,
                })
                i += 1

    return data_rows
