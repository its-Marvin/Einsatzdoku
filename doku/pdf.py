"""PDF-Erzeugung fuer die Einsatzdokumentation.

Basiert auf ReportLab (reines Python-Paket). Im Gegensatz zu WeasyPrint werden
keine nativen Systembibliotheken (Pango, Cairo, GDK-Pixbuf, libffi, ...)
benoetigt, wodurch das Container-Image deutlich schlanker bleibt.
"""

import io

from django.utils import timezone
from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# --- Farben (entsprechen dem bisherigen HTML/CSS-Layout) ---------------------
FARBE_TEXT = colors.HexColor("#333333")
FARBE_LABEL = colors.HexColor("#666666")
FARBE_LINIE = colors.HexColor("#cccccc")
FARBE_RAHMEN = colors.HexColor("#dddddd")
FARBE_KOPF_BG = colors.HexColor("#f0f0f0")
FARBE_BOX_BG = colors.HexColor("#fafafa")
FARBE_TABELLE_KOPF = colors.HexColor("#333333")
FARBE_TABELLE_ZEBRA = colors.HexColor("#f9f9f9")
FARBE_MELDUNG_BG = colors.HexColor("#f5f5f5")
FARBE_MELDUNG_BALKEN = colors.HexColor("#0066cc")
FARBE_WICHTIG_BG = colors.HexColor("#ffcccc")
FARBE_WICHTIG_BALKEN = colors.HexColor("#ff0000")
FARBE_DAUER_BG = colors.HexColor("#ffffcc")
FARBE_DAUER_RAHMEN = colors.HexColor("#cccc00")
FARBE_INFO_BG = colors.HexColor("#f0f8ff")
FARBE_OFFEN = colors.HexColor("#b00020")
FARBE_FOOTER = colors.HexColor("#999999")

SEITE = A4
RAND_LINKS = 3 * cm
RAND_RECHTS = 2 * cm
RAND_OBEN = 2 * cm
RAND_UNTEN = 2 * cm
INHALTSBREITE = SEITE[0] - RAND_LINKS - RAND_RECHTS


def _styles():
    basis = getSampleStyleSheet()
    s = {}
    s['normal'] = ParagraphStyle(
        'EdNormal', parent=basis['Normal'], fontName='Helvetica', fontSize=10,
        leading=14, textColor=FARBE_TEXT,
    )
    s['h1'] = ParagraphStyle(
        'EdH1', parent=s['normal'], fontName='Helvetica-Bold', fontSize=18,
        leading=22, spaceAfter=4, textColor=colors.black,
    )
    s['h2'] = ParagraphStyle(
        'EdH2', parent=s['normal'], fontName='Helvetica-Bold', fontSize=14,
        leading=18, textColor=colors.black,
    )
    s['h3'] = ParagraphStyle(
        'EdH3', parent=s['normal'], fontName='Helvetica-Bold', fontSize=12,
        leading=15, spaceBefore=8, spaceAfter=4, textColor=colors.black,
    )
    s['label'] = ParagraphStyle(
        'EdLabel', parent=s['normal'], fontName='Helvetica-Bold', fontSize=8,
        leading=10, textColor=FARBE_LABEL,
    )
    s['wert'] = ParagraphStyle(
        'EdWert', parent=s['normal'], fontSize=10, leading=13,
    )
    s['th'] = ParagraphStyle(
        'EdTh', parent=s['normal'], fontName='Helvetica-Bold', fontSize=9,
        leading=12, textColor=colors.white,
    )
    s['td'] = ParagraphStyle(
        'EdTd', parent=s['normal'], fontSize=9, leading=12,
    )
    s['meldung'] = ParagraphStyle(
        'EdMeldung', parent=s['normal'], fontSize=9.5, leading=13,
    )
    s['meldung_wichtig'] = ParagraphStyle(
        'EdMeldungWichtig', parent=s['meldung'], fontName='Helvetica-Bold',
        textColor=FARBE_WICHTIG_BALKEN,
    )
    s['meldung_meta'] = ParagraphStyle(
        'EdMeldungMeta', parent=s['normal'], fontSize=8, leading=11,
        textColor=FARBE_LABEL,
    )
    s['zeit'] = ParagraphStyle(
        'EdZeit', parent=s['normal'], fontName='Helvetica-Bold', fontSize=9,
        leading=12, textColor=colors.white,
    )
    s['staerke'] = ParagraphStyle(
        'EdStaerke', parent=s['normal'], fontName='Courier-Bold', fontSize=10,
        leading=13, alignment=TA_RIGHT,
    )
    s['footer'] = ParagraphStyle(
        'EdFooter', parent=s['normal'], fontSize=8, leading=10,
        textColor=FARBE_FOOTER,
    )
    return s


def _lokal(dt, fmt='%d.%m.%Y %H:%M'):
    """Formatiert ein (ggf. aware) datetime in der konfigurierten Zeitzone."""
    if dt is None:
        return ""
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime(fmt)


def _p(text, style):
    """Erzeugt einen Paragraph mit sicher escaptem Text und Zeilenumbruechen."""
    if text is None:
        text = ""
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def _hex(farbe):
    """Liefert eine ReportLab-Farbe als '#rrggbb'-String fuer Inline-Markup."""
    return "#" + farbe.hexval()[2:]


def _hex_farbe(wert, fallback=colors.HexColor("#dddddd")):
    try:
        return colors.HexColor(wert)
    except Exception:
        return fallback


def _autor_name(autor):
    """Liefert 'Vorname Nachname' eines Benutzers (Fallback: Benutzername)."""
    if not autor:
        return ""
    name = " ".join(
        teil for teil in (
            getattr(autor, 'first_name', '') or '',
            getattr(autor, 'last_name', '') or '',
        ) if teil
    ).strip()
    if name:
        return name
    try:
        return autor.get_username()
    except Exception:
        return str(autor)


def _kopfzeile(einsatz, s):
    nummer = einsatz.extNummer if einsatz.extNummer else f"Nr. {einsatz.Nummer}"
    titel = _p(f"Einsatzdokumentation - {nummer}", s['h1'])
    # H1 mit Unterstrich: als Tabelle mit unterer Linie umgesetzt
    t = Table([[titel]], colWidths=[INHALTSBREITE])
    t.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.black),
    ]))
    return t


def _abschnittstitel(text, s):
    t = Table([[_p(text, s['h2'])]], colWidths=[INHALTSBREITE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), FARBE_KOPF_BG),
        ('LINEBEFORE', (0, 0), (0, -1), 3, FARBE_TABELLE_KOPF),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def _grunddaten(einsatz, s):
    def feld(label, wert_flowables):
        inner = Table([[_p(label, s['label'])], [wert_flowables]],
                      colWidths=[(INHALTSBREITE - 20) / 2.0])
        inner.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 2),
            ('BOTTOMPADDING', (0, 1), (0, 1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        return inner

    nummer = einsatz.extNummer if einsatz.extNummer else einsatz.Nummer
    ort = einsatz.OrtFrei if einsatz.OrtFrei else einsatz.Ort.Langname

    anfang = _lokal(einsatz.Erstellt) + " Uhr"
    if einsatz.Ende:
        ende_txt = escape(_lokal(einsatz.Ende)) + " Uhr"
    else:
        ende_txt = (f'<font color="{_hex(FARBE_OFFEN)}">'
                    f'<b>NICHT BEENDET</b></font>')
    zeit_para = Paragraph(escape(anfang) + "<br/>" + ende_txt, s['wert'])

    zeilen = [
        [feld("Einsatznummer", _p(nummer, s['wert'])),
         feld("Stichwort", _p(einsatz.Stichwort.Langname, s['wert']))],
        [feld("Adresse", _p(einsatz.Adresse, s['wert'])),
         feld("Ort", _p(f"{ort} ({einsatz.Ort.Kurzname})", s['wert']))],
        [feld("Einsatzleiter", _p(einsatz.Einsatzleiter or "Keine Angabe", s['wert'])),
         feld("Anfang / Ende", zeit_para)],
    ]
    t = Table(zeilen, colWidths=[INHALTSBREITE / 2.0] * 2)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), FARBE_BOX_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, FARBE_RAHMEN),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def _infobox(text_flowable, bg, rahmen):
    t = Table([[text_flowable]], colWidths=[INHALTSBREITE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 0.75, rahmen),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def _datentabelle(kopf, zeilen, spaltenbreiten, s):
    daten = [[_p(h, s['th']) for h in kopf]]
    daten += [[_p(z, s['td']) for z in zeile] for zeile in zeilen]
    t = Table(daten, colWidths=spaltenbreiten, repeatRows=1)
    stil = [
        ('BACKGROUND', (0, 0), (-1, 0), FARBE_TABELLE_KOPF),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, FARBE_LINIE),
        ('LINEBELOW', (0, -1), (-1, -1), 1, FARBE_TABELLE_KOPF),
        ('INNERGRID', (0, 1), (-1, -1), 0.25, FARBE_RAHMEN),
    ]
    for i in range(1, len(daten)):
        if i % 2 == 0:
            stil.append(('BACKGROUND', (0, i), (-1, i), FARBE_TABELLE_ZEBRA))
    t.setStyle(TableStyle(stil))
    return t


def _fahrzeugzeile(html, s, farbe):
    """Farbig hinterlegte Zeile der Fahrzeug-/Zugliste."""
    t = Table([[Paragraph(html, s['td'])]], colWidths=[INHALTSBREITE])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), farbe),
        ('BOX', (0, 0), (-1, -1), 0.25, FARBE_RAHMEN),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def _meldungsblock(meldung, s):
    wichtig = bool(meldung.Wichtig)
    balken = FARBE_WICHTIG_BALKEN if wichtig else FARBE_MELDUNG_BALKEN
    hintergrund = FARBE_WICHTIG_BG if wichtig else FARBE_MELDUNG_BG

    # Im PDF immer das vollstaendige Datum inkl. Uhrzeit ausgeben
    zeit = Table([[_p(_lokal(meldung.Erstellt), s['zeit'])]])
    zeit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), balken),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    autor_name = _autor_name(meldung.Autor)

    kopf_rechts = [_p(autor_name, s['meldung_meta'])]

    kopf = Table([[zeit, kopf_rechts]],
                 colWidths=[INHALTSBREITE * 0.30, INHALTSBREITE * 0.70 - 16])
    kopf.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    inhalt = [kopf, _p(meldung.Inhalt,
                       s['meldung_wichtig'] if wichtig else s['meldung'])]

    block = Table([[inhalt]], colWidths=[INHALTSBREITE])
    block.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), hintergrund),
        ('LINEBEFORE', (0, 0), (0, -1), 3, balken),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return block


def _seiten_dekoration(canvas, doc, fusstext):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(FARBE_FOOTER)
    canvas.setStrokeColor(FARBE_RAHMEN)
    y = RAND_UNTEN - 0.7 * cm
    canvas.line(RAND_LINKS, y + 0.35 * cm, SEITE[0] - RAND_RECHTS, y + 0.35 * cm)
    canvas.drawString(RAND_LINKS, y, fusstext)
    canvas.drawRightString(SEITE[0] - RAND_RECHTS, y, f"Seite {doc.page}")
    canvas.restoreState()


def build_einsatz_pdf(context):
    """Erzeugt die Einsatzdokumentation als PDF und liefert die Bytes zurueck."""
    s = _styles()
    einsatz = context['einsatz']
    story = []

    # --- Kopf und Grunddaten ---
    story.append(_kopfzeile(einsatz, s))
    story.append(Spacer(1, 10))
    story.append(_grunddaten(einsatz, s))
    story.append(Spacer(1, 10))

    dauer = (f"<b>Einsatzdauer:</b> {context['dauer_tage']} Tage, "
             f"{context['dauer_stunden']} Stunden, {context['dauer_minuten']} Minuten")
    story.append(_infobox(Paragraph(dauer, s['normal']), FARBE_DAUER_BG, FARBE_DAUER_RAHMEN))

    # --- Personen ---
    alle_personen = list(context.get('alle_Personen') or [])
    if alle_personen:
        story.append(Spacer(1, 14))
        story.append(_abschnittstitel("Im Einsatz involvierte Personen", s))
        story.append(Spacer(1, 8))
        zeilen = [
            [f"{p.Nachname}, {p.Vorname}", p.Rolle, p.Notizen or "-"]
            for p in alle_personen
        ]
        story.append(_datentabelle(
            ["Name", "Rolle", "Notizen"], zeilen,
            [INHALTSBREITE * 0.33, INHALTSBREITE * 0.25, INHALTSBREITE * 0.42], s))

    # --- Fahrzeuge / Staerkemeldungen ---
    fahrzeuge = list(context.get('eingesetzte_Fahrzeuge') or [])
    externe = list(context.get('externe_zuege') or [])
    if fahrzeuge or externe:
        story.append(Spacer(1, 14))
        story.append(_abschnittstitel("Eingesetzte Fahrzeuge und Staerkemeldungen", s))
        story.append(Spacer(1, 8))

        gesamt = (f"{context['fahrzeug_gesamt_zugfuehrer']}/"
                  f"{context['fahrzeug_gesamt_gruppenfuehrer']}/"
                  f"{context['fahrzeug_gesamt_mannschaft']} "
                  f"({context['fahrzeug_gesamt_agt']} AGT)")
        summe = Table([[_p("Gesamtstaerke", s['h3']), _p(gesamt, s['staerke'])]],
                      colWidths=[INHALTSBREITE * 0.5 - 10, INHALTSBREITE * 0.5 - 10])
        summe.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(_infobox(summe, FARBE_INFO_BG, FARBE_MELDUNG_BALKEN))

        story.append(_p("Fahrzeugliste", s['h3']))
        for f in fahrzeuge:
            farbe = _hex_farbe(getattr(f.Name.Zug, 'Farbe', None))
            text = (f"<b>{escape(str(f.Name))}</b> | Besatzung: "
                    f"{f.Zugfuehrer}/{f.Gruppenfuehrer}/{f.Mannschaft} | AGT: {f.Atemschutz}")
            story.append(_fahrzeugzeile(text, s, farbe))
            story.append(Spacer(1, 3))
        for z in externe:
            text = (f"<b>{escape(str(z.Name))} (extern)</b> | Besatzung: "
                    f"{z.Zugfuehrer}/{z.Gruppenfuehrer}/{z.Mannschaft} | AGT: {z.Atemschutz}")
            story.append(_fahrzeugzeile(text, s, colors.HexColor("#dddddd")))
            story.append(Spacer(1, 3))

    # --- Meldungen (immer auf neuer Seite) ---
    meldungen = list(context.get('alle_Meldungen') or [])
    if meldungen:
        story.append(PageBreak())
        story.append(_abschnittstitel("Meldungen / Einsatzverlauf", s))
        story.append(Spacer(1, 8))
        # alle_Meldungen kommt absteigend sortiert -> chronologisch ausgeben
        for m in reversed(meldungen):
            story.append(KeepTogether(_meldungsblock(m, s)))
            story.append(Spacer(1, 6))

    fusstext = ("Einsatzdokumentation - Generiert: "
                + _lokal(context['today']) + " Uhr")

    puffer = io.BytesIO()
    doc = SimpleDocTemplate(
        puffer,
        pagesize=SEITE,
        leftMargin=RAND_LINKS,
        rightMargin=RAND_RECHTS,
        topMargin=RAND_OBEN,
        bottomMargin=RAND_UNTEN,
        title=f"Einsatzdokumentation {einsatz.extNummer or einsatz.Nummer}",
        author=context.get('einstellungen').Name if context.get('einstellungen') else "Einsatzdoku",
    )

    def dekoration(canvas, dokument):
        _seiten_dekoration(canvas, dokument, fusstext)

    doc.build(story, onFirstPage=dekoration, onLaterPages=dekoration)
    return puffer.getvalue()











