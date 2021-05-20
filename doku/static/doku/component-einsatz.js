'use strict';
import {get_ort} from './component-ort.js'

const e = React.createElement;

class Einsatzliste extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            data: '[]'
        };
    }

    componentDidMount() {
        this.fetchEinsaetze();
        this.interval = setInterval(() => {
            this.fetchEinsaetze()
        }, 5000);
    }

    componentWillUnmount() {
        clearInterval(this.interval);
    }

    fetchEinsaetze() {
        fetch("/doku/Einsatz/all")
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
                        error
                    });
                }
            )
    }

    get_ort_wrapper(ort_id) {
        return get_ort(ort_id).then(res => {
            document.querySelectorAll('.replace_' + ort_id)
                .forEach(domContainer => {
                    domContainer.innerHTML = res.toString();
                });
        });
    }

    render() {
        let json = JSON.parse(this.state.data);
        let array = [];
        for (let i = 0; i < json.length; i++) {
            if (this.props.onlyNew && json[i].fields.Ende == null) {
                // aktive Einsätze
                let el = "#" + json[i].pk + " - " + json[i].fields.Adresse;
                el += " in ";
                el += "<div class=\"replace_" + json[i].fields.Ort + "\"></div>"
                this.get_ort_wrapper(json[i].fields.Ort);
                // json[i].fields.Freitext === null ? el += json[i].fields.Freitext : el += get_ort(json[i].fields.Ort).Kurzname;
                if (json[i].fields.extNummer !== null) {
                    el = el + " (#" + json[i].fields.extNummer + ")"
                }
                let einsatz = e('li', {className: 'Wichtig', key: json[i].pk}, el);
                let link = e('a', {href: '/doku/' + json[i].pk, key: json[i].pk}, einsatz)
                array.push(link);
            } else if (!this.props.onlyNew && json[i].fields.Ende != null) {
                // beendete Einsätze
                let el = "#" + json[i].pk + " - " + json[i].fields.Adresse;
                if (json[i].fields.extNummer !== null) {
                    el = el + " (#" + json[i].fields.extNummer + ")"
                }
                let einsatz = e('li', {key: json[i].pk}, el);
                let link = e('a', {href: '/doku/' + json[i].pk, key: json[i].pk}, einsatz)
                array.push(link);
            }
        }
        return e('ul', null, array);
    }
}

document.querySelectorAll('.einsatzliste')
    .forEach(domContainer => {
        let onlyNew = false;
        if (domContainer.classList.contains('offene-einsaetze')) onlyNew = true;
        ReactDOM.render(
            e(Einsatzliste, {onlyNew: onlyNew, nav: false}),
            domContainer
        );
    });