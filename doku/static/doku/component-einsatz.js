'use strict';
import {get_ort} from './component-ort.js'

const e = React.createElement;

class Einsatzliste extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            data: '[]',
            orte: {}
        };
    }

    componentDidMount() {
        if (window.location.href.indexOf('training') > -1) {
            this.fetchEinsaetze('/training/all')
            this.interval = setInterval(() => {
                this.fetchEinsaetze('/training/all')
            }, 500);
        } else {
            this.fetchEinsaetze('/Einsatz/all')
            this.interval = setInterval(() => {
                this.fetchEinsaetze('/Einsatz/all')
            }, 500);
        }
    }

    componentWillUnmount() {
        clearInterval(this.interval);
    }

    fetchEinsaetze(url) {
        fetch(url)
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

    async get_ort_wrapper(ort_id) {
        if (!(ort_id in this.state.orte)) {
            this.state.orte[ort_id] = await get_ort(ort_id);
        }
        let ort = this.state.orte[ort_id];
        document.querySelectorAll('.o_' + ort_id)
                .forEach(domContainer => {
                    domContainer.innerHTML = JSON.parse(ort)[0].fields.Langname;
                });
    }

    render_aktiv(einsatz) {
        let childs = [];
        childs.push(einsatz.fields.Adresse + " in ");
        if (einsatz.fields.OrtFrei == null || einsatz.fields.OrtFrei == '') {
            childs.push(e('span',
                {className: 'o_' + einsatz.fields.Ort, key: einsatz.pk + "_o"}));
            this.get_ort_wrapper(einsatz.fields.Ort);
        } else {
            childs.push(e('span', {key: einsatz.pk + "_o"}, einsatz.fields.OrtFrei));
        }
        if (einsatz.fields.extNummer !== null) {
            childs.push(" (#" + einsatz.fields.extNummer + ")");
        }
        childs.push(e('b', {key: einsatz.pk + "_s"}, einsatz.fields.Stichwort));
        let list = e('li', {className: 'Wichtig', key: einsatz.pk}, childs);
        let link = e('a', {href: '/' + einsatz.pk, key: einsatz.pk}, list)
        return link;
    }

    render_beendet(einsatz) {
        let childs = [];
        childs.push(einsatz.fields.Adresse + " in ");
        if (einsatz.fields.OrtFrei == null || einsatz.fields.OrtFrei == '') {
            childs.push(e('span',
                {className: 'o_' + einsatz.fields.Ort, key: einsatz.pk + "_o"}));
            this.get_ort_wrapper(einsatz.fields.Ort);
        } else {
            childs.push(e('span', {key: einsatz.pk + "_o"}, einsatz.fields.OrtFrei));
        }
        childs.push(e('b', {key: einsatz.pk + "_s"}, einsatz.fields.Stichwort));
        let subchilds = [];
        if (einsatz.fields.extNummer !== null) {
            subchilds.push(e('p', {key: einsatz.pk + "_n"},"Einsatz-Nr: " + einsatz.fields.extNummer));
        }
        let dateoptions = {day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"};
        let starttime = new Date(einsatz.fields.Erstellt)
        let start = e('li', {key: einsatz.pk + "_start"}, "Von: " +
            starttime.toLocaleString(undefined, dateoptions));
        let endtime = new Date(einsatz.fields.Ende)
        let ende = e('li', {key: einsatz.pk + "_ende"}, "Bis: " +
            endtime.toLocaleString(undefined, dateoptions));
        subchilds.push(e('ul', {key: einsatz.pk + "_t"}, [start, ende]))

        childs.push(subchilds);

        let list = e('li', {key: einsatz.pk}, childs);
        let link = e('a', {href: '/' + einsatz.pk, key: einsatz.pk}, list)
        return link;
    }

    render() {
        let json = JSON.parse(this.state.data);
        let array = [];
        for (let i = 0; i < json.length; i++) {
            const einsatz = json[i];
            if (this.props.onlyNew && einsatz.fields.Ende == null) {
                // aktive Einsätze in umgekehrter Reihenfolge anzeigen, älteste zuerst
                array.unshift(this.render_aktiv(einsatz));
            } else if (!this.props.onlyNew &&
                json[i].fields.Ende != null &&
                this.props.year === new Date(einsatz.fields.Erstellt).getFullYear().toString()) {
                // beendete Einsätze
                array.push(this.render_beendet(einsatz));
            }
        }
        return e('ul', null, array);
    }
}

document.querySelectorAll('.einsatzliste')
    .forEach(domContainer => {
        let onlyNew = false;
        let year = new Date().getFullYear();
        if (domContainer.classList.contains('offene-einsaetze')) onlyNew = true;
        else if (domContainer.classList.length === 2) year = domContainer.classList[1];
        ReactDOM.render(
            e(Einsatzliste, {onlyNew: onlyNew, nav: false, year: year}),
            domContainer
        );
    });