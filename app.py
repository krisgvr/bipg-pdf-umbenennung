import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import zipfile
import re
import pandas as pd

# -----------------------------
# 🔤 Dein Benennungsschema
# -----------------------------
SCHEMA = {
    "Abmahnung": "abmahnung_{Vorfallsdatum}_{Vorfall}_{Nachname}, {Vorname}",
    "eAU": "{JJJJMMTT}_eAU_{Nachname}, {Vorname}",
    "Folge eAU": "{JJJJMMTT}_Folge_eAU_{Nachname}, {Vorname}",
    "AU": "{JJJJMMTT}_AU_{Nachname}, {Vorname}",
    "Folge AU": "{JJJJMMTT}_Folge_AU_{Nachname}, {Vorname}",
    "Kind Krank AU": "{JJJJMMTT}_KK_AU_{Nachname}, {Vorname}",
    "KH-Aufenthalte": "{JJJJMMTT}_KH-Aufenthalt_{Nachname}, {Vorname}",
    "Zertifikat Basiskurs": "Zertifikat_Basiskurs_{Ausstellungsdatum}_{Nachname}, {Vorname}",
    "Expertenkurs": "Pflegeexperte_{Ausstellungsdatum}_{Nachname}, {Vorname}",
    "Einfaches Führungszeugnis": "Führungszeugnis_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "Erweitertes Führungszeugnis": "Führungszeugnis_Erw._gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "IFSG-Erstbelehrung": "1.IFSG_{Datum}_{Nachname}, {Vorname}",
    "IFSG-Nachbelehrung": "IFSG_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "G42": "G42_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "Arbeitsvertrag": "AV_{Betriebseintritt}_{Nachname}, {Vorname}",
    "Vertragsanpassungen": "AV-Änderung_{Änderungsdatum}_{Nachname}, {Vorname}",
    "Zusatzvereinbarungen": "AV-Zusatzvereinbarung_{Thema}_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "Personalausweis": "Personalausweis_{Nachname}, {Vorname}",
    "Pass": "Pass_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "Aufenthaltserlaubnis": "Aufenthaltserlaubnis_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}",
    "Lebenslauf": "Lebenslauf_{Nachname}, {Vorname}",
}

# -----------------------------
# 🧠 Hilfsfunktionen
# -----------------------------

def extract_text_from_pdf(pdf_bytes):
    """Extrahiert Text aus PDF (inkl. OCR bei Bildern)."""
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_page = page.get_text("text")
            if not text_page.strip():
                try:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text += pytesseract.image_to_string(img, lang="deu")
                except pytesseract.TesseractNotFoundError:
                    st.warning("⚠️ Tesseract OCR ist nicht installiert. OCR wurde übersprungen.")
            else:
                text += text_page
    return text


def detect_document_type(text):
    text_lower = text.lower()
    for key in SCHEMA.keys():
        if key.lower().replace(" ", "") in text_lower.replace(" ", ""):
            return key
    return "Unbekannt"


def extract_name(text):
    match = re.search(r"(Herr|Frau)\s+([A-ZÄÖÜ][a-zäöüß]+)\s+([A-ZÄÖÜ][a-zäöüß\-]+)", text)
    if match:
        return match.group(3), match.group(2)
    return None, None


def extract_date(text):
    match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", text)
    if match:
        return match.group(1)
    return None


def generate_filename(doc_type, text):
    nachname, vorname = extract_name(text)
    datum = extract_date(text)

    if doc_type == "Unbekannt":
        return None

    schema = SCHEMA.get(doc_type)
    if not schema:
        return None

    if not vorname:
        vorname = st.text_input(f"Vorname für {doc_type}:")
    if not nachname:
        nachname = st.text_input(f"Nachname für {doc_type}:")
    if "{TT.MM.JJJJ}" in schema and not datum:
        datum = st.text_input(f"Datum (TT.MM.JJJJ) für {doc_type}:")
    if "{JJJJMMTT}" in schema and not datum:
        datum = st.text_input(f"Datum (JJJJMMTT) für {doc_type}:")

    filename = schema.format(
        Vorname=vorname or "Vorname",
        Nachname=nachname or "Nachname",
        TT_MM_JJJJ=datum or "",
        JJJJMMTT=datum or "",
        Ausstellungsdatum=datum or "",
        Datum=datum or "",
        Vorfallsdatum=datum or "",
        Betriebseintritt=datum or "",
        Thema="Thema"
    )
    return filename.strip().replace(" ", "_")


# -----------------------------
# 🖥️ Streamlit App
# -----------------------------
st.set_page_config(page_title="bipG PDF-Umbenennung", layout="wide")

st.title("📁 Automatische PDF-Umbenennung – bipG Version")
st.write("Lade hier mehrere PDF-Dateien hoch. Die App erkennt Typ, Datum und Namen automatisch.")

uploaded_files = st.file_uploader("Wähle deine PDF-Dateien aus", type="pdf", accept_multiple_files=True)

if uploaded_files:
    renamed_files = []
    for file in uploaded_files:
        pdf_bytes = file.read()
        text = extract_text_from_pdf(pdf_bytes)
        doc_type = detect_document_type(text)

        st.markdown(f"**Erkannter Typ:** {doc_type}")
        new_name = generate_filename(doc_type, text)
        if new_name:
            new_name += ".pdf"
            st.success(f"➡️ Neuer Name: {new_name}")
            renamed_files.append((new_name, pdf_bytes))
            st.download_button("📥 Diese Datei herunterladen", data=pdf_bytes, file_name=new_name)
        else:
            st.error("❌ Keine eindeutige Zuordnung möglich")

    if renamed_files:
        with io.BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for name, content in renamed_files:
                    zipf.writestr(name, content)
            zip_buffer.seek(0)
            st.download_button(
                "📦 Alle umbenannten Dateien als ZIP herunterladen",
                data=zip_buffer,
                file_name="umbenannte_dateien.zip",
                mime="application/zip"
            )
