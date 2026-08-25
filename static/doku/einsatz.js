// Slash automatisch nach jedem Zeichen einfügen (Stärkemeldung)
if($("input[name='Besatzung']").length){
    document.querySelector("input[name='Besatzung']").oninput = function () {
		var foo = this.value.split("/").join("");
		if (foo.length > 0) {
			foo = foo.match(new RegExp('.{1,1}', 'g')).join("/");
		}
		this.value = foo;
	};
    // In nächstes Input Element springen, wenn vollständig ausgefüllt
    document.querySelector("input[name='Besatzung']").onkeyup = function(e) {
        var target = e.srcElement || e.target;
        var maxLength = parseInt(target.attributes["maxlength"].value, 10);
        var myLength = target.value.length;
        if (myLength >= maxLength) {
            var next = target;
            while (next = next.nextElementSibling) {
                if (next == null)
                    break;
                if (next.tagName.toLowerCase() === "input") {
                    next.focus();
                    break;
                }
            }
        }
    }
}

// Ausfüllen des Formulars für neue Person, wenn vorhandene Person angeklickt wird
// (delegiert, da die Liste live neu gerendert wird)
$(document).on("click", ".Person", function(e) {
	var formObject = document.forms['neue_Person'];
	if (!formObject) {
		return;
	}
	formObject.elements['Nachname'].value = this.dataset.nachname || "";
	formObject.elements['Vorname'].value = this.dataset.vorname || "";
	formObject.elements['Rolle'].value = this.dataset.rolle || "";
	formObject.elements['Notizen'].value = this.dataset.notizen || "";
	formObject.elements['Notizen'].focus();
});

// Nach der Zugauswahl direkt in das Textfeld springen.
// Die Vorauswahl selbst basiert auf dem Einsatzort (siehe views.zug_fuer_ort)
// und wird serverseitig im Template gesetzt.
function rememberZug(obj){
    var inhalt = document.getElementById("MeldungInhalt");
    if (inhalt) {
        inhalt.focus();
    }
}

// Aufraeumen: fruehere Versionen haben die Zugauswahl im Browser gespeichert
try {
    localStorage.removeItem("letzterZug");
} catch (e) {
    // localStorage nicht verfuegbar - unkritisch
}
