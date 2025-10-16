import streamlit as st
import fitz  # PyMuPDF
import zipfile
import io
import re
from datetime import datetime, timedelta

# ----------------------------
# Streamlit Grundkonfiguration
# ----------------------------
st.set_page_config(page_title="BipG PDF-Umbenennung", layout="centered")
st.title("📄 BipG PDF-Umbenennung")
st.write("Bitte laden Sie mehrere PDF-Dateien hoch. Sie werden automatisch nach dem bipG-Benennungsschema umbenannt.")

uploaded_files = st.file_uploader("PDF-Dateien hochladen", type="pdf", accept_multiple_files=True)

# ----------------------------
# Benennungsschema
# ----------------------------
schema = {
    'Abmahnung': 'abmahnung_{JJJJMMTT}_{Vorfall}_{Nachname}, {Vorname}', 
    'eAU': '{JJJJMMTT}_eAU_{Nachname}, {Vorname}', 
    'Folge eAU': '{JJJJMMTT}_Folge_eAU_{Nachname}, {Vorname}', 
    'AU': '{JJJJMMTT}_AU_{Nachname}, {Vorname}', 
    'Folge AU': '{JJJJMMTT}_Folge_AU_{Nachname}, {Vorname}',
    'Kind Krank AU': '{JJJJMMTT}_KK_AU_{Nachname}, {Vorname}', 
    'KH-Aufenthalte': '{JJJJMMTT}_KH-Aufenthalt_{Nachname}, {Vorname}', 
    'Zertifikat Basiskurs': 'Zertifikat_Basiskurs_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Expertenkurs': 'Pflegeexperte_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Einwilligungserklärung OrgaVision': 'Einwilligungserklärung_OrgaVision_{Nachname}, {Vorname}', 
    'Präsenzschulungen': '{JJMMTT}_{Fortbildungsname}_{Fortbildungszeitraum}_{Nachname}, {Vorname}', 
    'Webinare': '{JJMMTT}_{Fortbildungsname}_{Fortbildungszeitraum}_{Nachname}, {Vorname}', 
    'Kundenbezogene Schulungen (bipG spezifisch)': '{JJMMTT}_{Fortbildungsname}_{Fortbildungszeitraum}_{Nachname}, {Vorname}', 
    'Notfallmanagement in der AKI': '{JJMMTT}_{Fortbildungsname}_{Fortbildungszeitraum}_{Nachname}, {Vorname}', 
    '9-Punkte Plan (bipG spezifisch)': '{JJMMTT}_{Gerätename}_{Nachname}, {Vorname}', 
    'MPG Heft': '{JJMMTT}_{Gerätename}_{Nachname}, {Vorname}', 
    'Bewerbungsanschreiben': 'Bewerbungsanschreiben_{Nachname}, {Vorname}', 
    'Personalfragebogen': 'Personalfragebogen_{Nachname}, {Vorname}', 
    'Datenschutz': 'Datenschutz_{Nachname}, {Vorname}', 
    'Geburtsurkunde Kinder': 'Geburtsurkunde_Kinder_{Nachname}, {Vorname}', 
    'Urlaubsbescheinigung': 'Urlaubsbescheinigung_{Nachname}, {Vorname}', 
    'Namensänderungsnachweis': 'Namensänderungsnachweis_{Nachname}, {Vorname}_geb. {Geburtsname}', 
    'Eheurkunde': 'Eheurkunde_{Nachname}, {Vorname}_geb. {Geburtsname}', 
    'Mitgliedsbescheinigung Krankenkasse': 'Mitgliedsbescheinigung_Krankenkasse_{Nachname}, {Vorname}', 
    'Führerschein': 'Führerschein_{Nachname}, {Vorname}', 
    'Personalausweis': 'Personalausweis_{Nachname}, {Vorname}', 
    'Bescheinigung über Beatmungserfahrung/Trachealkanüle': 'Bescheinigung_Beatmungserfahrung_{Nachname}, {Vorname}', 
    'Berufsurkunde': '{Abk}_Urkunde_{Nachname}, {Vorname}', 
    'Beglaubigte Kopie Berufsurkunde': 'Begl._Urkunde_{Abk}_{Nachname}, {Vorname}', 
    'Lebenslauf': 'Lebenslauf_{Nachname}, {Vorname}', 
    'Einfaches Führungszeugnis': 'Führungszeugnis_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Erweitertes Führungszeugnis': 'Führungszeugnis_Erw._gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'A&I': 'Zertifikat_A&I_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Arbeitszeugnisse mit Beatmungserfahrung': 'Arbeitszeugnis_Beatmungserfahrung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'IFSG-Erstbelehrung': '1.IFSG_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'IFSG-Nachbelehrung': 'IFSG_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'G42': 'G42_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Erste Hilfe Kurs': 'EHK_{Nachname}, {Vorname}', 
    'Praxisanleiter': 'Zertifikat_Praxisanleitung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Wundexperte': 'Zertifikat_Wundexperte_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Bescheinigung über intensivpflegerische Versorgung': 'Bescheinigung_intensivpflegerische_Versorgung_{Nachname}, {Vorname}', 
    'Arbeitsvertrag': 'AV_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Fahrtkostenvereinbarung Öffis': 'FK_Öffis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Fahrtkostenvereinbarung PKW': 'FK_PKW_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Vertragsanpassungen': 'AV-Änderung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Zusatzvereinbarungen': 'AV-Zusatzvereinbarung_{Thema}_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Rentenbescheid': 'Rentenbescheid_{Nachname}, {Vorname}', 
    'Weiterbildungsvereinbarungen': 'WB_{Kursname}_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Dienstwagenverträge': 'DWV_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    '1%-Regelung': '1%-Regelung_{Nachname}, {Vorname}', 
    'Teamleitervereinbarung': 'Teamleitervereinbarung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Teamleitervergütung': 'Teamleitervergütung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Neuer Einsatzort': 'Versetzung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Zwischenzeugnis bipG': 'Zwischenzeugnis_{Nachname}, {Vorname}', 
    'Arbeitszeugnis bipG': 'Arbeitszeugnis_{Nachname}, {Vorname}', 
    'Arbeitgeberbescheinigung bipG': 'Arbeitgeberbescheinigung_{Nachname}, {Vorname}', 
    'Betriebseintrittsänderung': 'Betriebseintrittsänderung_neuer_BE_{Nachname}, {Vorname}', 
    'Mitarbeiter werben Mitarbeiter': 'Vereinbarung_Mitarbeiter_werben_Mitarbeiter_{Nachname}, {Vorname}', 
    'Gefährungsbeurteilung': 'Gefährdungsbeurteilung_BV_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Pass': 'Pass_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Aufenthaltserlaubnis': 'Aufenthaltserlaubnis_bis_{TT.MM.JJJJ}_Erwerbstätigkeit_gestattet_{Nachname}, {Vorname}', 
    'Zusatzblatt': 'Zusatzblatt_Erwerbstätigkeit_gestattet_{Nachname}, {Vorname}'
}

# ----------------------------
# Hilfsfunktionen
# ----------------------------

def extract_text(file):
    """Liest den Text aus einer PDF-Datei."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_name(text):
    """Sucht nach 'Vorname Nachname' im Text."""
    lines = text.split("\n")
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {parts[-2]}"
    return "Unbekannt"

def extract_date(text):
    """Findet ein Datum im Format TT.MM.JJJJ."""
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d.%m.%Y")
        except:
            return None
    return None

def generate_filename(text):
    """Erzeugt anhand des Schemas einen passenden Dateinamen."""
    name = extract_name(text)
    nachname = name.split(",")[0].strip() if "," in name else name
    vorname = name.split(",")[1].strip() if "," in name else ""

    ausstellungsdatum = extract_date(text)
    for key, template in schema.items():
        if key.lower() in text.lower():
            # "gültig bis" nur für bestimmte Dateien
            if "gültig_bis" in template and ausstellungsdatum:
                gültig_bis = ausstellungsdatum + timedelta(days=730)
                datum_str = gültig_bis.strftime("%d.%m.%Y")
            else:
                datum_str = ausstellungsdatum.strftime("%d.%m.%Y") if ausstellungsdatum else "Datum_fehlt"

            try:
                return template.format(
                    Nachname=nachname,
                    Vorname=vorname,
                    TT_MM_JJJJ=datum_str,
                    JJJJMMTT=ausstellungsdatum.strftime("%Y%m%d") if ausstellungsdatum else "Datum_fehlt"
                )
            except Exception as e:
                return f"Fehlerhafte_Vorlage_{key}_{nachname}"
    return f"UNBEKANNT_{nachname}"

# ----------------------------
# Hauptlogik
# ----------------------------
if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in uploaded_files:
            text = extract_text(file)
            new_name = generate_filename(text) + ".pdf"
            zip_file.writestr(new_name, file.getvalue())

    st.success("✅ Dateien wurden erfolgreich umbenannt.")
    st.download_button("📦 ZIP-Datei herunterladen", data=zip_buffer.getvalue(), file_name="umbenannt.zip", mime="application/zip")
