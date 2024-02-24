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
