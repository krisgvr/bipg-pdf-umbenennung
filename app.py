
import streamlit as st
import fitz  # PyMuPDF
import zipfile
import os
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="BipG PDF-Umbenennung", layout="centered")
st.title("📄 BipG PDF-Umbenennung")

uploaded_files = st.file_uploader("PDF-Dateien hochladen", type="pdf", accept_multiple_files=True)

schema = {
    "Einfaches Führungszeugnis": "Führungszeugnis_gültig_bis_{datum}_{name}",
    "Erweitertes Führungszeugnis": "Führungszeugnis_Erw._gültig_bis_{datum}_{name}",
    "IFSG-Nachbelehrung": "IFSG_gültig_bis_{datum}_{name}"
    # Weitere Einträge können ergänzt werden
}

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_name(text):
    # Sehr einfache Extraktion: Suche nach "Vorname Nachname"
    lines = text.split("
")
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {parts[-2]}"
    return "Unbekannt"

def extract_date(text):
    # Suche nach Datum im Format TT.MM.JJJJ
    import re
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d.%m.%Y")
        except:
            return None
    return None

def generate_filename(text):
    name = extract_name(text)
    ausstellungsdatum = extract_date(text)
    for key in schema:
        if key.lower() in text.lower():
            if ausstellungsdatum:
                gültig_bis = ausstellungsdatum + timedelta(days=730 - 1)
                datum_str = gültig_bis.strftime("%d.%m.%Y")
                return schema[key].format(datum=datum_str, name=name)
            else:
                return schema[key].format(datum="Datum_fehlt", name=name)
    return f"UNBEKANNT_{name}"

if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in uploaded_files:
            text = extract_text(file)
            new_name = generate_filename(text) + ".pdf"
            zip_file.writestr(new_name, file.getvalue())

    st.success("Dateien wurden erfolgreich umbenannt.")
    st.download_button("ZIP-Datei herunterladen", data=zip_buffer.getvalue(), file_name="umbenannt.zip", mime="application/zip")
