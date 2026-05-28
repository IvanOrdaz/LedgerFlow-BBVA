import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from classifier import analyze_pdf
from parser_debit import parse_debit_pdf
from parser_credit import parse_credit_pdf

class LedgerFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LedgerFlow BBVA v1.0")
        self.root.geometry("550x350")
        self.root.resizable(False, False)
        
        # Variables de control de rutas
        self.source_dir = tk.StringVar()
        
        # Diseño de la Interfaz Estilo Limpio
        style = ttk.Style()
        style.theme_use('clam')
        
        # Contenedor Principal
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="LedgerFlow BBVA", font=("Arial", 18, "bold"), foreground="#004481")
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Extractor Automático de Estados de Cuenta para Contabilidad", font=("Arial", 10, "italic"))
        subtitle_label.pack(pady=(0, 25))
        
        # Selector de carpeta
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=10)
        
        self.entry_dir = ttk.Entry(folder_frame, textvariable=self.source_dir, width=45)
        self.entry_dir.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        
        btn_browse = ttk.Button(folder_frame, text="Buscar Carpeta", command=self.browse_folder)
        btn_browse.pack(side=tk.RIGHT)
        
        # Barra de estado o progreso
        self.status_label = ttk.Label(main_frame, text="Estado: En espera de carpeta con PDFs...", font=("Arial", 9))
        self.status_label.pack(pady=15)
        
        # Botón gigante de Ejecución
        self.btn_process = ttk.Button(main_frame, text="⚡ PROCESAR Y GENERAR EXCEL", command=self.process_statements, state=tk.DISABLED)
        self.btn_process.pack(pady=10, ipady=5, fill=tk.X)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_dir.set(folder_selected)
            self.btn_process.config(state=tk.NORMAL)
            self.status_label.config(text=f"Estado: Carpeta cargada con éxito.")

    def process_statements(self):
        folder = self.source_dir.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "La carpeta seleccionada no existe.")
            return
            
        pdf_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            messagebox.showwarning("Sin archivos", "No se encontraron archivos PDF en la carpeta seleccionada.")
            return
            
        self.status_label.config(text="Procesando archivos... Por favor espera.")
        self.root.update_idletasks()
        
        # Estructuras de datos intermedias para agrupar por mes
        # llave: "YYYY-MM", valor: lista de filas extraídas
        debit_master = {}
        credit_master = {}
        
        processed_count = 0
        
        for pdf_path in pdf_files:
            doc_type, period = analyze_pdf(pdf_path)
            
            if doc_type == "DEBIT":
                rows = parse_debit_pdf(pdf_path)
                if rows:
                    if period not in debit_master:
                        debit_master[period] = []
                    debit_master[period].extend(rows)
                processed_count += 1
                
            elif doc_type == "CREDIT":
                rows = parse_credit_pdf(pdf_path)
                if rows:
                    if period not in credit_master:
                        credit_master[period] = []
                    credit_master[period].extend(rows)
                processed_count += 1
        
        if processed_count == 0:
            self.status_label.config(text="Estado: Finalizado con advertencias.")
            messagebox.showwarning("Advertencia", "Se leyeron los PDFs pero ninguno corresponde al formato de estados de cuenta de BBVA soportados.")
            return

        # --- GUARDAR ARCHIVO DE DÉBITO ---
        if debit_master:
            debit_out_path = os.path.join(folder, "LedgerFlow_Debito_Consolidado.xlsx")
            # Ordenamos las llaves cronológicamente (ej: '2024-12', '2025-01')
            sorted_months = sorted(debit_master.keys())
            
            with pd.ExcelWriter(debit_out_path, engine='openpyxl') as writer:
                for month in sorted_months:
                    df = pd.DataFrame(debit_master[month])
                    # Guardamos la hoja con el nombre del mes
                    df.to_excel(writer, sheet_name=month, index=False)
                    
        # --- GUARDAR ARCHIVO DE CRÉDITO ---
        if credit_master:
            credit_out_path = os.path.join(folder, "LedgerFlow_Credito_Consolidado.xlsx")
            sorted_months = sorted(credit_master.keys())
            
            with pd.ExcelWriter(credit_out_path, engine='openpyxl') as writer:
                for month in sorted_months:
                    df = pd.DataFrame(credit_master[month])
                    df.to_excel(writer, sheet_name=month, index=False)

        self.status_label.config(text=f"¡Éxito! Se procesaron {processed_count} archivos correctamente.")
        messagebox.showinfo("Proceso Terminado", f"Se han generado con éxito los siguientes archivos en la carpeta de origen:\n\n1. LedgerFlow_Debito_Consolidado.xlsx\n2. LedgerFlow_Credito_Consolidado.xlsx")

if __name__ == "__main__":
    root = tk.Tk()
    app = LedgerFlowApp(root)
    root.mainloop()