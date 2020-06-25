document.title = "Einsatzdokumentation - Lagekarten"
var canvas = document.getElementById("Lagekarte");
var ctx = canvas.getContext("2d");
var width = canvas.width, height = canvas.height;
var curX, curY, prevX, prevY;
var hold = false;
var stroke_value = false;
var ratio = 16/9;
var canvas_data = { "background": null ,"pencil": [], "line": [], "rectangle": [], "circle": [], "icons": [], "texts": [] };
var offsetX = canvas.offsetLeft;
var offsetY = canvas.offsetTop;
var startX;
var startY;
var Stiftdicke = $('#stiftdickeauswahl').val();
ctx.lineWidth = Stiftdicke;
var selectedObject = -1;

var toolsExist = document.getElementById('addText');
if (toolsExist) {
    $('#stiftdickeauswahl').on('input', function() {
        ctx.lineWidth = this.value;
        Stiftdicke = this.value;
    })

    function clearEvents() {
        $(".Selected").removeClass("Selected");
        document.activeElement.blur()
        canvas.focus();
        $("#Lagekarte").off();
        function unhold(){
            hold=false;
        }
        canvas.onmousemove = unhold;
        canvas.onmousedown = unhold;
        canvas.onmouseup = unhold;
    }

    function cursor (){
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
        }

        // also done dragging
        function handleMouseOut(e) {
            e.preventDefault();
            selectedObject = -1;
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
            redraw();
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

    function pencil (){
        if($(".Selected").attr('id') == "penciltool"){
            clearEvents();
        } else {
            $(".Selected").removeClass("Selected");
            $("#penciltool").addClass("Selected");

            canvas.onmousedown = function _md(e){
                curX = e.clientX - canvas.offsetLeft;
                curY = e.clientY - canvas.offsetTop;
                hold = true;

                prevX = curX;
                prevY = curY;
                ctx.beginPath();
                ctx.lineWidth = Stiftdicke;
                ctx.moveTo(prevX, prevY);
            };

            canvas.onmousemove = function (e){
                if(hold){
                    prevX = curX;
                    prevY = curY;
                    curX = e.clientX - canvas.offsetLeft;
                    curY = e.clientY - canvas.offsetTop;
                    draw();
                }
            };

            canvas.onmouseup = function (e){
                hold = false;
            };

            canvas.onmouseout = function (e){
                hold = false;
            };

            function draw (){
                ctx.lineTo(curX, curY);
                ctx.stroke();
                canvas_data.pencil.push({ "startx": prevX, "starty": prevY, "endx": curX, "endy": curY,
                    "thick": ctx.lineWidth, "color": ctx.strokeStyle });
            }
        }
    }

    function line (){
        $(".Selected").removeClass("Selected");
        $("#linetool").addClass("Selected");

        canvas.onmousedown = function (e){
            img = ctx.getImageData(0, 0, width, height);
            prevX = e.clientX - canvas.offsetLeft;
            prevY = e.clientY - canvas.offsetTop;
            hold = true;
        };

        canvas.onmousemove = function (e){
            if (hold){
                ctx.putImageData(img, 0, 0);
                curX = e.clientX - canvas.offsetLeft;
                curY = e.clientY - canvas.offsetTop;
                ctx.beginPath();
                ctx.lineWidth = Stiftdicke;
                ctx.moveTo(prevX, prevY);
                ctx.lineTo(curX, curY);
                ctx.stroke();
                ctx.closePath();
            }
        };

        canvas.onmouseup = function (e){
            if (hold){
             canvas_data.line.push({ "startx": prevX, "starty": prevY, "endx": curX, "endy": curY,
                     "thick": ctx.lineWidth, "color": ctx.strokeStyle });
             }
             hold = false;

        };
    }

    function rectangle (){
        $(".Selected").removeClass("Selected");
        $("#rectangletool").addClass("Selected");

        canvas.onmousedown = function (e){
            img = ctx.getImageData(0, 0, width, height);
            prevX = e.clientX - canvas.offsetLeft;
            prevY = e.clientY - canvas.offsetTop;
            hold = true;
        };

        canvas.onmousemove = function (e){
            if (hold){
                ctx.putImageData(img, 0, 0);
                curX = e.clientX - canvas.offsetLeft - prevX;
                curY = e.clientY - canvas.offsetTop - prevY;
                ctx.strokeRect(prevX, prevY, curX, curY);
            }
        };

        canvas.onmouseup = function (e){
            canvas_data.rectangle.push({ "startx": prevX, "starty": prevY, "endx": curX, "endy": curY,
                    "thick": ctx.lineWidth, "color": ctx.strokeStyle });
            hold = false;
        };
    }

    function circle (){
        $(".Selected").removeClass("Selected");
        $("#circletool").addClass("Selected");

        canvas.onmousedown = function (e){
            img = ctx.getImageData(0, 0, width, height);
            prevX = e.clientX - canvas.offsetLeft;
            prevY = e.clientY - canvas.offsetTop;
            hold = true;
        };

        canvas.onmousemove = function (e){
            if (hold){
                ctx.putImageData(img, 0, 0);
                curX = e.clientX - canvas.offsetLeft;
                curY = e.clientY - canvas.offsetTop;
                ctx.beginPath();
                ctx.lineWidth = Stiftdicke;
                //ctx.arc(Math.abs(curX + prevX)/2, Math.abs(curY + prevY)/2, Math.sqrt(Math.pow(curX - prevX, 2) + Math.pow(curY - prevY, 2))/2, 0, Math.PI * 2, true);
                radius = Math.sqrt(Math.pow(curX - prevX, 2) + Math.pow(curY - prevY, 2));
                ctx.arc(prevX, prevY, radius, 0, 2 * Math.PI);
                ctx.closePath();
                ctx.stroke();
            }
        };

        canvas.onmouseup = function (e){
            hold = false;
            canvas_data.circle.push({ "startx": prevX, "starty": prevY, "radius": radius, "thick": ctx.lineWidth,
                    "color": ctx.strokeStyle });
        };

        canvas.onmouseout = function (e){
            hold = false;
        };
    }

    // Farbauswahl
    var colorInput = document.getElementById('Farbauswahl');
    var colorPalette = document.getElementById('Farbpalette');
    colorInput.value = "#000000";
    colorInput.addEventListener("click", showColorPalette);
    colorInput.addEventListener("focusout", hideColorPalette);
    colorPalette.mouseIsOver = false;
    colorInput.style.borderRight =  `20px solid ${colorInput.value}`;

    colorPalette.onmouseover = () => {
        colorPalette.mouseIsOver = true;
    };
    colorPalette.onmouseout = () => {
        colorPalette.mouseIsOver = false;
    }


    function hideColorPalette() {
      if(colorPalette.mouseIsOver === false) {
        colorPalette.style.display = 'none';
        colorInput.style.borderRight =  `20px solid ${colorInput.value}`;
      }
    }

    function chooseColor(e) {
      let selected_color = rgbToHex(e.target.style.backgroundColor);
      colorInput.value = selected_color;
      colorInput.style.borderRight =  `20px solid ${selected_color}`;
      colorPalette.style.display = 'none';
      ctx.strokeStyle = selected_color;
    }

    function componentToHex(c) {
      var hex = c.toString(16);
      return hex.length == 1 ? "0" + hex : hex;
    }

    function rgbToHex(color) {
      arr = color.replace('rgb', '').replace('(', '').replace(')', '').split(',');
      return "#" + componentToHex(Number(arr[0])) + componentToHex(Number(arr[1])) + componentToHex(Number(arr[2]));
    }

    function showColorPalette() {
      colorPalette.style.display = 'block';
      var newDiv = '<div class="color-option" style="background-color:#000000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#191919" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#323232" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#4b4b4b" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#646464" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#7d7d7d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#969696" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#afafaf" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#c8c8c8" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#e1e1e1" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffffff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#820000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#9b0000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b40000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#cd0000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#e60000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff0000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff1919" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff3232" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff4b4b" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff6464" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff7d7d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#823400" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#9b3e00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b44800" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#cd5200" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#e65c00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff6600" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff7519" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff8532" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff944b" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffa364" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffb27d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#828200" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#9b9b00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b4b400" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#cdcd00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#e6e600" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffff00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffff19" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffff32" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffff4b" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffff64" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ffff7d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#003300" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#004d00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#008000" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#00b300" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#00cc00" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#00e600" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#1aff1a" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#4dff4d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#66ff66" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#80ff80" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b3ffb3" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#001a4d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#002b80" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#003cb3" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#004de6" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#0000ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#0055ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#3377ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#4d88ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#6699ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#80b3ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b3d1ff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#003333" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#004d4d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#006666" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#009999" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#00cccc" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#00ffff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#1affff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#33ffff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#4dffff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#80ffff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b3ffff" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#4d004d" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#602060" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#660066" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#993399" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ac39ac" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#bf40bf" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#c653c6" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#cc66cc" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#d279d2" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#d98cd9" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#df9fdf" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#660029" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#800033" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#b30047" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#cc0052" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#e6005c" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff0066" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff1a75" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff3385" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff4d94" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff66a3" onclick="chooseColor(event)"></div><div class="color-option" style="background-color:#ff99c2" onclick="chooseColor(event)"></div>';
      colorPalette.innerHTML = newDiv;
    }


    var imageLoader = document.getElementById('importBackground');
        imageLoader.addEventListener('change', handleImage, false);

    function handleImage(e){
        var reader = new FileReader();
        reader.onload = function(event){
            var img = new Image();
            img.onload = function(){
                canvas_data.background = img;
                ratio = img.width / img.height;
                resize();
            }
            img.src = event.target.result;
        }
        reader.readAsDataURL(e.target.files[0]);
    }

    // Lagekarte speichern
    $("#speichern").click(function() {
        img = canvas_data.background;
        canvas_data.background = img.src;
        $.post(location.pathName, {
            'image': canvas.toDataURL(),
            'canvas_data': JSON.stringify(canvas_data)
        },
        function(){
            location.reload();
        });
        canvas_data.background = img;
        }
    )

    // ##############################################################################################
    // Text zu Lagekarte hinzufügen
    $("#addText").click(function () {
        let text_height = Stiftdicke * 5;
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

    // Default behaviour is drag&drop
    cursor();
}

// clear the canvas & redraw everything
function redraw() {
    prevColor = ctx.strokeStyle;
    ctx.clearRect(0, 0, width, height);
    addBackground();
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
    ctx.lineWidth = Stiftdicke;
    ctx.strokeStyle = prevColor;
}

function addBackground(){
    if (canvas_data.background !== null) { //Array.isArray(canvas_data.background) && canvas_data.background.length
        ctx.drawImage(canvas_data.background,0,0,width, height);
    }
}

// alte Lagekarte als Canvas Hintergrund setzen
$(".Archivkarte").click(function() {
    canvas_data = JSON.parse($(this).attr("alt"));
    let img = new Image();
    img.src = canvas_data.background;
    img.onload = function(){
        canvas_data.background = img;
        ratio = img.width / img.height;
        resize();
    }
})

function resize() {
    let oldImage = ctx.getImageData(0,0,canvas.width,canvas.height);
    var oldWidth = canvas.width;
    var oldHeight = canvas.height;
    var canvas_width = canvas.parentElement.parentElement.clientWidth - 40;
    var canvas_height = Math.round(canvas_width / ratio);

    if(canvas_height>window.innerHeight*0.8){
        canvas_height=window.innerHeight*0.8;
        canvas_width=canvas_height * ratio;
    }
    canvas.width = canvas_width;
    canvas.height = canvas_height;
    width = canvas_width;
    height = canvas_height;
    redraw();
}

$(window).resize(function(){resize();});
$(resize());
