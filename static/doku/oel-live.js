'use strict';
/*
 * Live-Abgleich der OEL-Ansicht.
 *
 * Die OEL-Seite wird serverseitig gerendert; bei einer Aenderung durch ein
 * anderes Geraet wird die Seite deshalb neu geladen. Damit dabei keine
 * Eingaben verloren gehen, wird gewartet, bis der Benutzer gerade nichts
 * tippt.
 */
import {subscribe, getVersion} from './state-store.js'

let bekannteVersion = null;
let neuladenGeplant = false;

function benutzerTippt() {
    const aktiv = document.activeElement;
    if (!aktiv) {
        return false;
    }
    const tag = aktiv.tagName ? aktiv.tagName.toLowerCase() : '';
    if (tag !== 'input' && tag !== 'textarea' && tag !== 'select') {
        return false;
    }
    return true;
}

function neuLadenWennMoeglich() {
    if (benutzerTippt()) {
        window.setTimeout(neuLadenWennMoeglich, 2000);
        return;
    }
    window.location.reload();
}

subscribe(() => {
    const version = getVersion();
    if (bekannteVersion === null) {
        bekannteVersion = version;
        return;
    }
    if (version !== bekannteVersion && !neuladenGeplant) {
        neuladenGeplant = true;
        neuLadenWennMoeglich();
    }
});

