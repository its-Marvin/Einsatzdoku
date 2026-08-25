# Einsatzdoku
Browserbasierte Einsatzdokumentation für Einsatzleitwagen der Feuerwehren



Core-Features:
-
 - Einsätze mit Ort und Stichwort anlegen
 - Meldungen mit Zeitstempel und Verfasser anlegen
    - nachträglich keine Änderungen möglich
 - Beteiligte Personen erfassen
 - Eingesetzte Fahrzeuge
   - inkl. Stärkemeldung und Aufteilung in Züge
 - getrennter Trainingsmodus
 - Großschadenslagen/ÖEL
   - viele kleine Einsätze übersichtlich erfassen und Einheiten zuordnen
 - Live-Synchronisation über alle Geräte
   - alle geöffneten Browser zeigen denselben Einsatzzustand
   - Push per Server-Sent-Events, ohne zusätzliche Infrastruktur (kein Redis nötig)
   - automatischer Rückfall auf Polling, wenn die Verbindung abreißt


Live-Synchronisation (technisch):
-
 - Jede Änderung an einem Einsatz erhöht einen Revisionszähler (`EinsatzRevision`).
 - `/<einsatz_id>/events` liefert per SSE nur die neue Versionsnummer.
 - `/<einsatz_id>/state` liefert daraufhin den kompletten Einsatzzustand als JSON
   (Grunddaten, Meldungen, Fahrzeuge, Stärken, Personen, Einsatzstellen).
 - Der Browser rendert daraus die Ansicht neu; Formulare werden per `fetch`
   abgeschickt, ein Seiten-Reload ist nicht mehr nötig.
 - Voraussetzung ist der ASGI-Betrieb (Daphne), der im Container bereits genutzt wird.


Installation:
-
1. compose.yml Datei kopieren und anpassen
    - Alle CHANGEME Einträge durch sichere Passwörter ersetzen!
    - Wenn aus dem Internet verfügbar: HTTPS verwenden
2. Container mit 'docker compose up' starten
3. IP/Domain des Servers im Browser aufrufen
4. Im Adminbereich (/admin) können nun Orte, Züge, Fahrzeuge und Benutzer gepflegt werden

Basierend auf Python Django


Lizenz: MIT
