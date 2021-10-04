// Javascript's Sleep
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}

// A function to generate random color
function getRndColor(min, max) {
    var r = min + (max - min) * Math.random() | 0,
        g = min + (max - min) * Math.random() | 0,
        b = min + (max - min) * Math.random() | 0;
    return 'rgb(' + r + ',' + g + ',' + b + ')';
}

// The canvas type for round rectangle
CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius = 40) {
    if (width < 2 * radius) radius = width / 2;
    if (height < 2 * radius) radius = height / 2;
    this.beginPath();
    this.moveTo(x + radius, y);
    this.arcTo(x + width, y, x + width, y + height, radius);
    this.arcTo(x + width, y + height, x, y + height, radius);
    this.arcTo(x, y + height, x, y, radius);
    this.arcTo(x, y, x + width, y, radius);
    this.closePath();
    this.fill();
    return this;
}


// A function to make line breaks
function lineBreak(str, width, maxLine = -1, font = "20px Corbel") { // width in px
    ret = "";
    tmp = str;
    lineCnt = 1;

    $("#hiddenSpan").attr("style", "display:none;font:" + font);
    $("#hiddenSpan").html(str);
    if ($("#hiddenSpan").width() <= width) {
        return str;
    }
    
    while (str.length > 0 && (maxLine == -1 || maxLine != -1 && lineCnt <= maxLine)) {
        if (lineCnt == maxLine) { // Line count limit: remove extra characters, use ... instead
            // Get line content (start from 1 character)
            lineLen = 1;
            $("#hiddenSpan").html(str.substr(0, lineLen));
            while ($("#hiddenSpan").width() <= width) {
                if(lineLen == str.length){
                    ret += str.substr(0,lineLen);
                    return ret;
                }
                lineLen += 1;
                $("#hiddenSpan").html(str.substr(0, lineLen));
            }

            // Replace the last characters with ...
            $("#hiddenSpan").html(str.substr(0, lineLen) + "...");
            while ($("#hiddenSpan").width() > width && lineLen > 0) {
                lineLen -= 1;
                $("#hiddenSpan").html(str.substr(0, lineLen) + "...");
            }
            ret += str.substr(0, lineLen) + "...";
            return ret;
        } else { // Line count not limited
            // Get line content (start from 1 character)
            lineLen = 1;
            $("#hiddenSpan").html(str.substr(0, lineLen));
            while ($("#hiddenSpan").width() <= width) {
                if(lineLen == str.length){
                    ret += str.substr(0,lineLen);
                    return ret;
                }
                lineLen += 1;
                $("#hiddenSpan").html(str.substr(0, lineLen));
            }

            // Add content to return data
            lineLen -= 1;
            ret += str.substr(0, lineLen) + "\n";
            if (str.length - lineLen <= 0) {
                break;
            }
            str = str.substr(lineLen, str.length - lineLen);

            lineCnt += 1;
        }
    }

    return ret;
}

function getWidth(str, font = "20px Corbel"){
    $("#hiddenSpan").attr("style", "display:none;font:" + font);
    $("#hiddenSpan").html(str);
    return $("#hiddenSpan").width();
}