document.title = "Einsatzdokumentation - Lagekarten"
const DEFAULT_WIDTH = 1100;
const DEFAULT_HEIGHT = 780;
let canvas = document.getElementById("Lagekarte");
let ctx = canvas.getContext("2d");
let ratio = canvas.width / canvas.height;
let curX, curY, prevX, prevY;
let hold = false;
var offsetX = canvas.offsetLeft;
var offsetY = canvas.offsetTop;
var startX;
var startY;
var startX_; // Used for distance calculation
var startY_;
let Linienbreite = $('#stiftdickeauswahl');
ctx.lineWidth = Linienbreite.val();
let Farbauswahl = $("#Farbauswahl");
ctx.strokeStyle = Farbauswahl.val();
var selectedObject = -1;

function initiateData() {
    return {
        "background": null,
        "pencil": [],
        "line": [],
        "rectangle": [],
        "circle": [],
        "icons": [],
        "texts": [],
        "width": DEFAULT_WIDTH,
        "height": DEFAULT_HEIGHT,
    };
}

let canvas_data = initiateData();

if (document.getElementById('addText')) {
    Linienbreite.change(function () {
        ctx.lineWidth = this.value;
    });

    Farbauswahl.change(function () {
        ctx.strokeStyle = this.value;
    });

    function clearEvents() {
        $(".Selected").removeClass("Selected");
        canvas.focus();
        $("#Lagekarte").off();

        function unhold() {
            hold = false;
        }

        canvas.onmousemove = unhold;
        canvas.onmousedown = unhold;
        canvas.onmouseup = unhold;
    }

    function cursor() {
        clearEvents();
        $("#cursor").addClass("Selected");

        // test if x,y is inside the bounding box of texts[textIndex]
        function textHittest(x, y, textIndex) {
            var text = canvas_data.texts[textIndex];
            return (x >= text.x && x <= text.x + text.width && y >= text.y - text.height && y <= text.y);
        }

        // handle mousedown events
        // iterate through texts[] and see if the user
        // mousedown'ed on one of them
        // If yes, set the selectedObject to the index of that text
        function handleMouseDown(e) {
            e.preventDefault();
            startX = parseInt(e.clientX - offsetX);
            startY = parseInt(e.clientY - offsetY);
            startX_ = startX;
            startY_ = startY;
            // Put your mousedown stuff here
            for (var i = 0; i < canvas_data.texts.length; i++) {
                if (textHittest(startX, startY, i)) {
                    selectedObject = i;
                }
            }
        }

        // done dragging
        function handleMouseUp(e) {
            e.preventDefault();
            selectedObject = -1;
            redraw();
        }

        // also done dragging
        function handleMouseOut(e) {
            e.preventDefault();
            selectedObject = -1;
            redraw();
        }

        // handle mousemove events
        // calc how far the mouse has been dragged since
        // the last mousemove event and move the selected text
        // by that distance
        function handleMouseMove(e) {
            if (selectedObject < 0) {
                return;
            }
            e.preventDefault();
            mouseX = parseInt(e.clientX - offsetX);
            mouseY = parseInt(e.clientY - offsetY);

            // Put your mousemove stuff here
            var dx = mouseX - startX;
            var dy = mouseY - startY;
            startX = mouseX;
            startY = mouseY;

            var text = canvas_data.texts[selectedObject];
            text.x += dx;
            text.y += dy;
            let a = Math.abs(dx - startX_);
            let b = Math.abs(dy - startY_);
            if (Math.round(Math.hypot(a,b)) % 10 == 0) {
                redraw();
            }
            redraw_elements();
        }

        // listen for mouse events
        $("#Lagekarte").mousedown(function _md(e) {
            handleMouseDown(e);
        });
        $("#Lagekarte").mousemove(function _mm(e) {
            handleMouseMove(e);
        });
        $("#Lagekarte").mouseup(function __mu(e) {
            handleMouseUp(e);
        });
        $("#Lagekarte").mouseout(function _mo(e) {
            handleMouseOut(e);
        });
    }

    function pencil() {
        if ($(".Selected").attr('id') == "penciltool") {
            clearEvents();
        } else {
            $(".Selected").removeClass("Selected");
            $("#penciltool").addClass("Selected");

            canvas.onmousedown = function _md(e) {
                curX = e.clientX - canvas.offsetLeft;
                curY = e.clientY - canvas.offsetTop;
                hold = true;

                prevX = curX;
                prevY = curY;
                ctx.beginPath();
                ctx.moveTo(prevX, prevY);
            };

            canvas.onmousemove = function (e) {
                if (hold) {
                    prevX = curX;
                    prevY = curY;
                    curX = e.clientX - canvas.offsetLeft;
                    curY = e.clientY - canvas.offsetTop;
                    draw();
                }
            };

            canvas.onmouseup = function (e) {
                hold = false;
            };

            canvas.onmouseout = function (e) {
                hold = false;
            };

            function draw() {
                ctx.lineTo(curX, curY);
                ctx.stroke();
                canvas_data.pencil.push({
                    "startx": prevX, "starty": prevY, "endx": curX, "endy": curY,
                    "thick": ctx.lineWidth, "color": ctx.strokeStyle
                });
            }
        }
    }

    function line() {
        $(".Selected").removeClass("Selected");
        $("#linetool").addClass("Selected");

        canvas.onmousedown = function (e) {
            img = ctx.getImageData(0, 0, canvas.width, canvas.height);
            prevX = e.clientX - canvas.offsetLeft;
            prevY = e.clientY - canvas.offsetTop;
            hold = true;
        };

        canvas.onmousemove = function (e) {
            if (hold) {
                ctx.putImageData(img, 0, 0);
                curX = e.clientX - canvas.offsetLeft;
                curY = e.clientY - canvas.offsetTop;
                ctx.beginPath();
                ctx.moveTo(prevX, prevY);
                ctx.lineTo(curX, curY);
                ctx.stroke();
                ctx.closePath();
            }
        };

        canvas.onmouseup = function (e) {
            if (hold) {
                canvas_data.line.push({
                    "startx": prevX, "starty": prevY, "endx": curX, "endy": curY,
                    "thick": ctx.lineWidth, "color": ctx.strokeStyle
                });
            }
            hold = false;

        };
    }

    function rectangle() {
        $(".Selected").removeClass("Selected");
        $("#rectangletool").addClass("Selected");

        canvas.onmousedown = function (e) {
            img = ctx.getImageData(0, 0, canvas.width, canvas.height);
            prevX = e.clientX - canvas.offsetLeft;
            prevY = e.clientY - canvas.offsetTop;
            hold = true;
        };

        canvas.onmousemove = function (e) {
            if (hold) {
                ctx.putImageData(img, 0, 0);
                curX = e.clientX - canvas.offsetLeft - prevX;
                curY = e.clientY - canvas.offsetTop - prevY;
                ctx.strokeRect(prevX, prevY, curX, curY);
            }
        };

        canvas.onmouseup = function (e) {
            canvas_data.rectangle.push({
                "startx": prevX, "starty": prevY, "endx": curX, "endy": curY,
                "thick": ctx.lineWidth, "color": ctx.strokeStyle
            });
            hold = false;
        };
    }

    function circle() {
        $(".Selected").removeClass("Selected");
        $("#circletool").addClass("Selected");

        canvas.onmousedown = function (e) {
            img = ctx.getImageData(0, 0, canvas.width, canvas.height);
            prevX = e.clientX - canvas.offsetLeft;
            prevY = e.clientY - canvas.offsetTop;
            hold = true;
        };

        canvas.onmousemove = function (e) {
            if (hold) {
                ctx.putImageData(img, 0, 0);
                curX = e.clientX - canvas.offsetLeft;
                curY = e.clientY - canvas.offsetTop;
                ctx.beginPath();
                //ctx.arc(Math.abs(curX + prevX)/2, Math.abs(curY + prevY)/2, Math.sqrt(Math.pow(curX - prevX, 2) + Math.pow(curY - prevY, 2))/2, 0, Math.PI * 2, true);
                radius = Math.sqrt(Math.pow(curX - prevX, 2) + Math.pow(curY - prevY, 2));
                ctx.arc(prevX, prevY, radius, 0, 2 * Math.PI);
                ctx.closePath();
                ctx.stroke();
            }
        };

        canvas.onmouseup = function (e) {
            hold = false;
            canvas_data.circle.push({
                "startx": prevX, "starty": prevY, "radius": radius, "thick": ctx.lineWidth,
                "color": ctx.strokeStyle
            });
        };

        canvas.onmouseout = function (e) {
            hold = false;
        };
    }

    // Hintergrund importieren
    var imageLoader = document.getElementById('importBackground');
    imageLoader.addEventListener('change', handleImage, false);

    function handleImage(e) {
        clearCanvas();
        var reader = new FileReader();
        reader.onload = function (event) {
            var img = new Image();
            img.src = event.target.result;
            img.onload = function () {
                ratio = img.width / img.height;
                canvas_data.background = img.src;
                resize();
            }
        }
        reader.readAsDataURL(e.target.files[0]);
    }

    // ##############################################################################################
    // Text zu Lagekarte hinzufügen
    $("#addText").click(function () {
        let text_height = ctx.lineWidth * 5;
        let text_font = String(text_height) + "px verdana";
        // get the text from the input element
        var text = {
            text: $("#newText").val(),
            x: 20,
            color: ctx.strokeStyle,
            font: text_font,
            height: text_height,
            y: 42,
        };
        // calc the size of this text for hit-testing purposes
        ctx.font = text.font;
        text.width = ctx.measureText(text.text).width;
        // put this new text in the texts array
        canvas_data.texts.push(text);
        redraw();
    });

    // Lagekarte speichern
    $("#speichern").click(function () {
            let img = canvas_data.background;
            try {
                canvas_data.background = img.src;
            } catch (TypeError) {
                alert("Speichern ist nur mit Hintergrund möglich!");
                return;
            }
            $.post(location.pathname, {
                    'image': canvas.toDataURL('image/webp', 0.85),
                    'canvas_data': JSON.stringify(canvas_data)
                },
                function () {
                    location.reload();
                });
            canvas_data.background = img;
        }
    )

    // Default behaviour is drag&drop
    cursor();
}

// clear the canvas & redraw everything
function redraw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    addBackground();
    redraw_elements();
}

function redraw_elements() {
    for (var i = 0; i < canvas_data.pencil.length; i++) {
        var pencil = canvas_data.pencil[i];
        ctx.beginPath();
        ctx.lineWidth = pencil.thick;
        ctx.strokeStyle = pencil.color;
        ctx.moveTo(pencil.startx, pencil.starty);
        ctx.lineTo(pencil.endx, pencil.endy);
        ctx.stroke();
    }
    for (var i = 0; i < canvas_data.line.length; i++) {
        var line = canvas_data.line[i];
        ctx.beginPath();
        ctx.lineWidth = line.thick;
        ctx.strokeStyle = line.color;
        ctx.moveTo(line.startx, line.starty);
        ctx.lineTo(line.endx, line.endy);
        ctx.stroke();
        ctx.closePath();
    }
    for (var i = 0; i < canvas_data.rectangle.length; i++) {
        var rectangle = canvas_data.rectangle[i];
        ctx.beginPath();
        ctx.lineWidth = rectangle.thick;
        ctx.strokeStyle = rectangle.color;
        ctx.strokeRect(rectangle.startx, rectangle.starty, rectangle.endx, rectangle.endy);
    }
    for (var i = 0; i < canvas_data.circle.length; i++) {
        var circle = canvas_data.circle[i];
        ctx.beginPath();
        ctx.lineWidth = circle.thick;
        ctx.strokeStyle = circle.color;
        ctx.arc(circle.startx, circle.starty, circle.radius, 0, Math.PI * 2);
        ctx.stroke();
    }
    for (var i = 0; i < canvas_data.icons.length; i++) {
        var icon = canvas_data.icons[i];
        ctx.drawImage(icon.img, icon.startx, icon.starty, icon.endx, icon.endy);
    }
    for (var i = 0; i < canvas_data.texts.length; i++) {
        var text = canvas_data.texts[i];
        ctx.font = text.font;
        ctx.fillStyle = text.color;
        ctx.fillText(text.text, text.x, text.y);
    }
    ctx.lineWidth = Linienbreite.val();
    ctx.strokeStyle = Farbauswahl.val();
    rememberCanvas()
}

function addBackground() {
    if (canvas_data.background !== null && canvas_data.background !== undefined) {
        //ctx.drawImage(canvas_data.background, 0, 0, canvas_data.width, canvas_data.height);
        let img = new Image();
        if (canvas_data.background !== null) {
            img.src = canvas_data.background;
        }
        img.onload = function () {
            //canvas_data.background = img;
            ctx.drawImage(img, 0, 0, canvas_data.width, canvas_data.height);
            redraw_elements();
        }
    }
}

// alte Lagekarte als Canvas Hintergrund setzen
$(".ArchivKarte").click(function () {
    canvas_data = JSON.parse($(this).find(".Lagekarte-Data").text());
    let img = new Image();
    if (canvas_data.background !== null) {
        img.src = canvas_data.background;
    }
    img.onload = function () {
        ratio = img.width / img.height;
        ctx.drawImage(img, 0, 0, canvas_data.width, canvas_data.height);
        resize();
    }

})

function resize() {
    canvas_data.height = Math.round(canvas_data.width / ratio);

    if (canvas_data.height > DEFAULT_HEIGHT) {
        canvas_data.height = DEFAULT_HEIGHT;
        canvas_data.width = DEFAULT_HEIGHT * ratio;
    }
    canvas.width = canvas_data.width;
    canvas.height = canvas_data.height;
    redraw();
}

// Aktualisierung überstehen
function rememberCanvas() {
    sessionStorage.setItem("Lagekarte", JSON.stringify(canvas_data));
}

function clearCanvas() {
    canvas_data = initiateData();
    resize();
    cursor();
}

// letzte Auswahl wiederherstellen
$(document).ready(function () {
    let tmp_canvas_data = sessionStorage.getItem("Lagekarte");
    if (tmp_canvas_data !== null) {
        canvas_data = JSON.parse(tmp_canvas_data);
        ratio = canvas_data.width / canvas_data.height;
        resize();
    }
});
