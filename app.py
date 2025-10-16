

import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile
from datetime import datetime, timedelta

st.set_page_config(page_title="BipG PDF-Umbenennung", layout="centered")
st.title("📄 BipG PDF-Umbenennung")

uploaded_files = st.file_uploader("Ziehe hier deine PDF-Dateien rein oder wähle sie aus", type="pdf", accept_multiple_files=True)

schema = {
    "Einfaches Führungszeugnis": "Führungszeugnis_gültig_bis_{datum}_{nachname}, {vorname}.pdf",
    "Erweitertes Führungszeugnis": "Führungszeugnis_Erw._gültig_bis_{datum}_{nachname}, {vorname}.pdf",
    "IFSG-Nachbelehrung": "IFSG_gültig_bis_{datum}_{nachname}, {vorname}.pdf"
    # Weitere Einträge können ergänzt werden
}

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "
".join(page.get_text() for page in doc)
    return text

def extract_name(text):
    # Sehr einfache Extraktion – kann angepasst werden
    lines = text.split("
")
    for line in lines:
        if "," in line:
            parts = line.split(",")
            if len(parts) == 2:
                return parts[1].strip(), parts[0].strip()  # Vorname, Nachname
    return "Unbekannt", "Unbekannt"

def extract_date(text):
    for word in text.split():
        try:
            return datetime.strptime(word, "%d.%m.%Y")
        except:
            continue
    return None

def generate_filename(doc_type, text):
    vorname, nachname = extract_name(text)
    ausstellungsdatum = extract_date(text)
    if doc_type in schema and ausstellungsdatum:
        gültig_bis = ausstellungsdatum + timedelta(days=730 - 1)
        datum_str = gültig_bis.strftime("%d.%m.%Y")
        return schema[doc_type].format(datum=datum_str, nachname=nachname, vorname=vorname)
    return f"UNBEKANNT_{nachname}_{vorname}.pdf"

if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for file in uploaded_files:
            text = extract_text(file)
            filename = generate_filename("Einfaches Führungszeugnis", text)  # Beispiel
            zipf.writestr(filename, file.getvalue())

    st.success("✅ Dateien erfolgreich umbenannt!")
    st.download_button("📥 ZIP-Datei herunterladen", data=zip_buffer.getvalue(), file_name="umbenannt.zip")
