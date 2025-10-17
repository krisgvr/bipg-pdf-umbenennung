import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import io
import os

# Titel
st.title("📄 Automatische PDF-Umbenennung (mit OCR)")
st.write("Dieses Tool liest Text aus PDFs (auch gescannte) und benennt sie anhand deiner Excel-Tabelle automatisch um.")

# Datei-Uploads
excel_file = st.file_uploader("📘 Excel-Tabelle mit Benennungsschema hochladen", type=["xlsx"])
pdf_files = st.file_uploader("📂 PDF-Dateien hochladen", type=["pdf"], accept_multiple_files=True)

# --- Funktionen --------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes):
    """Extrahiert Text aus PDFs (erst normal, dann OCR-Fallback)."""
    text = ""
    try:
        # 1️⃣ Versuch: normalen Text auslesen
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text("text")
    except Exception as e:
        st.warning(f"Fehler beim Lesen: {e}")

    # 2️⃣ Fallback: OCR, falls kein echter Text gefunden wurde
    if not text.strip():
        images = convert_from_path(io.BytesIO(pdf_bytes))
        ocr_text = ""
        for image in images:
            ocr_text += pytesseract.image_to_string(image, lang="deu")
        text = ocr_text

    return text


def find_best_match(text, df):
    """Findet den besten passenden Namen oder Begriff im PDF-Text."""
    for _, row in df.iterrows():
        name = str(row.get("Name", "")).strip()
        dokumenttyp = str(row.get("Dokumenttyp", "")).strip()

        if name.lower() in text.lower() or dokumenttyp.lower() in text.lower():
            return row
    return None


# --- Hauptlogik --------------------------------------------------------------

if excel_file and pdf_files:
    df = pd.read_excel(excel_file)

    # Spalten prüfen
    if not {"Name", "Dokumenttyp", "Datum"}.issubset(df.columns):
        st.error("⚠️ Deine Excel-Datei muss die Spalten **Name**, **Dokumenttyp** und **Datum** enthalten.")
    else:
        renamed_files = []

        for pdf in pdf_files:
            pdf_bytes = pdf.read()
            text = extract_text_from_pdf(pdf_bytes)

            match = find_best_match(text, df)

            if match is not None:
                name = match["Name"]
                dokumenttyp = match["Dokumenttyp"]
                datum = str(match["Datum"]).split(" ")[0]
                new_name = f"{name}_{dokumenttyp}_{datum}.pdf"
            else:
                new_name = f"unbekannt_{pdf.name}"

            renamed_files.append((pdf.name, new_name))

        # Ergebnis anzeigen
        st.subheader("🔄 Ergebnis:")
        result_df = pd.DataFrame(renamed_files, columns=["Originalname", "Neuer Name"])
        st.dataframe(result_df)

        # Download anbieten
        for original, new in renamed_files:
            st.download_button(label=f"⬇️ {new} herunterladen", data=pdf_bytes, file_name=new, mime="application/pdf")

else:
    st.info("Bitte lade zuerst eine Excel-Datei und mindestens eine PDF-Datei hoch.")
