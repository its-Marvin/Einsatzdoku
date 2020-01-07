// Slash automatisch nach jedem Zeichen einfügen (Stärkemeldung)
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

// Ausfüllen des Formulars für neue Person, wenn vorhandene Person angeklickt wird
$(".Person").click(function(e) {
	formObject = document.forms['neue_Person'];
	content = this.innerHTML.split("<")[0];
	formObject.elements['Nachname'].value = content.split(",")[0].trim();
	formObject.elements['Vorname'].value = content.split(",")[1].split("(")[0].trim();
	formObject.elements['Rolle'].value = content.split(",")[1].split("(")[1].replace(")", "").trim();
	formObject.elements['Notizen'].value = this.children[0].children[0].innerHTML.trim();
	formObject.elements['Notizen'].focus();
});

// Farbgebung der Meldungen
// TODO Farben variabel und auf Basis der Züge
$(".Meldung").each(function(i, obj){
    if($(this).text().indexOf('West:') > -1) {$(this).css("background-color","#87CEFA");$(this).css("color","#000000");};
    if($(this).text().indexOf('Ost:') > -1) {$(this).css("background-color","#4682B4");};
})

// Zugauswahl für Meldungen merken
function rememberZug(obj){
    localStorage.setItem("letzterZug", obj.options[obj.selectedIndex].value);
    document.getElementById("MeldungInhalt").focus();
}

// letzte Auswahl wiederherstellen
document.getElementById("MeldungZug").value = localStorage.getItem("letzterZug");
