'use strict';
import {subscribe} from './state-store.js'

const e = React.createElement;
const monthNames = ["Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember"
];

class Meldungsliste extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            meldungen: []
        };
    }

    componentDidMount() {
        // Zentraler Store: identischer Zustand auf allen Geraeten
        this.unsubscribe = subscribe((daten) => {
            this.setState({meldungen: (daten && daten.meldungen) ? daten.meldungen : []});
        });
    }

    componentWillUnmount() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    }

    getCustomDateString(meldung) {
        const erstellt = new Date(meldung.Erstellt);
        const today = new Date();
        let date = "";
        // Tagesgenauer Vergleich: nur wenn die Meldung nicht von heute ist,
        // wird zusaetzlich das Datum ausgegeben.
        const erstelltTag = new Date(erstellt.getFullYear(), erstellt.getMonth(), erstellt.getDate());
        const heuteTag = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        if (erstelltTag.getTime() !== heuteTag.getTime()) {
            date = ("0" + erstellt.getDate().toString()).slice(-2)
                + ". " + monthNames[erstellt.getMonth()]
                + " " + erstellt.getFullYear().toString()
                + " ";
        }
        date += ("0" + erstellt.getHours().toString()).slice(-2) + ":"
            + ("0" + erstellt.getMinutes().toString()).slice(-2);
        return date;
    }

    render() {
        // Explizit sortieren (neueste zuerst), damit die Anzeige nicht von der
        // Reihenfolge der Server-Antwort abhaengt. Bei identischen Zeitstempeln
        // entscheidet die pk - genau wie im Django-Modell.
        const meldungen = this.state.meldungen.slice().sort((a, b) => {
            const diff = new Date(b.Erstellt) - new Date(a.Erstellt);
            return diff !== 0 ? diff : (b.pk - a.pk);
        });
        const childs = meldungen.map(meldung => {
            const text = this.getCustomDateString(meldung) + " - " + meldung.Inhalt;
            const props = {
                key: meldung.pk,
                className: meldung.Wichtig ? "Meldung Wichtig" : "Meldung",
                title: meldung.Autor ? meldung.Autor : undefined
            };
            if (!meldung.Wichtig && meldung.Farbe) {
                props.style = {backgroundColor: meldung.Farbe};
            }
            return e('li', props, text);
        });
        return e('ul', null, childs);
    }
}

document.querySelectorAll('.Meldungsliste')
    .forEach(domContainer => {
        ReactDOM.render(
            e(Meldungsliste, {}),
            domContainer
        );
    });