"""Tests fuer die Einsatzdokumentation.

Schwerpunkte:
  * PDF-Export (ReportLab, ersetzt die frueher genutzte WeasyPrint-Variante)
  * Chronologische Sortierung der Meldungen
  * Modell-Hilfsmethoden
  * Views inkl. Berechtigungspruefungen, OEL-Ansicht und JSON-Endpunkte
"""

import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from doku.forms import OrtForm, ZugForm
from doku.models import (
    Einheiten,
    Einsatz,
    EinsatzRevision,
    Einsatzstellen,
    Einsatzstellen_Notizen,
    Einstellungen,
    Fahrzeug,
    Fahrzeuge,
    Meldung,
    Ort,
    Person,
    Profile,
    Stichwort,
    Zug,
    ZugExtra,
)
from doku.pdf import build_einsatz_pdf
from doku.views import get_icons


class EinsatzTestMixin:
    """Legt einen vollstaendig befuellten Einsatz als Testdatenbestand an."""

    @classmethod
    def basisdaten(cls):
        cls.user = get_user_model().objects.create_user(
            username="tester", password="geheim",
            first_name="Max", last_name="Müller",
        )
        cls.einstellungen = Einstellungen.objects.create(Name="Feuerwehr Musterstadt")
        cls.ort = Ort.objects.create(PLZ=12345, Kurzname="MST", Langname="Musterstadt")
        cls.ort_frei = Ort.objects.create(PLZ=0, Kurzname="ZZZ", Langname="Freitext")
        cls.stichwort = Stichwort.objects.create(Kurzname="B3", Langname="Gebäudebrand groß")
        cls.zug = Zug.objects.create(Name="Zug 1", Farbe="#ffcc00")
        cls.einsatz = Einsatz.objects.create(
            Stichwort=cls.stichwort, Adresse="Hauptstraße 1", Ort=cls.ort,
            Einsatzleiter="Müller, Max", extNummer=2026001,
        )

    @classmethod
    def einsatz_befuellen(cls):
        cls.fahrzeugtyp = Fahrzeuge.objects.create(
            Funkname="MST 1/44", Ort=cls.ort, Typ="HLF 20", Zug=cls.zug,
        )
        cls.fahrzeug = Fahrzeug.objects.create(
            Name=cls.fahrzeugtyp, Zugfuehrer=0, Gruppenfuehrer=1, Mannschaft=5,
            Atemschutz=4, Einsatz=cls.einsatz, Autor=cls.user,
        )
        cls.zug_extra = ZugExtra.objects.create(
            Name="Rettungsdienst", Zugfuehrer=1, Gruppenfuehrer=0, Mannschaft=3,
            Atemschutz=0, Einsatz=cls.einsatz,
        )
        cls.person = Person.objects.create(
            Nachname="Schmidt", Vorname="Anna", Rolle="Eigentümerin",
            Notizen="vor Ort angetroffen", Einsatz=cls.einsatz,
        )
        cls.meldung_normal = Meldung.objects.create(
            Inhalt="Erste Lage: Rauch aus Dachstuhl.", Wichtig=False,
            Einsatz=cls.einsatz, Autor=cls.user, Zug=cls.zug,
        )
        cls.meldung_wichtig = Meldung.objects.create(
            Inhalt="Feuer aus.\nNachlöscharbeiten laufen.", Wichtig=True,
            Einsatz=cls.einsatz, Autor=cls.user, Zug=None,
        )

    @staticmethod
    def pdf_kontext(einsatz, einstellungen=None, meldungen=None, fahrzeuge=None,
                    externe=None, personen=None):
        """Baut denselben Kontext, den auch die View an den PDF-Builder uebergibt."""
        meldungen = (Meldung.objects.filter(Einsatz=einsatz).order_by('-Erstellt', '-pk')
                     if meldungen is None else meldungen)
        fahrzeuge = (Fahrzeug.objects.filter(Einsatz=einsatz)
                     if fahrzeuge is None else fahrzeuge)
        externe = (ZugExtra.objects.filter(Einsatz=einsatz)
                   if externe is None else externe)
        personen = (Person.objects.filter(Einsatz=einsatz)
                    if personen is None else personen)
        dauer = einsatz.getDuration()
        sekunden = max(int(dauer.total_seconds()), 0)
        return {
            'einsatz': einsatz,
            'einstellungen': einstellungen,
            'alle_Meldungen': meldungen,
            'eingesetzte_Fahrzeuge': fahrzeuge,
            'externe_zuege': externe,
            'alle_Personen': personen,
            'fahrzeug_gesamt_zugfuehrer': 1,
            'fahrzeug_gesamt_gruppenfuehrer': 1,
            'fahrzeug_gesamt_mannschaft': 8,
            'fahrzeug_gesamt_agt': 4,
            'fahrzeug_gesamt_personal': 10,
            'dauer_tage': sekunden // 86400,
            'dauer_stunden': (sekunden % 86400) // 3600,
            'dauer_minuten': (sekunden % 3600) // 60,
            'today': timezone.now(),
        }


class PdfBuilderTests(EinsatzTestMixin, TestCase):
    """Direkte Tests des ReportLab-Builders `build_einsatz_pdf`."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    def test_erzeugt_gueltiges_pdf(self):
        pdf = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        self.assertTrue(pdf.startswith(b'%PDF'), "Ausgabe ist kein PDF")
        self.assertIn(b'%%EOF', pdf, "PDF ist nicht korrekt abgeschlossen")
        self.assertGreater(len(pdf), 1000, "PDF ist verdaechtig klein")

    def test_ohne_weasyprint_abhaengigkeit(self):
        """Der Builder darf keine nativen HTML-Renderer benoetigen."""
        import doku.pdf as pdf_modul
        self.assertFalse(hasattr(pdf_modul, 'HTML'),
                         "WeasyPrint-Import ist noch vorhanden")

    def test_laufender_einsatz_ohne_daten(self):
        """Einsatz ohne Ende, ohne Personen/Fahrzeuge/Meldungen."""
        einsatz = Einsatz.objects.create(
            Stichwort=self.stichwort, Adresse="Waldweg", Ort=self.ort_frei,
            OrtFrei="Irgendwo im Wald",
        )
        pdf = build_einsatz_pdf(self.pdf_kontext(einsatz))
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_beendeter_einsatz(self):
        self.einsatz.Ende = timezone.now()
        self.einsatz.save()
        pdf = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_sonderzeichen_und_html_werden_escaped(self):
        """Umlaute, Ampersands und HTML in Meldungen duerfen nicht crashen."""
        Meldung.objects.create(
            Inhalt='Umlaute äöüß & <script>alert("x")</script> <b>fett</b>',
            Wichtig=False, Einsatz=self.einsatz, Autor=self.user,
        )
        pdf = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_ungueltige_zugfarbe_faellt_zurueck(self):
        """Eine kaputte Farbangabe darf die PDF-Erzeugung nicht abbrechen."""
        self.zug.Farbe = "keine-farbe"
        self.zug.save()
        pdf = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_autor_ohne_namen(self):
        """Faellt auf den Benutzernamen zurueck, wenn Vor-/Nachname leer sind."""
        anonym = get_user_model().objects.create_user(username="leitstelle", password="x")
        Meldung.objects.create(Inhalt="Alarmierung erfolgt", Wichtig=False,
                               Einsatz=self.einsatz, Autor=anonym)
        pdf = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        self.assertTrue(pdf.startswith(b'%PDF'))

    def test_viele_meldungen_erzeugen_mehrere_seiten(self):
        einseitig = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        for i in range(80):
            Meldung.objects.create(
                Inhalt=f"Lagemeldung Nummer {i} mit etwas laengerem Text zur Fuellung.",
                Wichtig=(i % 10 == 0), Einsatz=self.einsatz, Autor=self.user,
            )
        mehrseitig = build_einsatz_pdf(self.pdf_kontext(self.einsatz, self.einstellungen))
        self.assertTrue(mehrseitig.startswith(b'%PDF'))
        self.assertGreater(mehrseitig.count(b'/Type /Page\n'),
                           einseitig.count(b'/Type /Page\n'),
                           "Zusaetzliche Meldungen haben keine weiteren Seiten erzeugt")

    def test_einstellungen_optional(self):
        """Der Builder muss auch ohne Einstellungen-Objekt funktionieren."""
        pdf = build_einsatz_pdf(self.pdf_kontext(self.einsatz, einstellungen=None))
        self.assertTrue(pdf.startswith(b'%PDF'))


class PdfExportViewTests(EinsatzTestMixin, TestCase):
    """Tests des HTTP-Endpunkts fuer den PDF-Export."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    def test_export_liefert_pdf(self):
        url = reverse('doku:einsatzPDFExport', args=[self.einsatz.Nummer])
        antwort = self.client.get(url)
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort['Content-Type'], 'application/pdf')
        self.assertTrue(antwort.content.startswith(b'%PDF'))

    def test_dateiname_enthaelt_einsatzdaten(self):
        url = reverse('doku:einsatzPDFExport', args=[self.einsatz.Nummer])
        antwort = self.client.get(url)
        disposition = antwort['Content-Disposition']
        self.assertIn('attachment;', disposition)
        self.assertIn(str(self.einsatz.extNummer), disposition)
        self.assertIn(self.stichwort.Kurzname, disposition)
        self.assertIn(self.ort.Kurzname, disposition)

    def test_dateiname_nutzt_interne_nummer_ohne_extnummer(self):
        self.einsatz.extNummer = None
        self.einsatz.save()
        url = reverse('doku:einsatzPDFExport', args=[self.einsatz.Nummer])
        antwort = self.client.get(url)
        self.assertIn(f'Einsatzdoku_{self.einsatz.Nummer}_', antwort['Content-Disposition'])

    def test_unbekannter_einsatz(self):
        url = reverse('doku:einsatzPDFExport', args=[999999])
        antwort = self.client.get(url)
        self.assertEqual(antwort.status_code, 500)
        self.assertIn(b'Einsatz nicht gefunden', antwort.content)


class MeldungSortierungTests(EinsatzTestMixin, TestCase):
    """Absicherung der chronologischen Reihenfolge der Meldungen."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()

    def _meldung(self, inhalt):
        return Meldung.objects.create(Inhalt=inhalt, Wichtig=False,
                                      Einsatz=self.einsatz, Autor=self.user)

    def test_standardsortierung_ist_chronologisch(self):
        erste = self._meldung("A")
        zweite = self._meldung("B")
        dritte = self._meldung("C")
        ids = list(Meldung.objects.filter(Einsatz=self.einsatz)
                   .values_list('pk', flat=True))
        self.assertEqual(ids, [erste.pk, zweite.pk, dritte.pk])

    def test_gleiche_zeitstempel_werden_ueber_pk_entschieden(self):
        erste = self._meldung("A")
        zweite = self._meldung("B")
        dritte = self._meldung("C")
        # Alle Meldungen kuenstlich auf denselben Zeitstempel setzen
        fest = timezone.now().replace(microsecond=0)
        Meldung.objects.filter(Einsatz=self.einsatz).update(Erstellt=fest)
        ids = list(Meldung.objects.filter(Einsatz=self.einsatz)
                   .values_list('pk', flat=True))
        self.assertEqual(ids, sorted([erste.pk, zweite.pk, dritte.pk]),
                         "Bei identischen Zeitstempeln fehlt der pk-Tiebreaker")

    def test_polling_api_liefert_aufsteigend(self):
        self._meldung("A")
        self._meldung("B")
        self._meldung("C")
        # Zeitstempel absichtlich verdrehen: pk-Reihenfolge != Zeit-Reihenfolge
        basis = timezone.now() - datetime.timedelta(hours=1)
        for versatz, inhalt in enumerate(["C", "A", "B"]):
            Meldung.objects.filter(Einsatz=self.einsatz, Inhalt=inhalt).update(
                Erstellt=basis + datetime.timedelta(minutes=versatz))

        url = reverse('doku:Meldung', args=[self.einsatz.Nummer])
        antwort = self.client.get(url)
        self.assertEqual(antwort.status_code, 200)

        daten = json.loads(json.loads(antwort.content))
        reihenfolge = [eintrag['fields']['Inhalt'] for eintrag in daten]
        self.assertEqual(reihenfolge, ["C", "A", "B"],
                         "Polling-API liefert nicht nach Erstellt sortiert")

    def test_polling_api_beachtet_lastid(self):
        erste = self._meldung("A")
        zweite = self._meldung("B")
        url = reverse('doku:Meldung', args=[self.einsatz.Nummer])
        antwort = self.client.get(url, {'lastID': erste.pk})

        daten = json.loads(json.loads(antwort.content))
        self.assertEqual([e['pk'] for e in daten], [zweite.pk])

    def test_einsatzansicht_sortiert_absteigend(self):
        erste = self._meldung("A")
        zweite = self._meldung("B")
        url = reverse('doku:einsatz', args=[self.einsatz.Nummer])
        antwort = self.client.get(url)
        self.assertEqual(antwort.status_code, 200)
        ids = [m.pk for m in antwort.context['alle_Meldungen']]
        self.assertEqual(ids, [zweite.pk, erste.pk],
                         "Einsatzansicht muss neueste Meldung zuerst liefern")


class ModellTests(EinsatzTestMixin, TestCase):
    """Tests der Hilfsmethoden auf den Modellen."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    # --- Einsatz ---------------------------------------------------------
    def test_einsatz_str(self):
        self.assertEqual(
            str(self.einsatz),
            f"{self.einsatz.Nummer}_{self.stichwort.Kurzname}_{self.ort.Kurzname}")

    def test_einsatz_getyear(self):
        erwartet = timezone.localtime(self.einsatz.Erstellt).strftime('%Y')
        self.assertEqual(self.einsatz.getYear(), erwartet)

    def test_einsatz_dauer_bei_beendetem_einsatz(self):
        self.einsatz.Ende = self.einsatz.Erstellt + datetime.timedelta(hours=2, minutes=30)
        self.einsatz.save()
        self.assertEqual(self.einsatz.getDuration(), datetime.timedelta(hours=2, minutes=30))

    def test_einsatz_dauer_bei_laufendem_einsatz(self):
        self.einsatz.Ende = None
        self.einsatz.save()
        self.assertGreaterEqual(self.einsatz.getDuration().total_seconds(), 0)

    def test_maps_adresse_mit_ort(self):
        self.einsatz.OrtFrei = None
        self.assertEqual(self.einsatz.getMapsCompatibleAdress(),
                         "Hauptstraße 1, Musterstadt")

    def test_maps_adresse_mit_freitext(self):
        self.einsatz.OrtFrei = "Irgendwo im Wald"
        self.assertEqual(self.einsatz.getMapsCompatibleAdress(),
                         "Hauptstraße 1, Irgendwo im Wald")

    # --- Meldung ---------------------------------------------------------
    def test_meldung_zeit_heute_ohne_datum(self):
        text = self.meldung_normal.getTimeOrDate()
        self.assertRegex(text, r'^\d{2}:\d{2}$',
                         "Heutige Meldungen duerfen nur die Uhrzeit zeigen")

    def test_meldung_zeit_aeltere_mit_datum(self):
        gestern = timezone.now() - datetime.timedelta(days=3)
        Meldung.objects.filter(pk=self.meldung_normal.pk).update(Erstellt=gestern)
        self.meldung_normal.refresh_from_db()
        text = self.meldung_normal.getTimeOrDate()
        self.assertIn(gestern.astimezone().strftime('%Y'), text)
        self.assertNotRegex(text, r'^\d{2}:\d{2}$')

    def test_meldung_str_enthaelt_autor(self):
        self.assertIn(self.user.username, str(self.meldung_normal))

    # --- Fahrzeug / ZugExtra --------------------------------------------
    def test_fahrzeug_str_zeigt_staerke(self):
        self.assertIn("0/1/5", str(self.fahrzeug))
        self.assertIn("4 AGT", str(self.fahrzeug))

    def test_zugextra_str_zeigt_staerke(self):
        self.assertIn("1/0/3", str(self.zug_extra))

    def test_fahrzeuge_str(self):
        self.assertEqual(str(self.fahrzeugtyp), "MST 1/44 HLF 20 Musterstadt")

    # --- Einsatzstellen / Einheiten --------------------------------------
    def test_einsatzstelle_str_mit_ort(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        self.assertEqual(str(stelle), "Keller, Musterstadt")

    def test_einsatzstelle_str_mit_freitext(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort_frei, OrtFrei="Waldrand", Name="Baum")
        self.assertEqual(str(stelle), "Baum, Waldrand")

    def test_einheit_zaehlt_nur_offene_einsatzstellen(self):
        einheit = Einheiten.objects.create(Einsatz=self.einsatz, Name="Löschzug A")
        Einsatzstellen.objects.create(Einsatz=self.einsatz, Ort=self.ort,
                                      Name="Offen 1", Einheit=einheit)
        Einsatzstellen.objects.create(Einsatz=self.einsatz, Ort=self.ort,
                                      Name="Offen 2", Einheit=einheit)
        Einsatzstellen.objects.create(Einsatz=self.einsatz, Ort=self.ort,
                                      Name="Fertig", Einheit=einheit,
                                      Abgeschlossen=timezone.now())
        self.assertEqual(einheit.getAnzahlEinsatzstellen(), 2)

    def test_notiz_mehrzeilig_wird_zu_br(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        notiz = Einsatzstellen_Notizen.objects.create(
            Einsatz=self.einsatz, Einsatzstelle=stelle, Notiz="Zeile 1\nZeile 2")
        self.assertEqual(notiz.get_html_multiline(), "Zeile 1<br>Zeile 2")

    # --- Einstellungen (Singleton) ---------------------------------------
    def test_einstellungen_sind_singleton(self):
        zweite = Einstellungen(Name="Zweite Instanz")
        zweite.save()
        self.assertEqual(Einstellungen.objects.count(), 1)
        self.assertEqual(zweite.pk, 1)
        self.assertEqual(Einstellungen.objects.get().Name, "Zweite Instanz")

    def test_einstellungen_lassen_sich_nicht_loeschen(self):
        Einstellungen.load().delete()
        self.assertEqual(Einstellungen.objects.count(), 1)

    def test_einstellungen_load_erzeugt_objekt(self):
        Einstellungen.objects.all().delete()
        self.assertEqual(Einstellungen.load().pk, 1)

    # --- Profile-Signal ---------------------------------------------------
    def test_profil_wird_automatisch_angelegt(self):
        neuer = get_user_model().objects.create_user(username="neuling", password="x")
        self.assertTrue(Profile.objects.filter(user=neuer).exists())
        self.assertTrue(neuer.profile.nightmode)


class UebersichtsViewTests(EinsatzTestMixin, TestCase):
    """Tests der Index-, Einsatz- und JSON-Ansichten."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    def test_index_erreichbar(self):
        antwort = self.client.get(reverse('doku:index'))
        self.assertEqual(antwort.status_code, 200)
        self.assertFalse(antwort.context['training'])
        self.assertIn(self.einsatz, list(antwort.context['alle_Einsaetze']))

    def test_index_legt_freitext_ort_an(self):
        Ort.objects.filter(PLZ=0).delete()
        self.client.get(reverse('doku:index'))
        self.assertTrue(Ort.objects.filter(PLZ=0, Kurzname="ZZZ").exists())

    def test_index_first_run_ist_false_bei_vorhandenen_benutzern(self):
        antwort = self.client.get(reverse('doku:index'))
        self.assertFalse(antwort.context['first_run'])

    def test_index_training_zeigt_nur_trainings(self):
        training = Einsatz.objects.create(
            Stichwort=self.stichwort, Adresse="Übungsplatz", Ort=self.ort, Training=True)
        antwort = self.client.get(reverse('doku:index_training'))
        self.assertEqual(antwort.status_code, 200)
        self.assertTrue(antwort.context['training'])
        einsaetze = list(antwort.context['alle_Einsaetze'])
        self.assertIn(training, einsaetze)
        self.assertNotIn(self.einsatz, einsaetze)

    def test_index_listet_jahre_beendeter_einsaetze(self):
        self.einsatz.Ende = timezone.now()
        self.einsatz.save()
        antwort = self.client.get(reverse('doku:index'))
        self.assertIn(self.einsatz.getYear(), antwort.context['jahre'])

    def test_einsatzansicht_erreichbar(self):
        antwort = self.client.get(reverse('doku:einsatz', args=[self.einsatz.Nummer]))
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.context['einsatz'], self.einsatz)
        self.assertFalse(antwort.context['auto_pdf_export'])

    def test_einsatzansicht_auto_pdf_flag(self):
        antwort = self.client.get(reverse('doku:einsatz', args=[self.einsatz.Nummer]),
                                  {'auto_pdf': '1'})
        self.assertTrue(antwort.context['auto_pdf_export'])

    def test_alle_einsaetze_json(self):
        antwort = self.client.get(reverse('doku:alleEinsaetze'))
        daten = json.loads(json.loads(antwort.content))
        self.assertIn(self.einsatz.Nummer, [e['pk'] for e in daten])

    def test_alle_trainings_json(self):
        Einsatz.objects.create(Stichwort=self.stichwort, Adresse="Platz",
                               Ort=self.ort, Training=True)
        antwort = self.client.get(reverse('doku:alleTrainingsEinsaetze'))
        daten = json.loads(json.loads(antwort.content))
        self.assertEqual(len(daten), 1)

    def test_get_ort(self):
        antwort = self.client.get(reverse('doku:getOrt', args=[self.ort.PLZ]))
        daten = json.loads(json.loads(antwort.content))
        self.assertEqual(daten[0]['fields']['Langname'], "Musterstadt")

    def test_get_stichwort(self):
        antwort = self.client.get(reverse('doku:getStichwort', args=[self.stichwort.pk]))
        daten = json.loads(json.loads(antwort.content))
        self.assertEqual(daten[0]['pk'], "B3")

    def test_get_zug(self):
        antwort = self.client.get(reverse('doku:getZug', args=[self.zug.pk]))
        daten = json.loads(json.loads(antwort.content))
        self.assertEqual(daten[0]['fields']['Farbe'], "#ffcc00")

    def test_get_ort_unbekannt(self):
        self.assertEqual(self.client.get(reverse('doku:getOrt', args=[99999])).status_code, 404)

    def test_summe_personal(self):
        antwort = self.client.get(reverse('doku:summePersonal', args=[self.einsatz.Nummer]))
        summe = json.loads(json.loads(antwort.content))
        self.assertEqual(summe['Gesamt'], {
            'zugfuehrer': 1, 'gruppenfuehrer': 1, 'mannschaft': 8, 'atemschutz': 4})
        self.assertEqual(summe[self.zug.Name]['mannschaft'], 5)
        self.assertEqual(summe[self.zug_extra.Name]['mannschaft'], 3)

    def test_get_icons_liefert_sortierte_liste(self):
        icons = get_icons()
        self.assertIsInstance(icons, list)
        for icon in icons:
            self.assertIn('path', icon)
            self.assertIn('name', icon)
            self.assertIn('order', icon)
        reihenfolge = [(i['order'], i['name']) for i in icons]
        self.assertEqual(reihenfolge, sorted(reihenfolge))


class BerechtigungsTests(EinsatzTestMixin, TestCase):
    """Alle schreibenden Views muessen einen angemeldeten Benutzer verlangen."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    def test_schreibende_views_ohne_login_verboten(self):
        nr = self.einsatz.Nummer
        endpunkte = [
            reverse('doku:neuerEinsatz'),
            reverse('doku:neuesTraining'),
            reverse('doku:einsatznummer', args=[nr]),
            reverse('doku:einsatzleiter', args=[nr]),
            reverse('doku:adresse', args=[nr]),
            reverse('doku:neueMeldung', args=[nr]),
            reverse('doku:neuePerson', args=[nr]),
            reverse('doku:neuesFahrzeug', args=[nr]),
            reverse('doku:neuerZug', args=[nr]),
            reverse('doku:einsatzende', args=[nr]),
        ]
        for url in endpunkte:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_oel_ohne_login_verboten(self):
        antwort = self.client.post(reverse('doku:oel', args=[self.einsatz.Nummer]), {})
        self.assertEqual(antwort.status_code, 403)

    def test_oel_notiz_ohne_login_verboten(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        antwort = self.client.post(
            reverse('doku:neueNotiz', args=[self.einsatz.Nummer, stelle.pk]),
            {'Notiz': "Test"})
        self.assertEqual(antwort.status_code, 403)
        self.assertEqual(Einsatzstellen_Notizen.objects.count(), 0)


class SchreibendeViewTests(EinsatzTestMixin, TestCase):
    """Tests der Views, die Daten anlegen oder aendern (angemeldet)."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()

    def setUp(self):
        self.client.force_login(self.user)

    def test_neuer_einsatz(self):
        antwort = self.client.post(reverse('doku:neuerEinsatz'), {
            'Ort': self.ort.Kurzname, 'Stichwort': self.stichwort.Kurzname,
            'Adresse': "Bahnhofstraße 5",
        })
        neuer = Einsatz.objects.exclude(pk=self.einsatz.pk).get()
        self.assertRedirects(antwort, reverse('doku:einsatz', args=[neuer.pk]),
                             fetch_redirect_response=False)
        self.assertFalse(neuer.Training)
        self.assertEqual(neuer.Adresse, "Bahnhofstraße 5")

    def test_neues_training(self):
        self.client.post(reverse('doku:neuesTraining'), {
            'Ort': self.ort.Kurzname, 'Stichwort': self.stichwort.Kurzname,
            'Adresse': "Übungsplatz",
        })
        neuer = Einsatz.objects.exclude(pk=self.einsatz.pk).get()
        self.assertTrue(neuer.Training)

    def test_neuer_einsatz_mit_unvollstaendigen_daten(self):
        antwort = self.client.post(reverse('doku:neuerEinsatz'), {'Ort': self.ort.Kurzname})
        self.assertIn(b'Fehler bei der Verarbeitung', antwort.content)
        self.assertEqual(Einsatz.objects.count(), 1)

    def test_einsatznummer_setzen(self):
        antwort = self.client.post(
            reverse('doku:einsatznummer', args=[self.einsatz.Nummer]), {'extENr': '2026042'})
        self.assertEqual(antwort.status_code, 200)
        self.einsatz.refresh_from_db()
        self.assertEqual(self.einsatz.extNummer, 2026042)

    def test_einsatznummer_ungueltig(self):
        antwort = self.client.post(
            reverse('doku:einsatznummer', args=[self.einsatz.Nummer]), {'extENr': 'abc'})
        self.assertEqual(antwort.status_code, 500)

    def test_einsatzleiter_setzen(self):
        self.client.post(reverse('doku:einsatzleiter', args=[self.einsatz.Nummer]),
                         {'einsatzleiter': "Schmidt, Anna"})
        self.einsatz.refresh_from_db()
        self.assertEqual(self.einsatz.Einsatzleiter, "Schmidt, Anna")

    def test_adresse_setzen(self):
        self.client.post(reverse('doku:adresse', args=[self.einsatz.Nummer]),
                         {'adresse': "Neue Straße 9"})
        self.einsatz.refresh_from_db()
        self.assertEqual(self.einsatz.Adresse, "Neue Straße 9")

    # --- Meldungen -------------------------------------------------------
    def test_neue_meldung(self):
        self.client.post(reverse('doku:neueMeldung', args=[self.einsatz.Nummer]),
                         {'Inhalt': "Lage erkundet"})
        meldung = Meldung.objects.get()
        self.assertEqual(meldung.Inhalt, "Lage erkundet")
        self.assertEqual(meldung.Autor, self.user)
        self.assertFalse(meldung.Wichtig)
        self.assertIsNone(meldung.Zug)

    def test_neue_meldung_wichtig_mit_zug(self):
        self.client.post(reverse('doku:neueMeldung', args=[self.einsatz.Nummer]), {
            'Inhalt': "Wasser marsch", 'Wichtig': 'on', 'Zug': f"{self.zug.Name}: ",
        })
        meldung = Meldung.objects.get()
        self.assertTrue(meldung.Wichtig)
        self.assertEqual(meldung.Zug, self.zug)
        self.assertEqual(meldung.Inhalt, f"{self.zug.Name}: Wasser marsch")

    def test_keine_meldung_nach_einsatzende(self):
        self.einsatz.Ende = timezone.now()
        self.einsatz.save()
        antwort = self.client.post(
            reverse('doku:neueMeldung', args=[self.einsatz.Nummer]), {'Inhalt': "Zu spät"})
        self.assertEqual(antwort.status_code, 403)
        self.assertEqual(Meldung.objects.count(), 0)

    # --- Personen --------------------------------------------------------
    def test_neue_person(self):
        self.client.post(reverse('doku:neuePerson', args=[self.einsatz.Nummer]), {
            'Nachname': "Schmidt", 'Vorname': "Anna",
            'Rolle': "Eigentümerin", 'Notizen': "unverletzt",
        })
        person = Person.objects.get()
        self.assertEqual(person.Nachname, "Schmidt")

    def test_person_wird_aktualisiert_statt_dupliziert(self):
        daten = {'Nachname': "Schmidt", 'Vorname': "Anna",
                 'Rolle': "Eigentümerin", 'Notizen': "unverletzt"}
        self.client.post(reverse('doku:neuePerson', args=[self.einsatz.Nummer]), daten)
        daten['Notizen'] = "an Rettungsdienst übergeben"
        self.client.post(reverse('doku:neuePerson', args=[self.einsatz.Nummer]), daten)
        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Person.objects.get().Notizen, "an Rettungsdienst übergeben")

    # --- Fahrzeuge -------------------------------------------------------
    def test_neues_fahrzeug(self):
        fahrzeugtyp = Fahrzeuge.objects.create(
            Funkname="MST 1/44", Ort=self.ort, Typ="HLF 20", Zug=self.zug)
        self.client.post(reverse('doku:neuesFahrzeug', args=[self.einsatz.Nummer]), {
            'Name': fahrzeugtyp.pk, 'Besatzung': "0/1/5", 'Atemschutz': "4",
        })
        fahrzeug = Fahrzeug.objects.get()
        self.assertEqual((fahrzeug.Zugfuehrer, fahrzeug.Gruppenfuehrer,
                          fahrzeug.Mannschaft, fahrzeug.Atemschutz), (0, 1, 5, 4))

    def test_fahrzeug_wird_aktualisiert_statt_dupliziert(self):
        fahrzeugtyp = Fahrzeuge.objects.create(
            Funkname="MST 1/44", Ort=self.ort, Typ="HLF 20", Zug=self.zug)
        url = reverse('doku:neuesFahrzeug', args=[self.einsatz.Nummer])
        self.client.post(url, {'Name': fahrzeugtyp.pk, 'Besatzung': "0/1/5", 'Atemschutz': "4"})
        self.client.post(url, {'Name': fahrzeugtyp.pk, 'Besatzung': "0/1/8", 'Atemschutz': ""})
        self.assertEqual(Fahrzeug.objects.count(), 1)
        fahrzeug = Fahrzeug.objects.get()
        self.assertEqual(fahrzeug.Mannschaft, 8)
        self.assertEqual(fahrzeug.Atemschutz, 0, "Leeres AGT-Feld muss zu 0 werden")

    def test_fahrzeug_mit_ungueltiger_besatzung(self):
        fahrzeugtyp = Fahrzeuge.objects.create(
            Funkname="MST 1/44", Ort=self.ort, Typ="HLF 20", Zug=self.zug)
        antwort = self.client.post(reverse('doku:neuesFahrzeug', args=[self.einsatz.Nummer]),
                                   {'Name': fahrzeugtyp.pk, 'Besatzung': "kaputt"})
        self.assertIn(b'Fehler bei der Verarbeitung', antwort.content)
        self.assertEqual(Fahrzeug.objects.count(), 0)

    # --- Externe Zuege ---------------------------------------------------
    def test_externen_zug_anlegen_und_aktualisieren(self):
        url = reverse('doku:neuerZug', args=[self.einsatz.Nummer])
        self.client.post(url, {'Name': "Rettungsdienst", 'Besatzung': "1/0/3", 'Atemschutz': "0"})
        self.client.post(url, {'Name': "Rettungsdienst", 'Besatzung': "1/1/6", 'Atemschutz': "2"})
        self.assertEqual(ZugExtra.objects.count(), 1)
        zug = ZugExtra.objects.get()
        self.assertEqual((zug.Gruppenfuehrer, zug.Mannschaft, zug.Atemschutz), (1, 6, 2))

    # --- Einsatzende -----------------------------------------------------
    def test_einsatzende_setzt_zeitstempel_und_leitet_zum_pdf(self):
        antwort = self.client.post(reverse('doku:einsatzende', args=[self.einsatz.Nummer]))
        self.einsatz.refresh_from_db()
        self.assertIsNotNone(self.einsatz.Ende)
        self.assertEqual(
            antwort['Location'],
            reverse('doku:einsatz', args=[self.einsatz.Nummer]) + '?auto_pdf=1')

    # --- Nachtmodus ------------------------------------------------------
    def test_nachtmodus_umschalten(self):
        ausgangswert = self.user.profile.nightmode
        self.client.get(reverse('doku:toggleNightmode'), HTTP_REFERER='/')
        self.user.profile.refresh_from_db()
        self.assertNotEqual(self.user.profile.nightmode, ausgangswert)


class OelViewTests(EinsatzTestMixin, TestCase):
    """Tests der Ansicht fuer die oertliche Einsatzleitung."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('doku:oel', args=[self.einsatz.Nummer])

    def test_get_liefert_uebersicht(self):
        antwort = self.client.get(self.url)
        self.assertEqual(antwort.status_code, 200)
        self.assertIsNone(antwort.context['error'])

    def test_unerlaubte_methode(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)

    def test_neue_einsatzstelle_mit_notiz_und_meldung(self):
        antwort = self.client.post(self.url, {
            'neueEinsatzstelle': '1', 'Name': "Keller 1",
            'Ort': self.ort.Kurzname, 'Anmerkungen': "Wasser im Keller",
        })
        self.assertIsNone(antwort.context['error'])
        stelle = Einsatzstellen.objects.get()
        self.assertEqual(stelle.Name, "Keller 1")
        self.assertEqual(Einsatzstellen_Notizen.objects.count(), 1)
        self.assertIn("Neue Einsatzstelle", Meldung.objects.get().Inhalt)

    def test_neue_einsatzstelle_mit_freitextort(self):
        antwort = self.client.post(self.url, {
            'neueEinsatzstelle': '1', 'Name': "Baum auf Weg",
            'Ort': self.ort_frei.Kurzname, 'Freitext': "Waldrand",
        })
        self.assertIsNone(antwort.context['error'])
        self.assertEqual(Einsatzstellen.objects.get().OrtFrei, "Waldrand")

    def test_freitextort_ohne_freitext_meldet_fehler(self):
        antwort = self.client.post(self.url, {
            'neueEinsatzstelle': '1', 'Name': "Baum", 'Ort': self.ort_frei.Kurzname,
        })
        self.assertIn("Freitext", antwort.context['error'])
        self.assertEqual(Einsatzstellen.objects.count(), 0)

    def test_einsatzstelle_ohne_namen_meldet_fehler(self):
        antwort = self.client.post(self.url, {})
        self.assertIn("Name", antwort.context['error'])

    def test_einsatzstelle_ohne_ort_meldet_fehler(self):
        antwort = self.client.post(self.url, {'neueEinsatzstelle': '1', 'Name': "Keller"})
        self.assertIn("Ort", antwort.context['error'])

    def test_einheit_anlegen(self):
        antwort = self.client.post(self.url, {'Name': "Löschzug A"})
        self.assertIsNone(antwort.context['error'])
        self.assertEqual(Einheiten.objects.get().Name, "Löschzug A")

    def test_einheit_wird_nicht_dupliziert(self):
        self.client.post(self.url, {'Name': "Löschzug A"})
        self.client.post(self.url, {'Name': "Löschzug A"})
        self.assertEqual(Einheiten.objects.count(), 1)

    def test_einsatzstelle_zuweisen_und_abschliessen(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        einheit = Einheiten.objects.create(Einsatz=self.einsatz, Name="Löschzug A")

        self.client.post(self.url, {'Einsatzstelle': stelle.pk, 'Einheit': einheit.pk})
        stelle.refresh_from_db()
        self.assertEqual(stelle.Einheit, einheit)
        self.assertIsNotNone(stelle.Zugewiesen)
        self.assertIn("übernommen", Meldung.objects.first().Inhalt)

        self.client.post(self.url, {'Einsatzstelle': stelle.pk, 'DONE': '1'})
        stelle.refresh_from_db()
        self.assertIsNotNone(stelle.Abgeschlossen)
        self.assertIn("abgearbeitet", Meldung.objects.last().Inhalt)

    def test_notiz_zu_einsatzstelle_anlegen(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        url = reverse('doku:neueNotiz', args=[self.einsatz.Nummer, stelle.pk])
        antwort = self.client.post(url, {'Notiz': "Pumpe läuft"})
        self.assertRedirects(antwort, self.url, fetch_redirect_response=False)
        self.assertEqual(Einsatzstellen_Notizen.objects.get().Notiz, "Pumpe läuft")

    def test_leere_notiz_wird_nicht_gespeichert(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        url = reverse('doku:neueNotiz', args=[self.einsatz.Nummer, stelle.pk])
        self.client.post(url, {'Notiz': "   "})
        self.assertEqual(Einsatzstellen_Notizen.objects.count(), 0)

    def test_notiz_wird_escaped(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        url = reverse('doku:neueNotiz', args=[self.einsatz.Nummer, stelle.pk])
        self.client.post(url, {'Notiz': '<script>alert("x")</script>'})
        self.assertNotIn("<script>", Einsatzstellen_Notizen.objects.get().Notiz)

    def test_notiz_per_get_legt_nichts_an(self):
        stelle = Einsatzstellen.objects.create(
            Einsatz=self.einsatz, Ort=self.ort, Name="Keller")
        url = reverse('doku:neueNotiz', args=[self.einsatz.Nummer, stelle.pk])
        antwort = self.client.get(url)
        self.assertEqual(antwort.status_code, 302)
        self.assertEqual(Einsatzstellen_Notizen.objects.count(), 0)


class ErstanmeldungTests(TestCase):
    """Tests fuer die Ersteinrichtung ohne vorhandene Benutzer."""

    def setUp(self):
        Stichwort.objects.create(Kurzname="B1", Langname="Kleinbrand")
        Ort.objects.create(PLZ=12345, Kurzname="MST", Langname="Musterstadt")

    def test_index_meldet_first_run(self):
        antwort = self.client.get(reverse('doku:index'))
        self.assertTrue(antwort.context['first_run'])

    def test_erster_benutzer_wird_superuser(self):
        antwort = self.client.post(reverse('doku:neuerBenutzer'),
                                   {'username': "Admin", 'password': "geheim"})
        self.assertRedirects(antwort, reverse('doku:index'))
        benutzer = get_user_model().objects.get()
        self.assertEqual(benutzer.username, "admin", "Benutzername muss klein sein")
        self.assertTrue(benutzer.is_superuser)
        self.assertTrue(benutzer.is_staff)

    def test_zweiter_benutzer_wird_abgelehnt(self):
        get_user_model().objects.create_user(username="vorhanden", password="x")
        antwort = self.client.post(reverse('doku:neuerBenutzer'),
                                   {'username': "hacker", 'password': "x"})
        self.assertEqual(antwort.status_code, 403)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_benutzeranlage_nur_per_post(self):
        self.assertEqual(self.client.get(reverse('doku:neuerBenutzer')).status_code, 403)


class FormularTests(TestCase):
    """Tests der Admin-Formulare."""

    def test_zugform_nutzt_farbwaehler(self):
        self.assertIn('type="color"', str(ZugForm()['Farbe']))

    def test_ortform_nutzt_farbwaehler(self):
        self.assertIn('type="color"', str(OrtForm()['Farbe']))

    def test_zugform_gueltig(self):
        self.assertTrue(ZugForm(data={'Name': "Zug 1", 'Farbe': "#ff0000"}).is_valid())

    def test_zugform_ohne_namen_ungueltig(self):
        self.assertFalse(ZugForm(data={'Name': "", 'Farbe': "#ff0000"}).is_valid())

    def test_ortform_plz_grenzwerte(self):
        gueltig = OrtForm(data={'PLZ': 99999, 'Kurzname': "XYZ",
                                'Langname': "Grenzfall", 'Farbe': "#ffffff"})
        self.assertTrue(gueltig.is_valid())
        ungueltig = OrtForm(data={'PLZ': 100000, 'Kurzname': "XYZ",
                                  'Langname': "Zu gross", 'Farbe': "#ffffff"})
        self.assertFalse(ungueltig.is_valid())


class RevisionTests(EinsatzTestMixin, TestCase):
    """Der Revisionszaehler ist die Grundlage der Geraete-Synchronisation."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    def test_neue_meldung_erhoeht_version(self):
        vorher = EinsatzRevision.get_version(self.einsatz.pk)
        Meldung.objects.create(Inhalt="Nachtrag", Wichtig=False,
                               Einsatz=self.einsatz, Autor=self.user)
        self.assertGreater(EinsatzRevision.get_version(self.einsatz.pk), vorher)

    def test_loeschen_erhoeht_version(self):
        meldung = Meldung.objects.create(Inhalt="Irrtum", Wichtig=False,
                                         Einsatz=self.einsatz, Autor=self.user)
        vorher = EinsatzRevision.get_version(self.einsatz.pk)
        meldung.delete()
        self.assertGreater(EinsatzRevision.get_version(self.einsatz.pk), vorher)

    def test_aenderung_wirkt_nur_auf_eigenen_einsatz(self):
        anderer = Einsatz.objects.create(Stichwort=self.stichwort, Adresse="Nebenweg 2",
                                         Ort=self.ort)
        vorher = EinsatzRevision.get_version(anderer.pk)
        Meldung.objects.create(Inhalt="Nur hier", Wichtig=False,
                               Einsatz=self.einsatz, Autor=self.user)
        self.assertEqual(EinsatzRevision.get_version(anderer.pk), vorher)

    def test_unbekannter_einsatz_hat_version_null(self):
        self.assertEqual(EinsatzRevision.get_version(999999), 0)


class EinsatzStateTests(EinsatzTestMixin, TestCase):
    """Snapshot-Endpunkt: alle Geraete erhalten denselben Zustand."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()
        cls.einsatz_befuellen()

    def snapshot(self):
        antwort = self.client.get(reverse('doku:einsatzState', args=[self.einsatz.Nummer]))
        self.assertEqual(antwort.status_code, 200)
        return json.loads(antwort.content)

    def test_snapshot_enthaelt_alle_bereiche(self):
        daten = self.snapshot()
        for schluessel in ('version', 'einsatz', 'meldungen', 'fahrzeuge',
                           'zuege_extra', 'staerken', 'personen', 'einsatzstellen'):
            self.assertIn(schluessel, daten)
        self.assertEqual(daten['einsatz']['Einsatzleiter'], "Müller, Max")
        self.assertEqual(len(daten['meldungen']), 2)
        self.assertEqual(len(daten['fahrzeuge']), 1)
        self.assertEqual(len(daten['personen']), 1)

    def test_meldungen_absteigend_sortiert(self):
        meldungen = self.snapshot()['meldungen']
        self.assertEqual(meldungen, sorted(meldungen,
                                           key=lambda m: (m['Erstellt'], m['pk']),
                                           reverse=True))

    def test_staerken_enthalten_gesamtsumme(self):
        gesamt = self.snapshot()['staerken']['Gesamt']
        self.assertEqual(gesamt['zugfuehrer'], 1)
        self.assertEqual(gesamt['gruppenfuehrer'], 1)
        self.assertEqual(gesamt['mannschaft'], 8)
        self.assertEqual(gesamt['atemschutz'], 4)

    def test_version_steigt_nach_aenderung(self):
        vorher = self.snapshot()['version']
        Meldung.objects.create(Inhalt="Weitere Lage", Wichtig=False,
                               Einsatz=self.einsatz, Autor=self.user)
        self.assertGreater(self.snapshot()['version'], vorher)

    def test_unbekannter_einsatz_liefert_404(self):
        antwort = self.client.get(reverse('doku:einsatzState', args=[999999]))
        self.assertEqual(antwort.status_code, 404)


class LeseansichtOhneLoginTests(EinsatzTestMixin, TestCase):
    """Auch ohne Anmeldung muessen die Grunddaten lesbar sein."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()

    def html(self):
        antwort = self.client.get(reverse('doku:einsatz', args=[self.einsatz.Nummer]))
        self.assertEqual(antwort.status_code, 200)
        return antwort.content.decode()

    def test_grunddaten_sind_ohne_login_sichtbar(self):
        inhalt = self.html()
        self.assertIn(str(self.einsatz.extNummer), inhalt)
        self.assertIn("Müller, Max", inhalt)
        self.assertIn("Hauptstraße 1", inhalt)

    def test_keine_eingabefelder_ohne_login(self):
        inhalt = self.html()
        self.assertNotIn('name="extENr"', inhalt)
        self.assertNotIn('name="einsatzleiter"', inhalt)
        self.assertNotIn('name="adresse"', inhalt)

    def test_platzhalter_bei_leeren_feldern(self):
        self.einsatz.Einsatzleiter = ""
        self.einsatz.extNummer = None
        self.einsatz.save()
        inhalt = self.html()
        self.assertIn("Kein Einsatzleiter eingetragen!", inhalt)
        self.assertIn('data-live-text="extNummer"', inhalt)

    def test_felder_sind_fuer_live_update_markiert(self):
        inhalt = self.html()
        for feld in ('extNummer', 'Einsatzleiter', 'Adresse'):
            self.assertIn(f'data-live-text="{feld}"', inhalt)


class EinsatzEventsTests(EinsatzTestMixin, TestCase):
    """Der SSE-Stream muss als Event-Stream ohne Pufferung ausgeliefert werden."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()

    def test_kopfzeilen_fuer_server_sent_events(self):
        antwort = self.client.get(reverse('doku:einsatzEvents', args=[self.einsatz.Nummer]))
        try:
            self.assertEqual(antwort['Content-Type'], 'text/event-stream')
            self.assertIn('no-cache', antwort['Cache-Control'])
            self.assertEqual(antwort['X-Accel-Buffering'], 'no')
        finally:
            antwort.close()


class LiveFormularTests(EinsatzTestMixin, TestCase):
    """Schreibzugriffe antworten fetch-Clients mit JSON statt Redirect."""

    @classmethod
    def setUpTestData(cls):
        cls.basisdaten()

    def setUp(self):
        self.client.force_login(self.user)

    def fetch_post(self, url, daten):
        return self.client.post(url, daten, HTTP_X_REQUESTED_WITH='fetch',
                                HTTP_ACCEPT='application/json')

    def test_neue_meldung_liefert_json_mit_version(self):
        antwort = self.fetch_post(reverse('doku:neueMeldung', args=[self.einsatz.Nummer]),
                                  {'Inhalt': "Lagemeldung", 'Zug': ""})
        self.assertEqual(antwort.status_code, 200)
        daten = json.loads(antwort.content)
        self.assertTrue(daten['ok'])
        self.assertEqual(daten['version'], EinsatzRevision.get_version(self.einsatz.Nummer))
        self.assertTrue(Meldung.objects.filter(Inhalt="Lagemeldung").exists())

    def test_klassisches_formular_bleibt_redirect(self):
        antwort = self.client.post(reverse('doku:neueMeldung', args=[self.einsatz.Nummer]),
                                   {'Inhalt': "Ohne fetch", 'Zug': ""})
        self.assertRedirects(antwort, reverse('doku:einsatz', args=[self.einsatz.Nummer]))

    def test_fehlerhafte_eingabe_liefert_fehlertext(self):
        antwort = self.fetch_post(reverse('doku:neuerZug', args=[self.einsatz.Nummer]),
                                  {'Name': "Extern", 'Besatzung': "kaputt"})
        self.assertEqual(antwort.status_code, 400)
        daten = json.loads(antwort.content)
        self.assertFalse(daten['ok'])
        self.assertIn('error', daten)

    def test_einsatzende_liefert_weiterleitungsziel(self):
        antwort = self.fetch_post(reverse('doku:einsatzende', args=[self.einsatz.Nummer]),
                                  {'sicher': "on"})
        self.assertEqual(antwort.status_code, 200)
        daten = json.loads(antwort.content)
        self.assertTrue(daten['ok'])
        self.assertIn('auto_pdf=1', daten['redirect'])
        self.einsatz.refresh_from_db()
        self.assertIsNotNone(self.einsatz.Ende)
