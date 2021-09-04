'use strict';
import {get_ort} from './component-ort.js'

const e = React.createElement;
const monthNames = ["Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember"
];

class Meldungsliste extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            data: '[]',
        };
    }

    fetchMeldungen() {
        const einsatz_id = window.location.pathname.split("/").pop();
        fetch("/doku/" + einsatz_id + "/Meldung")
            .then(res => res.json())
            .then(
                (json) => {
                    this.setState({
                        isLoaded: true,
                        data: json
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error: error
                    });
                }
            )
    }

    componentDidMount() {
        this.fetchMeldungen();
        this.interval = setInterval(() => {
            this.fetchMeldungen();
        }, 500);
    }

    componentWillUnmount() {
        clearInterval(this.interval);
    }

    getCustomDateString(meldung) {
        const erstellt = new Date(meldung.fields.Erstellt);
        const today = new Date();
        let date = "";
        if (erstellt.getDate() < today.getDate()
            || erstellt.getMonth() < today.getMonth()
            || erstellt.getFullYear() < today.getFullYear()) {
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
        let json = JSON.parse(this.state.data);
        let array = [];
        let childs = [];
        for (let i = 0; i < json.length; i++) {
            const meldung = json[i];
            let text = this.getCustomDateString(meldung)
            text += " - " + meldung.fields.Inhalt;
            if (meldung.fields.Wichtig) {
                childs.unshift(e('li', {className: "Meldung Wichtig"}, text));
            } else {
                childs.unshift(e('li', {className: "Meldung"}, text));
            }
        }
        array.push(childs);
        return e('ul', null, array);
    }
}

document.querySelectorAll('.Meldungsliste')
    .forEach(domContainer => {
        ReactDOM.render(
            e(Meldungsliste, {}),
            domContainer
        );
    });