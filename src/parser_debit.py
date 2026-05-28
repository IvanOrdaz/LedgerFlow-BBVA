import pdfplumber
import re
import pandas as pd
from classifier import get_clean_lines

def clean_amount(val):
    if pd.isna(val) or not val:
        return 0.0
    cleaned = re.sub(r'[^\d\.\-]', '', str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def parse_debit_pdf(pdf_path):
    data_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = get_clean_lines(page)
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if re.match(r'^\d{2}/[A-Z]{3}', line):
                    parts = line.split()
                    date_oper = parts[0]
                    date_liq = parts[1] if len(parts) > 1 and re.match(r'^\d{2}/[A-Z]{3}', parts[1]) else date_oper
                    
                    start_idx = 2 if date_liq != date_oper else 1
                    block_tokens = parts[start_idx:]
                    
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        if re.match(r'^\d{2}/[A-Z]{3}', next_line) or "página" in next_line.lower() or "saldo global" in next_line.lower():
                            break
                        block_tokens.extend(next_line.split())
                        j += 1
                        
                    i = j - 1
                    
                    num_tokens = [t for t in block_tokens if re.search(r'\d+\.\d{2}', t)]
                    cargo = 0.0
                    abono = 0.0
                    saldo = 0.0
                    
                    if len(num_tokens) >= 2:
                        amount_val = clean_amount(num_tokens[-2])
                        saldo = clean_amount(num_tokens[-1])
                        desc_tokens = [t for t in block_tokens if t not in num_tokens[-2:]]
                        description = " ".join(desc_tokens)
                        
                        if any(k in description.upper() for k in ["PAGO DE NOMINA", "AGUINALDO", "DEPOSITO", "RECIBIDO", "ABONO", "INTERESES"]):
                            abono = amount_val
                        else:
                            cargo = amount_val
                    elif len(num_tokens) == 1:
                        amount_val = clean_amount(num_tokens[0])
                        desc_tokens = [t for t in block_tokens if t != num_tokens[0]]
                        description = " ".join(desc_tokens)
                        if any(k in description.upper() for k in ["PAGO DE NOMINA", "AGUINALDO", "DEPOSITO", "RECIBIDO", "ABONO", "INTERESES"]):
                            abono = amount_val
                        else:
                            cargo = amount_val
                    else:
                        description = " ".join(block_tokens)
                        
                    if "total" in description.lower() or not description.strip():
                        i += 1
                        continue
                        
                    data_rows.append({
                        "Fecha Operación": date_oper,
                        "Fecha Liquidación": date_liq,
                        "Descripción / Concepto": description.strip(),
                        "Cargo (Retiro -)": cargo,
                        "Abono (Depósito +)": abono,
                        "Saldo Resultante": saldo
                    })
                i += 1
    return data_rows