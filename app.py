
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
    'Abmahnung': 'abmahnung_{Vorfallsdatum}_{Vorfall}_{Nachname}, {Vorname}', 
    'eAU': '{JJJJMMTT}_eAU_{Nachname}, {Vorname}', 
    'Folge eAU': '{JJJJMMTT}_Folge eAU_{Nachname}, {Vorname}', 
    'AU': '{JJJJMMTT}_AU_{Nachname}, {Vorname}', 
    'Folge AU': '{JJJJMMTT}_Folge AU_{Nachname}, {Vorname}',
    'Kind Krank AU': '{JJJJMMTT}_KK_AU_{Nachname}, {Vorname}', 
    'KH-Aufenthalte': '{JJJJMMTT}_KH-Aufenthalt_{Nachname}, {Vorname}', 
    'Zertifikat Basiskurs': 'Zertifikat_Basiskurs_{Ausstellungsdatum}_{Nachname}, {Vorname}', 
    'Expertenkurs': 'Pflegeexperte_{Ausstellungsdatum}_{Nachname}, {Vorname}', 
    'Einwilligungserklärung OrgaVision': 'Einwilligungserklärung_OrgaVision_{Nachname}, {Vorname}', 
    'Präsenzschulungen': '{JMMTT}_{Fortbildungsname}_{Fortbildungszeitraum}_{Nachname}, {Vorname}', 
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
    'Bescheinigung über Beatmungserfahrung/Trachealkanüle': 
    'Bescheinigung_Beatmungserfahrung_{Nachname}, {Vorname}', 
    'Berufsurkunde': '{Abk}_Urkunde_{Nachname}, {Vorname}', 
    'Beglaubigte Kopie Berufsurkunde': 'Begl._Urkunde_{Abk}_{Nachname}, {Vorname}', 
    'Lebenslauf': 'Lebenslauf_{Nachname}, {Vorname}', 
    'Einfaches Führungszeugnis': 'Führungszeugnis_gültig_bis_{Nachname}, {Vorname}', 
    'Erweitertes Führungszeugnis': 'Führungszeugnis_Erw._gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'A&I': 'Zertifikat_A&I_{Ausstellungsdatum}_{Nachname}, {Vorname}', 
    'Arbeitszeugnisse mit Beatmungserfahrung': 'Arbeitszeugnis_Beatmungserfahrung_{Erfahrungszeitraum}_{Nachname}, {Vorname}', 
    'IFSG-Erstbelehrung': '1.IFSG_{Datum}_{Nachname}, {Vorname}', 
    'IFSG-Nachbelehrung': 'IFSG_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'G42': 'G42_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Erste Hilfe Kurs': 'EHK_{Nachname}, {Vorname}', 
    'Praxisanleiter': 'Zertifikat_Praxisanleitung_{Ausstellungsdatum}_{Nachname}, {Vorname}', 
    'Wundexperte': 'Zertifikat_Wundexperte_{Ausstellungsdatum}_{Nachname}, {Vorname}', 
    'Bescheinigung über intensivpflegerische Versorgung': 'Bescheinigung_intensivpflegerische_Versorgung_{Nachname}, {Vorname}', 
    'Arbeitsvertrag': 'AV_{Betriebseintritt}_{Nachname}, {Vorname}', 
    'Fahrtkostenvereinbarung Öffis': 'FK_Öffis_{Beginn}_{Nachname}, {Vorname}', 
    'Fahrtkostenvereinbarung PKW': 'FK_PKW_{Beginn}_{Nachname}, {Vorname}', 
    'Vertragsanpassungen': 'AV-Änderung_{Änderungsdatum}_{Nachname}, {Vorname}', 
    'Zusatzvereinbarungen': 'AV-Zusatzvereinbarung_{Thema}_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Rentenbescheid': 'Rentenbescheid_{Nachname}, {Vorname}', 
    'Weiterbildungsvereinbarungen': 'WB_{Kursname}_{DatumBeginn}_bis_{DatumEnde}_{Nachname}, {Vorname}', 
    'Dienstwagenverträge': 'DWV_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    '1%-Regelung': '1%-Regelung_{Nachname}, {Vorname}', 
    'Teamleitervereinbarung': 'Teamleitervereinbarung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Teamleitervergütung': 'Teamleitervergütung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Neuer Einsatzort': 'Versetzung_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Zwischenzeugnis bipG': 'Zwischenzeugnis_{Nachname}, {Vorname}', 
    'Arbeitszeugnis bipG': 'Arbeitszeugnis_{Nachname}, {Vorname}', 
    'Arbeitgeberbescheinigung bipG': 'Arbeitgeberbescheinigung_{Nachname}, {Vorname}', 
    'Betriebseintrittsänderung': 'Betriebseintrittsänderung_neuer_BE_{Nachname}, {Vorname}', 
    'Mitarbeiter werben Mitarbeiter': 'Vereinbarung_Mitarbeiter werben Mitarbeiter_{Nachname}, {Vorname}', 
    'Gefährungsbeurteilung': 'Gefährdungsbeurteilung_BV_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Pass': 'Pass_gültig_bis_{TT.MM.JJJJ}_{Nachname}, {Vorname}', 
    'Aufenthaltserlaubnis': 'Aufenthaltserlaubnis_bis_{TT.MM.JJJJ}_Erwerbstätigkeit_gestattet_{Nachname}, {Vorname}', 
    'Zusatzblatt': 'Zusatzblatt_Erwerbstätigkeit_gestattet_{Nachname}, {Vorname}'
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
