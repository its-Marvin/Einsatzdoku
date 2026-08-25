'use strict';
/*
 * Zentraler Zustands-Store fuer die Einsatzansicht.
 *
 * Der Server meldet ueber Server-Sent-Events (/<id>/events) nur, dass sich
 * etwas geaendert hat. Daraufhin holt der Client den kompletten Snapshot
 * (/<id>/state). Dadurch sehen alle geoeffneten Geraete garantiert denselben
 * Zustand. Faellt die SSE-Verbindung aus, wird automatisch auf Polling
 * zurueckgefallen.
 */

const listeners = new Set();

let state = null;
let version = -1;
let source = null;
let pollTimer = null;
let reconnectTimer = null;
let backoff = 1000;
let laufendeAbfrage = null;

const POLL_INTERVAL = 3000;
const MAX_BACKOFF = 30000;

export function getEinsatzId() {
    if (document.body && document.body.dataset.einsatzId) {
        return document.body.dataset.einsatzId;
    }
    const match = window.location.pathname.match(/^\/(\d+)(\/|$)/);
    return match ? match[1] : null;
}

export function getState() {
    return state;
}

export function getVersion() {
    return version;
}

export function subscribe(callback) {
    listeners.add(callback);
    if (state) {
        sicherAufrufen(callback);
    }
    return () => listeners.delete(callback);
}

function sicherAufrufen(callback) {
    try {
        callback(state);
    } catch (err) {
        console.error('Fehler beim Aktualisieren der Ansicht', err);
    }
}

function benachrichtigen() {
    listeners.forEach(sicherAufrufen);
}

export function refresh(force = false) {
    const id = getEinsatzId();
    if (!id) {
        return Promise.resolve(null);
    }
    if (laufendeAbfrage) {
        return laufendeAbfrage;
    }
    laufendeAbfrage = fetch('/' + id + '/state', {
        headers: {'Accept': 'application/json'},
        credentials: 'same-origin'
    })
        .then(res => {
            if (!res.ok) {
                throw new Error('HTTP ' + res.status);
            }
            return res.json();
        })
        .then(daten => {
            if (force || daten.version !== version) {
                state = daten;
                version = daten.version;
                benachrichtigen();
            }
            return daten;
        })
        .catch(err => {
            console.warn('Einsatzzustand konnte nicht geladen werden', err);
            return null;
        })
        .finally(() => {
            laufendeAbfrage = null;
        });
    return laufendeAbfrage;
}

function pollingStarten() {
    if (pollTimer === null) {
        pollTimer = window.setInterval(() => refresh(), POLL_INTERVAL);
    }
}

function pollingStoppen() {
    if (pollTimer !== null) {
        window.clearInterval(pollTimer);
        pollTimer = null;
    }
}

function verbindungAufbauen() {
    const id = getEinsatzId();
    if (!id) {
        return;
    }
    if (!('EventSource' in window)) {
        pollingStarten();
        return;
    }
    if (source) {
        source.close();
    }
    source = new EventSource('/' + id + '/events?version=' + Math.max(version, 0));

    source.onopen = () => {
        backoff = 1000;
        pollingStoppen();
        // Nach (Wieder-)Verbindung sicherheitshalber den Stand abgleichen
        refresh();
    };

    source.addEventListener('change', () => refresh());

    source.onerror = () => {
        if (source) {
            source.close();
            source = null;
        }
        // Bis zur Wiederverbindung sicherstellen, dass Aenderungen ankommen
        pollingStarten();
        if (reconnectTimer === null) {
            reconnectTimer = window.setTimeout(() => {
                reconnectTimer = null;
                verbindungAufbauen();
            }, backoff);
            backoff = Math.min(backoff * 2, MAX_BACKOFF);
        }
    };
}

export function start() {
    const id = getEinsatzId();
    if (!id) {
        return;
    }
    refresh(true).then(() => verbindungAufbauen());

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            refresh();
        }
    });
    window.addEventListener('online', () => {
        refresh();
        verbindungAufbauen();
    });
}

// Automatisch starten, sobald das Modul geladen ist
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
} else {
    start();
}

// Auch fuer klassische (nicht-modulare) Skripte erreichbar machen
window.EinsatzStore = {subscribe, getState, getVersion, refresh, getEinsatzId};
