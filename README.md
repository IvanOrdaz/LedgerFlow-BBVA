# LedgerFlow BBVA 📊🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

**LedgerFlow BBVA** es una aplicación de escritorio diseñada para automatizar la extracción, clasificación y estructuración de datos financieros desde estados de cuenta digitales en formato PDF de BBVA México directo a libros de trabajo de Excel listos para contabilidad.

Este desarrollo elimina por completo la necesidad de transcripción manual de movimientos bancarios, permitiendo procesar múltiples estados de cuenta y diferentes tipos de productos financieros de manera simultánea en cuestión de segundos.

---

## ✨ Características Principales

- **Clasificación Inteligente de Documentos:** Detecta de forma automática la naturaleza del estado de cuenta de BBVA, distinguiendo entre cuentas de ahorro/nómina (**Libretón Nómina**) y tarjetas de crédito (**Tarjeta Oro/Clásica**) mediante análisis de metadatos de texto.
- **Extracción y Reconstrucción de Saldos:**
  - **Cuenta de Débito:** Reconstruye el flujo cronológico exacto de efectivo (Depósitos, Nómina, Traspasos a Inversiones como GBM, Retiros sin Tarjeta), validando que la suma y resta de transacciones cuadre centavo a centavo con el balance reportado.
  - **Tarjeta de Crédito:** Separa las compras y abonos regulares en el periodo actual de los consumos diferidos a **Meses Sin Intereses (MSI)**, calculando el impacto real en el "pago para no generar intereses".
- **Procesamiento por Lotes (Batch Processing):** Permite arrastrar múltiples PDFs de diferentes meses a una misma carpeta de entrada para generar un archivo contable integrado de manera secuencial.
- **Salida Optimizada para Contadores:** Entrega un libro de Excel (`.xlsx`) estructurado por pestañas, con fechas normalizadas en estándar internacional (`AAAA-MM-DD`) y columnas numéricas limpias (sin caracteres especiales de divisas ni comas) optimizadas para el uso inmediato de tablas dinámicas, filtros y fórmulas de conciliación.
- **Cero Dependencias para el Usuario Final:** Gracias a su empaquetado autónomo, cualquier usuario (como tu contador) puede ejecutar la herramienta en Windows a través de una interfaz gráfica intuitiva sin necesidad de tener Python, VSCode o dependencias instaladas en su equipo.

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Extracción de PDF:** `pdfplumber` (Excelente precisión sobre la estructura tabular nativa del PDF).
- **Manipulación de Datos:** `pandas` (Estructuración y limpieza de DataFrames).
- **Formato de Excel:** `openpyxl` (Generación física del archivo final estructurado).
- **Interfaz Gráfica (GUI):** `tkinter` (Librería nativa de interfaz de usuario de Python).
- **Empaquetado:** `pyinstaller` (Compilación de la aplicación a archivo portable `.exe`).

---

## 📂 Estructura del Proyecto

```text
ledgerflow-bbva/
│
├── src/
│   ├── main.py            # Orquestador principal y lógica de la GUI (Tkinter)
│   ├── classifier.py      # Motor de identificación del tipo de documento
│   ├── parser_debit.py    # Algoritmos de parsing para estados de cuenta de Débito
│   └── parser_credit.py   # Algoritmos de parsing para Tarjetas de Crédito (con MSI)
│
├── requirements.txt       # Dependencias de Python requeridas para desarrollo
├── LICENSE                # Archivo de Licencia MIT
└── README.md              # Documentación técnica del proyecto
```

🚀 Guía de Inicio (Para Desarrolladores)
Prerrequisitos
Asegúrate de contar con Python 3.10 o superior instalado en tu entorno de Windows.

Instalación en Entorno de Desarrollo
Clonar el repositorio:

Bash
git clone [https://github.com/tu-usuario/ledgerflow-bbva.git](https://github.com/tu-usuario/ledgerflow-bbva.git)
cd ledgerflow-bbva
Crear y activar un entorno virtual:

Bash
python -m venv venv

# En Windows

venv\Scripts\activate
Instalar las dependencias del proyecto:

Bash
pip install -r requirements.txt
Ejecutar la aplicación en modo desarrollo:

Bash
python src/main.py
📦 Compilación y Distribución (.exe)
Para compilar este script en una aplicación de Windows completamente autónoma que tu contadora o cliente final pueda ejecutar con doble clic (sin necesidad de instalar Python), ejecuta el siguiente comando en tu terminal dentro del entorno virtual activo:

Bash
pyinstaller --noconsole --onefile --name="LedgerFlow_BBVA" src/main.py
El ejecutable independiente se generará automáticamente en la carpeta dist/LedgerFlow_BBVA.exe.

⚙️ ¿Cómo Funciona la Aplicación? (Arquitectura Interna)
[PDFs de BBVA] ➔ [Classifier] ➔ 📂 Débito ➔ [Parser_Debit] ➔ [Pandas Clean] ➔ 📊 Excel Multitab
➔ 💳 Crédito ➔ [Parser_Credit] ➔ [Pandas Clean]
Ingreso de Datos: El usuario selecciona el directorio de origen que contiene los PDFs de BBVA mediante una ventana nativa de selección de carpetas de Windows.

Identificación (classifier.py): El motor lee la primera página de cada archivo. Si detecta cadenas como "LIBRETON NOMINA", canaliza el procesamiento hacia el parser de débito; si detecta "TARJETA ORO" u homólogos de crédito, lo envía al de tarjeta.

Procesamiento de Débito (parser_debit.py): Captura la tabla de transacciones cronológicas eliminando los saltos de página y notas del pie del PDF. Separa de forma precisa los cargos de los abonos basándose en la alineación espacial de los datos numéricos de BBVA.

Procesamiento de Crédito (parser_credit.py): Separa las transacciones del mes y extrae los datos de la tabla de compras a plazos diferidos, amortizando el pago correspondiente al mes en curso para reportar la deuda real adquirida.

Sanitización de Datos: Transforma formatos de fecha nativos del banco (ej. 23-dic-2024) a un formato normalizado estándar, limpia los símbolos de moneda e interpreta de manera correcta los signos contables.

Exportación consolidada: Usa pandas.ExcelWriter para empaquetar el resultado final en un único libro de Excel estructurado, ordenado cronológicamente por mes.

📄 Licencia
Este proyecto se encuentra distribuido bajo la licencia MIT. Consulta el archivo LICENSE para conocer más detalles sobre los permisos, garantías y límites de responsabilidad legal.

🤝 Contacto
Ivan Ordaz - ordaz.rodriguez.ivan@gmail.com

Enlace del proyecto: https://github.com/IvanOrdaz/LedgerFlow-BBVA.git

```

```
