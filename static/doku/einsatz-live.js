'use strict';
/*
 * Rendert die veraenderlichen Bereiche der Einsatzansicht aus dem zentralen
 * Zustand (state-store.js) und verschickt Formulare per fetch, damit kein
 * Seiten-Reload noetig ist. Alle geoeffneten Geraete zeigen damit denselben
 * Stand.
 */
import {subscribe, refresh} from './state-store.js'

function csrfToken() {
    const feld = document.querySelector("[name=csrfmiddlewaretoken]");
    return feld ? feld.value : "";
}

function istFokussiert(element) {
    return element && document.activeElement === element;
}

function staerkeText(eintrag) {
    return eintrag.Zugfuehrer + "/" + eintrag.Gruppenfuehrer + "/" + eintrag.Mannschaft
        + " (" + eintrag.Atemschutz + " AGT)";
}

function tooltipsAktualisieren(container) {
    if (window.jQuery && jQuery.fn.tooltip) {
        jQuery(container).find('[data-toggle="tooltip"]').tooltip();
    }
}

// ---------------------------------------------------------------------------
// Grunddaten
// ---------------------------------------------------------------------------
let endeBereitsBekannt = null;

function renderGrunddaten(state) {
    const einsatz = state.einsatz;

    const felder = [
        [document.querySelector("input[name='extENr']"), einsatz.extNummer === null ? "" : einsatz.extNummer],
        [document.querySelector("input[name='einsatzleiter']"), einsatz.Einsatzleiter || ""],
        [document.querySelector("input[name='adresse']"), einsatz.Adresse || ""]
    ];
    felder.forEach(([element, wert]) => {
        // Eingaben anderer Geraete uebernehmen, aber nie waehrend des Tippens
        if (element && !istFokussiert(element) && element.value !== String(wert)) {
            element.value = wert;
        }
    });

    // Nur-Lese-Anzeige (z.B. fuer nicht angemeldete Betrachter)
    const texte = {
        'extNummer': einsatz.extNummer === null || einsatz.extNummer === undefined || einsatz.extNummer === ""
            ? String(einsatz.Nummer)
            : String(einsatz.extNummer),
        'Einsatzleiter': einsatz.Einsatzleiter || "Kein Einsatzleiter eingetragen!",
        'Adresse': einsatz.Adresse || ""
    };
    document.querySelectorAll('[data-live-text]').forEach(element => {
        const wert = texte[element.dataset.liveText];
        if (wert !== undefined && element.textContent !== wert) {
            element.textContent = wert;
        }
    });

    // Einsatzende: sobald der Einsatz beendet wurde, muessen alle Geraete in
    // die Abschlussansicht wechseln (Formulare weg, Ende sichtbar).
    const beendet = Boolean(einsatz.Ende);
    if (endeBereitsBekannt === null) {
        endeBereitsBekannt = beendet;
    } else if (beendet && !endeBereitsBekannt) {
        endeBereitsBekannt = true;
        window.location.reload();
    }
}

// ---------------------------------------------------------------------------
// Fahrzeuge und Staerken
// ---------------------------------------------------------------------------
function renderFahrzeuge(state) {
    const liste = document.getElementById('Fahrzeugliste');
    if (!liste) {
        return;
    }
    const staerken = state.staerken || {};
    const gesamt = staerken['Gesamt'];
    const teile = [];

    if (gesamt) {
        const personal = gesamt.zugfuehrer + gesamt.gruppenfuehrer + gesamt.mannschaft;
        teile.push('<li class="SummePersonal Wichtig">'
            + '<center class="do-not-print">Insgesamt ' + personal + ' Einsatzkräfte</center>'
            + '<span class="do-not-show">Insgesamt ' + personal + ' Einsatzkräfte</span></li>');
        teile.push('<li class="SummePersonal Wichtig">'
            + '<center class="do-not-print">davon ' + gesamt.atemschutz + ' AGT</center></li>');
    }

    Object.keys(staerken).forEach(name => {
        if (name === 'Gesamt') {
            return;
        }
        const zug = staerken[name];
        teile.push('<li class="SummePersonal Wichtig">' + escapeHtml(name) + ': <div>'
            + zug.zugfuehrer + '/' + zug.gruppenfuehrer + '/' + zug.mannschaft
            + ' (' + zug.atemschutz + ' AGT)</div></li>');
    });

    (state.fahrzeuge || []).forEach(fahrzeug => {
        teile.push('<li class="Fahrzeug" style="background-color: ' + escapeHtml(fahrzeug.Farbe) + ';"'
            + ' data-toggle="tooltip" data-placement="bottom"'
            + ' title="' + escapeHtml(fahrzeug.Typ + ' - ' + fahrzeug.Ort) + '">'
            + escapeHtml(fahrzeug.Funkname) + ' - Stärke: ' + staerkeText(fahrzeug)
            + '</li>');
    });

    liste.innerHTML = teile.join('');
    tooltipsAktualisieren(liste);
}

// ---------------------------------------------------------------------------
// Beteiligte Personen
// ---------------------------------------------------------------------------
function renderPersonen(state) {
    const liste = document.getElementById('Personenliste');
    if (!liste) {
        return;
    }
    const teile = (state.personen || []).map(person => {
        const beschriftung = person.Nachname + ', ' + person.Vorname + ' (' + person.Rolle + ')';
        return '<li class="Person"'
            + ' data-nachname="' + escapeHtml(person.Nachname) + '"'
            + ' data-vorname="' + escapeHtml(person.Vorname) + '"'
            + ' data-rolle="' + escapeHtml(person.Rolle) + '"'
            + ' data-notizen="' + escapeHtml(person.Notizen || '') + '"'
            + (person.Notizen ? ' data-toggle="tooltip" title="' + escapeHtml(person.Notizen) + '"' : '')
            + ' data-placement="bottom">'
            + escapeHtml(beschriftung)
            + '<ul class="do-not-show"><li>' + escapeHtml(person.Notizen || '') + '</li></ul>'
            + '</li>';
    });
    liste.innerHTML = teile.join('');
    tooltipsAktualisieren(liste);
}

function escapeHtml(wert) {
    return String(wert === null || wert === undefined ? '' : wert)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ---------------------------------------------------------------------------
// Formulare ohne Seiten-Reload abschicken
// ---------------------------------------------------------------------------
function formularAbsenden(form) {
    const daten = new FormData(form);
    const absenden = form.querySelectorAll('input[type=submit], button[type=submit]');
    absenden.forEach(btn => btn.disabled = true);

    return fetch(form.action, {
        method: 'POST',
        body: daten,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': csrfToken(),
            'X-Requested-With': 'fetch',
            'Accept': 'application/json'
        }
    })
        .then(res => res.json().catch(() => ({ok: res.ok})))
        .then(antwort => {
            if (antwort && antwort.redirect) {
                window.location.href = antwort.redirect;
                return;
            }
            if (antwort && antwort.ok === false) {
                alert(antwort.error || 'Die Eingabe konnte nicht gespeichert werden.');
                return;
            }
            form.reset();
            if (form.name === 'neue_Meldung') {
                // form.reset() stellt die vom Server gesetzte Vorauswahl
                // (Zug des Einsatzortes) wieder her, Fokus zurueck ins Textfeld
                const inhalt = form.querySelector('#MeldungInhalt');
                if (inhalt) {
                    inhalt.focus();
                }
            }
            refresh();
        })
        .catch(err => {
            console.error('Absenden fehlgeschlagen', err);
            alert('Keine Verbindung zum Server - die Eingabe wurde nicht gespeichert.');
        })
        .finally(() => {
            absenden.forEach(btn => btn.disabled = false);
        });
}

function feldSpeichern(url, daten) {
    return fetch(url, {
        method: 'POST',
        body: new URLSearchParams(daten),
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': csrfToken(),
            'X-Requested-With': 'fetch',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }).then(() => refresh());
}

function initFormulare() {
    document.querySelectorAll('form.js-live-form').forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            formularAbsenden(form);
        });
    });

    document.querySelectorAll('[data-numeric-only]').forEach(feld => {
        const nurZiffern = () => {
            const gefiltert = feld.value.replace(/[^0-9]/g, '');
            if (gefiltert !== feld.value) {
                const pos = feld.selectionStart;
                feld.value = gefiltert;
                try {
                    feld.setSelectionRange(pos - 1, pos - 1);
                } catch (e) {
                    /* Feldtyp unterstuetzt keine Auswahl */
                }
            }
        };
        feld.addEventListener('input', nurZiffern);
        feld.addEventListener('paste', () => setTimeout(nurZiffern, 0));
        feld.addEventListener('keypress', event => {
            if (event.key.length === 1 && !/[0-9]/.test(event.key)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll('[data-live-field]').forEach(feld => {
        feld.addEventListener('change', () => {
            if (typeof feld.checkValidity === 'function' && !feld.checkValidity()) {
                if (typeof feld.reportValidity === 'function') {
                    feld.reportValidity();
                }
                return;
            }
            const url = feld.dataset.liveField;
            const daten = {};
            daten[feld.name] = feld.value;
            feldSpeichern(url, daten);
        });
    });
}

// ---------------------------------------------------------------------------
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFormulare);
} else {
    initFormulare();
}

subscribe(state => {
    if (!state) {
        return;
    }
    renderGrunddaten(state);
    renderFahrzeuge(state);
    renderPersonen(state);
});




