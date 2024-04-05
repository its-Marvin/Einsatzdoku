'use strict';
import {get_zug} from './component-zug.js'

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
            zug: {}
        };
    }

    fetchMeldungen() {
        const einsatz_id = window.location.pathname.split("/").pop();
        fetch("/" + einsatz_id + "/Meldung")
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

    async get_zug_color_wrapper(zug_id) {
        if (!(zug_id in this.state.zug)) {
            this.state.zug[zug_id] = await get_zug(zug_id);
        }
        let zug = this.state.zug[zug_id];
        document.querySelectorAll('.z_' + zug_id)
                .forEach(domContainer => {
                    domContainer.style.backgroundColor = JSON.parse(zug)[0].fields.Farbe;
                });
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
                if (meldung.fields.Zug) {
                    let zug_id = meldung.fields.Zug;
                    childs.unshift(e('li', {className: "Meldung z_" + zug_id}, text));
                    this.get_zug_color_wrapper(zug_id);
                } else {
                //{% if not Meldung.Wichtig %}style="background-color:{{ Meldung.Zug.Farbe }};"{% endif %}
                    childs.unshift(e('li', {className: "Meldung"}, text));
                }
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