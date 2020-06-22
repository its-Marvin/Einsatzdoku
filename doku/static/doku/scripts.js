// Bereiche mit Klick minimieren
var coll = document.getElementsByClassName("minimize-button");
addMinimizeHandler(coll);
coll = document.getElementsByTagName("h2");
addMinimizeHandler(coll);
function addMinimizeHandler(coll) {
    for (var i = 0; i < coll.length; i++) {
        coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var plusMinus = this;
            var content = this.nextElementSibling;
            if (this.tagName == "H2") {
                plusMinus = content;
                content = content.nextElementSibling;
            }
            if (content.style.display === "block") {
              content.style.display = "none";
              plusMinus.innerHTML = "+";
            } else {
              content.style.display = "block";
              plusMinus.innerHTML = "-";
            }
        });
    }
}
	
// X Hinzufügen oder Entfernen beim Klicken von Checkboxen
$(".checkmark").click(function(e) {
	if (this.innerHTML == "X") {
		this.innerHTML = "";
	} else {
		this.innerHTML = "X";
	}
});

var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(document).ready(function(){
  $('[data-toggle="tooltip"]').tooltip();
});

// Onclick dropdown
$(document).ready(function() {
  $('.Einsatzstelle').on("click",function(){

    $(this).find(".EinsatzstelleMenu").toggle();
    $(this).siblings().find(".EinsatzstelleMenu").hide();
  }).find('.noClick').on("click",function(e){e.stopPropagation();});
});

$(document).ready(function() {
    $('.minimize-button').prev().css("cursor", "pointer");
});
