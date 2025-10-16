import streamlit as st
import fitz  # PyMuPDF
import zipfile
import os
import io
import re
from datetime import datetime, timedelta

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="BipG PDF-Umbenennung", layout="centered")
st.title("📄 BipG PDF-Umbenennung")
st.write("Lade hier PDF-Dateien hoch, um sie automatisch nach bipG-Schema umzubenennen.")

uploaded_files = st.file_uploader("PDF-Dateien hochladen", type="pdf", accept_multiple_files=True)

# -------------------------------
# Benennungsschema
# -------------------------------
schema = {
    'Einfaches Führungszeugnis': 'Führungszeugnis_gültig_bis_{Datum}_{Nachname}, {Vorname}',
    'Erweitertes Führungszeugnis': 'Führungszeugnis_Erw._gültig_bis_{Datum}_{Nachname}, {Vorname}',
    'IFSG-Erstbelehrung': '1.IFSG_{Datum}_{Nachname}, {Vorname}',
    'IFSG-Nachbelehrung': 'IFSG_gültig_bis_{Datum}_{Nachname}, {Vorname}',
    'Arbeitsvertrag': 'AV_{Datum}_{Nachname}, {Vorname}',
    'Zertifikat Basiskurs': 'Zertifikat_Basiskurs_{Datum}_{Nachname}, {Vorname}',
    'Wundexperte': 'Zertifikat_Wundexperte_{Datum}_{Nachname}, {Vorname}',
    'Praxisanleiter': 'Zertifikat_Praxisanleitung_{Datum}_{Nachname}, {Vorname}',
    'Arbeitszeugnis bipG': 'Arbeitszeugnis_{Nachname}, {Vorname}',
    'Arbeitgeberbescheinigung bipG': 'Arbeitgeberbescheinigung_{Nachname}, {Vorname}',
    'Personalausweis': 'Personalausweis_{Nachname}, {Vorname}',
    'Pass': 'Pass_gültig_bis_{Datum}_{Nachname}, {Vorname}',
    'Aufenthaltserlaubnis': 'Aufenthaltserlaubnis_bis_{Datum}_{Nachname}, {Vorname}',
}

# -------------------------------
# Hilfsfunktionen
# -------------------------------
def extract_text(file):
    """Liest gesamten Text aus PDF."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_name(text):
    """Sucht nach 'Frau/Herr Vorname Nachname'."""
    match = re.search(r"(Frau|Herr)\s+([A-ZÄÖÜ][a-zäöüß]+)\s+([A-ZÄÖÜ][a-zäöüß\-]+)", text)
    if match:
        vorname = match.group(2)
        nachname = match.group(3)
        return nachname, vorname
    return "Unbekannt", "Unbekannt"

def extract_date(text):
    """Sucht Datum im Format TT.MM.JJJJ."""
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d.%m.%Y")
        except:
            return None
    return None

def detect_doc_type(text):
    """Versucht, das Dokument anhand von Stichwörtern zu identifizieren."""
    for key in schema:
        if key.lower() in text.lower():
            return key
    return "Unbekannt"

def generate_filename(text):
    """Erstellt den neuen Dateinamen gemäß Schema."""
    nachname, vorname = extract_name(text)
    ausstellungsdatum = extract_date(text)
    dok_typ = detect_doc_type(text)

    # Datum berechnen (z. B. „gültig bis“ für Führungszeugnis / IFSG)
    if dok_typ in ["Einfaches Führungszeugnis", "Erweitertes Führungszeugnis", "IFSG-Nachbelehrung", "IFSG-Erstbelehrung"]:
        if ausstellungsdatum:
            gültig_bis = ausstellungsdatum + timedelta(days=730 - 1)
            datum_str = gültig_bis.strftime("%d.%m.%Y")
        else:
            datum_str = "Datum_fehlt"
    elif ausstellungsdatum:
        datum_str = ausstellungsdatum.strftime("%d.%m.%Y")
    else:
        datum_str = "Datum_fehlt"

    if dok_typ in schema:
        return schema[dok_typ].format(
            Vorname=vorname,
            Nachname=nachname,
            Datum=datum_str
        )
    else:
        return f"UNBEKANNT_{nachname}, {vorname}"

# -------------------------------
# Verarbeitung der Dateien
# -------------------------------
if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in uploaded_files:
            text = extract_text(file)
            new_name = generate_filename(text) + ".pdf"
            zip_file.writestr(new_name, file.getvalue())

    st.success("✅ Dateien wurden erfolgreich umbenannt.")
    st.download_button(
        "📦 ZIP-Datei herunterladen",
        data=zip_buffer.getvalue(),
        file_name="umbenannt.zip",
        mime="application/zip"
    )
