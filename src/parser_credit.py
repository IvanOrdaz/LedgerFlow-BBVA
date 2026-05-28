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

def parse_credit_pdf(pdf_path):
    data_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = get_clean_lines(page)
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                # Detectar si la línea inicia con una fecha (ej: 22-ene-2025 o 2-dic-2024)
                if re.match(r'^\d{1,2}-[a-zA-Z]{3}-\d{4}', line):
                    parts = line.split()
                    date_op = parts[0]
                    
                    # Verificar si viene acompañado inmediatamente de la fecha de cargo
                    has_second_date = re.match(r'^\d{1,2}-[a-zA-Z]{3}-\d{4}', parts[1]) if len(parts) > 1 else False
                    start_desc_idx = 2 if has_second_date else 1
                    
                    monto_str = parts[-1]
                    desc_parts = parts[start_desc_idx:-1]
                    
                    # ACUMULADOR: Leer líneas siguientes si pertenecen al mismo movimiento (multilínea de BBVA)
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        # Si la siguiente línea ya es otra fecha u otra sección, detenemos la acumulación
                        if re.match(r'^\d{1,2}-[a-zA-Z]{3}-\d{4}', next_line) or "página" in next_line.lower() or "total" in next_line.lower():
                            break
                        
                        desc_parts.extend(next_line.split())
                        j += 1
                    
                    i = j - 1 # Adelantar el puntero principal
                    
                    # Combinar todos los tokens para aislar el monto real y la descripción limpia
                    final_tokens = line.split() + desc_parts
                    
                    # Buscar el último token que contenga el monto real del movimiento
                    amount_token = ""
                    for token in reversed(final_tokens):
                        if re.search(r'\d', token):
                            amount_token = token
                            break
                    
                    monto_num = clean_amount(amount_token)
                    if "-" in amount_token:
                        cargo = 0.0
                        abono = monto_num
                    else:
                        cargo = monto_num
                        abono = 0.0
                    
                    # Limpiar descripción eliminando fechas y montos
                    desc_tokens = [t for t in final_tokens if t != date_op and (not has_second_date or t != parts[1]) and t != amount_token]
                    description = " ".join(desc_tokens)
                    description = re.sub(r'^[+\-\s\$]+', '', description).strip()
                    
                    if "pago para no" in description.lower() or not description:
                        i += 1
                        continue
                    
                    # Clasificación inteligente de MSI
                    tipo_gasto = "Regular"
                    if re.search(r'\d+\s+DE\s+\d+', description.upper()) or "MSI" in description.upper():
                        tipo_gasto = "Mensualidad MSI"
                        
                    data_rows.append({
                        "Fecha": date_op,
                        "Descripción / Establecimiento": description,
                        "Tipo de Cargo": tipo_gasto,
                        "Cargo (Compra +)": cargo,
                        "Abono (Pago -)": abono
                    })
                i += 1
    return data_rows