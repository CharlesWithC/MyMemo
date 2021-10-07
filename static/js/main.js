// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

// Define canvas
var canvas = document.getElementById("canvas");
var ctx = canvas.getContext('2d');

// Check device
var isphone = 0;
if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
    isphone = 1;
}





// Prepare display settings for different types of devices

var fontSize = 40;
var smallFontSize = 20;
var largeFontSize = 60;
var orgFontSize = 40;
var orgsmallFontSize = 20;
var orglargeFontSize = 60;

var btnMargin = 0.5;
var bottomOffset = 100;

var buttons = [];
var btncnt = 26;

if (isphone) {
    fontSize = 60;
    smallFontSize = 40;
    largeFontSize = 80;
    orgFontSize = 60;
    orgsmallFontSize = 40;
    orglargeFontSize = 80;

    btnMargin = 0.2;
    bottomOffset = 250;
}

var windowOrgW = 1536;
var windowOrgH = 864;
buttons[0]={name:"start",x:0,y:0,w:300,h:50,orgw:300,orgh:50},
buttons[6]={name:"tag",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[11]={name:"remove",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[1]={name:"previous",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[2]={name:"next",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[3]={name:"sound",x:0,y:0,w:50,h:50,orgw:50,orgh:50},
buttons[13]={name:"pauseap",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[16]={name:"challengeyes",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[17]={name:"challengeno",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[15]={name:"mode0",x:0,y:0,w:250,h:50,orgw:250,orgh:50},
buttons[4]={name:"mode1",x:0,y:0,w:170,h:50,orgw:170,orgh:50},
buttons[5]={name:"mode2",x:0,y:0,w:170,h:50,orgw:170,orgh:50},
buttons[7]={name:"mode3",x:0,y:0,w:170,h:50,orgw:170,orgh:50},
buttons[10]={name:"mode4",x:0,y:0,w:170,h:50,orgw:170,orgh:50},
buttons[8]={name:"homepage",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[14]={name:"settings",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[20]={name:"account",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[18]={name:"statistics",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[22]={name:"wordbook",x:0,y:0,w:300,h:50,orgw:200,orgh:50},
buttons[9]={name:"import",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[12]={name:"export",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[19]={name:"addword",x:0,y:0,w:300,h:50,orgw:300,orgh:50},
buttons[21]={name:"cleardeleted",x:0,y:0,w:500,h:50,orgw:500,orgh:50},
buttons[23]={name:"createwordbook",x:0,y:0,w:500,h:50,orgw:500,orgh:50},
buttons[24]={name:"wordbookaddword",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[25]={name:"selectwordbook",x:0,y:0,w:200,h:50,orgw:200,orgh:50};

var wordBookW = 300;
var wordBookH = 150;
var wordBookOrgW = 300;
var wordBookOrgH = 150;

if (isphone) {
    for (var i = 0; i < btncnt; i++) {
        buttons[i].w = buttons[i].orgw * 2.5;
        buttons[i].h = buttons[i].orgw * 2.5;
    }
}


// Initialize button position

function btninit() {
    for (var i = 0; i < btncnt; i++) {
        buttons[i].x = canvas.width + 5000;
        buttons[i].y = canvas.height + 5000;
    }
}

function btnresize() {
    for (var i = 0; i < btncnt; i++) {
        buttons[i].w = Math.min(buttons[i].orgw, parseInt(buttons[i].orgw * window.innerWidth / windowOrgW * window.innerHeight / windowOrgH));
        buttons[i].h = Math.min(buttons[i].orgh, parseInt(buttons[i].orgh * window.innerHeight / windowOrgH * window.innerWidth / windowOrgW * 1.2));
    }
    wordBookW = Math.min(wordBookOrgW, parseInt(wordBookOrgW * window.innerWidth / windowOrgW * window.innerHeight / windowOrgH));
    wordBookH = Math.min(wordBookOrgH, parseInt(wordBookOrgH * window.innerWidth / windowOrgW * window.innerHeight / windowOrgH));
}

function fontresize() {
    fontSize = Math.min(orgFontSize, parseInt(orgFontSize * window.innerWidth / windowOrgW));
    largeFontSize = Math.min(orglargeFontSize, parseInt(orglargeFontSize * window.innerWidth / windowOrgW));
    smallFontSize = Math.min(orgsmallFontSize, parseInt(orgsmallFontSize * window.innerWidth / windowOrgW));

    if (isphone) {
        fontSize *= 1.5;
        largeFontSize *= 1.5;
        smallFontSize *= 1.5;
    }
}
btninit();
btnresize();
fontresize();





// Check network status

validateMsg = (Math.random()).toString();
$.ajax({
    url: "/ping",
    method: 'POST',
    async: false,
    dataType: "json",
    data: {
        "msg": validateMsg
    },
    success: function (r) {
        if (r.msg != validateMsg) {
            alert("It seems that you or the server is not online, offline mode is enabled automatically!");
            displayMode = 2;
            localStorage.setItem("displayMode", "2");
        }
    },
    erorr: function (r) {
        alert("It seems that you or the server is not online, offline mode is enabled automatically!");
        displayMode = 2;
        localStorage.setItem("displayMode", "2");
    }
});




// Settings variables

var started = 0;
var random = localStorage.getItem("random");
if (random == null) {
    random = 0;
}
random = parseInt(random);
var swap = localStorage.getItem("swap");
if (swap == null) {
    swap = 0;
}
swap = parseInt(swap);
var showStatus = localStorage.getItem("showStatus"); //1: default (normal + tagged) | 2: tagged | 3: deleted
if (showStatus == null) {
    showStatus = 1;
}
showStatus = parseInt(showStatus);
var autoPlay = localStorage.getItem("autoPlay");
if (autoPlay == null) {
    autoPlay = 0; //0: none | 1: slow (8 sec) | 2:medium (5 sec) | 3.fast (3 sec)
}
autoPlay = parseInt(autoPlay);
var apinterval = -1;
var appaused = 1;

displayMode = localStorage.getItem("displayMode");
if (displayMode == null) {
    displayMode = 0;
}
displayMode = parseInt(displayMode);

var wordId = localStorage.getItem("wordId");

var selectedWordBook = localStorage.getItem("selectedWordBook");
if (selectedWordBook == null) {
    selectedWordBook = 0;
    localStorage.setItem("selectedWordBook", "0");
}
selectedWordBook = parseInt(selectedWordBook);
var selectedWordBookName = "";

var word = "";
var displayId = -1;
var displayWord = "";
var displayTranslation = "";
var translation = "";
var wordStatus = 0;

var lastpage = 0;
var currentpage = localStorage.getItem("currentpage");
// 0: homepage, 1: wordpage, 2: settings, 3: addword, 4: wordlist, 5: wordbook, 6: wordbook-addword
if (currentpage == null) {
    currentpage = 0;
    localStorage.setItem("currentpage", "0");
}
if(currentpage == 3){
    currentpage = 0;
}


var statson = 0; // statistics ondisplay
var speaker = window.speechSynthesis;

var displayingAnswer = 0;

var challengeStatus = 0;

var wordBookId = localStorage.getItem("wordBookId");
if (wordBookId == null) {
    wordBookId = 0;
    localStorage.setItem("wordBookId", "0");
}
wordBookId = parseInt(wordBookId);
var wordBookName = "";

var wordBookRect = [];
var wordBookCnt = 1;

var wordBookShareCode = "";

var wordBookList = JSON.parse(localStorage.getItem("wordBookList"));
if (wordBookList == null || wordBookList.length == 0) {
    wordBookList = [];
    localStorage.setItem("wordBookList", JSON.stringify(wordBookList));
}
wordBookCnt = wordBookList.length;

var lastWordBookListUpdate = Date.now();





// Fetch word list

$('#wordList').DataTable({
    pagingType: "full_numbers"
});
$("#wordList_length").append('&nbsp;&nbsp;|&nbsp;&nbsp;<a onClick="selectAll();">Select All</a>');
$("#wordList_length").append('&nbsp;&nbsp;|&nbsp;&nbsp;<a onClick="deselectAll();">Deselect All</a>');
$("#wordList_length").append('&nbsp;&nbsp;|&nbsp;&nbsp;Double click word to edit');
$("#wordList_wrapper").hide();
$("#wordList").show();

var selected = [];

var wordList = JSON.parse(localStorage.getItem("wordList"));
var selectedWordList = [];
if (wordList == null) {
    wordList = [];
    localStorage.setItem("wordList", JSON.stringify([]));
} else {
    table = $("#wordList").DataTable();

    table.clear();
    table.draw();

    l = ["", "Default", "Tagged", "Deleted"];
    for (var i = 0; i < wordList.length; i++) {
        table.row.add([
            [wordList[i].word],
            [wordList[i].translation],
            [l[wordList[i].status]]
        ]).node().id = wordList[i].wordId;
    }
    table.draw();
}
var wordListMap = new Map();
for (var i = 0; i < wordList.length; i++) {
    wordListMap.set(wordList[i].wordId, {
        "word": wordList[i].word,
        "translation": wordList[i].translation,
        "status": wordList[i].status
    });
}


function updateTable() {
    if(wordBookList.length == 0){
        return;
    }
    table = $("#wordList").DataTable();
    table.clear();
    wordBookIdx = 0;
    for (var i = 0; i < wordBookList.length; i++) {
        if (wordBookList[i].wordBookId == wordBookId) {
            wordBookIdx = i;
            break;
        }
    }

    for (var i = 0; i < wordBookList[wordBookIdx].words.length; i++) {
        wordId = wordBookList[wordBookIdx].words[i];
        wordData = wordListMap.get(wordId);
        if (wordData == undefined) continue;
        table.row.add([
            [wordData.word],
            [wordData.translation],
            [l[wordData.status]]
        ]).node().id = wordId;
    }
    table.draw();
}

// Update word list each 10 minutes

var lastWordListUpdate = Date.now();

function updateWordList(doasync = true, forceUpdate = false) {
    if (Date.now() - lastWordListUpdate < 10000 && !forceUpdate) { // only one update each 10 seconds
        updateTable();
        return;
    }
    lastWordListUpdate = Date.now();
    $.ajax({
        url: "/api/getWordList",
        method: 'POST',
        async: doasync,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            wordList = r;
            wordListMap = new Map();
            for (var i = 0; i < wordList.length; i++) {
                wordListMap.set(wordList[i].wordId, {
                    "word": wordList[i].word,
                    "translation": wordList[i].translation,
                    "status": wordList[i].status
                });
            }

            l = ["", "Default", "Tagged", "Deleted"];
            localStorage.setItem("wordList", JSON.stringify(wordList));

            words = [];
            for (var i = 0; i < wordList.length; i++) {
                words.push(wordList[i].wordId);
            }
            updateTable();
        },
        error: function (r) {
            updateTable();
        }
    });
}
updateWordList(true, true);
setInterval(updateWordList, 600000);


// Update word book list each 10 minutes

function updateWordBookList(doasync = true, forceUpdate = false) {
    if (Date.now() - lastWordBookListUpdate < 30000 && !forceUpdate) { // only one update each 30 seconds
        return;
    }
    lastWordBookListUpdate = Date.now();
    $.ajax({
        url: "/api/getWordBookList",
        method: 'POST',
        async: doasync,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            words = [];
            for (var i = 0; i < wordList.length; i++) {
                words.push(wordList[i].wordId);
            }

            wordBookList = [];
            for (var i = 0; i < r.length; i++) {
                wordBookList.push(r[i]);
            }
            wordBookCnt = wordBookList.length;
            localStorage.setItem("wordBookList", JSON.stringify(wordBookList));

            for (var i = 0; i < wordBookList.length; i++) {
                if (wordBookList[i].wordBookId == wordBookId) {
                    wordBookName = wordBookList[i].name;
                    wordBookShareCode = wordBookList[i].shareCode;
                }
                if (wordBookList[i].wordBookId == selectedWordBook) {
                    selectedWordBookName = wordBookList[i].name;
                    selectedWordList = [];
                    for (var j = 0; j < wordBookList[i].words.length; j++) {
                        wordId = wordBookList[i].words[j];
                        wordData = wordListMap.get(wordId);
                        selectedWordList.push({
                            "wordId": wordId,
                            "word": wordData.word,
                            "translation": wordData.translation,
                            "status": wordData.status
                        });
                    }
                }
            }
        }
    });
}
updateWordBookList(true, true);
setInterval(updateWordBookList, 600000);

for (var i = 0; i < wordBookList.length; i++) {
    if (wordBookList[i].wordBookId == wordBookId) {
        wordBookName = wordBookList[i].name;
        wordBookShareCode = wordBookList[i].shareCode;
    }
    if (wordBookList[i].wordBookId == selectedWordBook) {
        selectedWordBookName = wordBookList[i].name;
        selectedWordList = [];
        for (var j = 0; j < wordBookList[i].words.length; j++) {
            wordId = wordBookList[i].words[j];
            wordData = wordListMap.get(wordId);
            selectedWordList.push({
                "wordId": wordId,
                "word": wordData.word,
                "translation": wordData.translation,
                "status": wordData.status
            });
        }
    }
}

function updateWordBookWordList(forceUpdate = false) {
    table = $("#wordList").DataTable();
    table.clear();
    table.row.add([
        [""],
        ["Loading..."],
        [""]
    ])
    table.draw();

    updateWordBookList(false, forceUpdate);
    if (Date.now() - lastWordListUpdate < 10000 && !forceUpdate) { // only one update each 10 seconds
        updateTable();
        return;
    }
    updateWordList(true, forceUpdate);
}
updateWordBookWordList();

function selectAll() {
    $("#wordList tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && !$(this).hasClass("selected")) { // check for NaN
            selected.push(wid);
        }

        $(this).addClass("selected");
    });
}

function deselectAll() {
    $("#wordList tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && $(this).hasClass("selected")) { // check for NaN
            idx = selected.indexOf(wid);
            if (idx > -1) {
                selected.splice(idx, 1);
            }
        }

        $(this).removeClass("selected");
    });
}




// Prepare word to show

if (wordId != null) {
    if (localStorage.getItem("userId") != null || localStorage.getItem("token") != "") {
        // Get the word to start from
        $.ajax({
            url: '/api/getWord',
            method: 'POST',
            async: false,
            dataType: "json",
            data: {
                wordId: wordId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                word = r.word;
                translation = r.translation;
                wordStatus = r.status;
            },
            error: function (r) {
                // Connection failed, check local word list
                for (var i = 0; i < selectedWordList.length; i++) {
                    if (selectedWordList[i].wordId == wordId) {
                        word = selectedWordList[i].word;
                        translation = selectedWordList[i].translation;
                        wordStatus = selectedWordList[i].status;
                    }
                }
            }
        });
    } else {
        // Connection failed, check local word list
        for (var i = 0; i < selectedWordList.length; i++) {
            if (selectedWordList[i].wordId == wordId) {
                word = selectedWordList[i].word;
                translation = selectedWordList[i].translation;
                wordStatus = selectedWordList[i].status;
            }
        }
    }
}

// Word does not exist
if (word == "") { // Then show a random word to start from
    if (selectedWordList.length != 0) {
        index = parseInt(Math.random() * selectedWordList.length);
        wordId = selectedWordList[index].wordId;
        word = selectedWordList[index].word;
        translation = selectedWordList[index].translation;
        wordStatus = selectedWordList[index].status;

        $("#startfrom").val(word);
    }
}

lastInputChange = 0;

function displayRandomWord() {
    if (selectedWordList.length != 0) {
        index = parseInt(Math.random() * selectedWordList.length);
        wordId = selectedWordList[index].wordId;
        word = selectedWordList[index].word;
        translation = selectedWordList[index].translation;
        wordStatus = selectedWordList[index].status;

        $("#startfrom").val(word);
    }
}

$('#startfrom').on('input', function () {
    lastInputChange = Date.now();
});
var randomDisplayer = setInterval(displayRandomWord, 5000);




// Start rendering

// Render home page on canvas
function renderHomePage() {
    btninit();
    $("#wordList_wrapper").hide();

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Render buttons
    // Title
    ctx.textAlign = "center";

    ctx.font = largeFontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100)
    ctx.fillText("Word Memo", canvas.width / 2, canvas.height / 2 - 100);

    // Content
    buttons[0].x = canvas.width / 2 - buttons[0].w / 2;
    buttons[0].y = canvas.height / 2 + buttons[0].h;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[0].x, buttons[0].y, buttons[0].w, buttons[0].h);
    ctx.font = fontSize + "px Corbel";

    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Start", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h / 1.4);
    if (displayMode == 0) {
        ctx.fillText("Practice Mode", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h * 2.2);
    } else if (displayMode == 1) {
        ctx.fillText("Challenge Mode", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h * 2.2);
    } else if (displayMode == 2) {
        ctx.fillText("Offline Mode", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h * 2.2);
    }

    ctx.fillText(selectedWordBookName, buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h * 3.4);

    ////
    buttons[20].x = canvas.width - buttons[20].w * 1.2;
    buttons[20].y = buttons[20].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[20].x, buttons[20].y, buttons[20].w, buttons[20].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Account", buttons[20].x + buttons[20].w / 2, buttons[20].y + buttons[20].h / 1.4);
    ////
    buttons[14].x = canvas.width - buttons[14].w * 1.2;
    buttons[14].y = buttons[14].h * 1.5;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[14].x, buttons[14].y, buttons[14].w, buttons[14].h);

    ctx.font = fontSize * 0.9 + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Settings", buttons[14].x + buttons[14].w / 2, buttons[14].y + buttons[14].h / 1.4);
    ////
    buttons[22].x = buttons[22].w * 0.2;
    buttons[22].y = buttons[22].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[22].x, buttons[22].y, buttons[22].w, buttons[22].h);

    ctx.font = fontSize * 0.6 + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Word Books", buttons[22].x + buttons[22].w / 2, buttons[22].y + buttons[22].h / 1.4);

    // Render the input box "Start from"
    $("#startfrom").attr("style", "position:absolute;left:" + (buttons[0].x + 15) + ";top:" + (buttons[0].y - buttons[0].h - 20) + ";height:" + (buttons[0].h) + ";width:" + (buttons[0].w - 14) + ";font-size:" + fontSize * 0.6 + ";font-family:Corbel");
    if (displayMode == 1) {
        $("#startfrom").attr("disabled", "disabled");
    } else {
        $("#startfrom").removeAttr("disabled");
    }
    if (randomDisplayer == -1) {
        randomDisplayer = setInterval(displayRandomWord, 5000);
    }
}

// Render settings buttons on canvas
function renderSettings() {
    if (randomDisplayer != -1) {
        clearInterval(randomDisplayer);
        randomDisplayer = -1;
    }
    $("#addword_word").val("");
    $("#addword_word").hide();
    $("#addword_translation").val("");
    $("#addword_translation").hide();
    btninit();

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Render buttons
    ctx.textAlign = "center";

    buttons[15].x = canvas.width / 2 + buttons[15].w / 2.5;
    buttons[15].y = buttons[15].h * 2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[15].x, buttons[15].y, buttons[15].w, buttons[15].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Mode:", buttons[15].x - buttons[15].w * 0.7, buttons[15].y + buttons[15].h / 1.4);
    l = ["Practice", "Challenge", "Offline"];
    ctx.fillText(l[displayMode], buttons[15].x + buttons[15].w / 2, buttons[15].y + buttons[15].h / 1.4);
    ////
    if (displayMode == 0 || displayMode == 2) {
        buttons[4].x = canvas.width / 2 + buttons[4].w / 1.2;
        buttons[4].y = buttons[4].h * 3.5;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[4].x, buttons[4].y, buttons[4].w, buttons[4].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Display order: ", buttons[4].x - buttons[4].w * 1.2, buttons[4].y + buttons[4].h / 1.4);
        l = ["Sequence", "Random"]
        ctx.fillText(l[random], buttons[4].x + buttons[4].w / 2, buttons[4].y + buttons[4].h / 1.4);
        ////
        buttons[5].x = canvas.width / 2 + buttons[5].w / 1.2;
        buttons[5].y = buttons[5].h * 5;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[5].x, buttons[5].y, buttons[5].w, buttons[5].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Swap word & translation? ", buttons[5].x - buttons[5].w * 1.4, buttons[5].y + buttons[5].h / 1.4);
        l = ["No", "Yes"];
        ctx.fillText(l[swap], buttons[5].x + buttons[5].w / 2, buttons[5].y + buttons[5].h / 1.4);
        ////
        buttons[7].x = canvas.width / 2 + buttons[7].w / 1.2;
        buttons[7].y = buttons[7].h * 6.5;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[7].x, buttons[7].y, buttons[7].w, buttons[7].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("What to show? ", buttons[7].x - buttons[7].w * 1.2, buttons[7].y + buttons[7].h / 1.4);
        l = ["", "All", "Tagged", "Deleted"];
        ctx.fillText(l[showStatus], buttons[7].x + buttons[7].w / 2, buttons[7].y + buttons[7].h / 1.4);
        ////
        buttons[10].x = canvas.width / 2 + buttons[10].w / 1.2;
        buttons[10].y = buttons[10].h * 8;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[10].x, buttons[10].y, buttons[10].w, buttons[10].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Auto play:", buttons[10].x - buttons[10].w * 1.2, buttons[10].y + buttons[10].h / 1.4);
        l = ["Disabled", "Slow", "Medium", "Fast"];
        ctx.fillText(l[autoPlay], buttons[10].x + buttons[10].w / 2, buttons[10].y + buttons[10].h / 1.4);

    } else if (displayMode == 1) {
        x = canvas.width / 2 + buttons[4].w / 1.2;
        y = buttons[4].h * 3.5;
        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Display order: ", x - buttons[4].w * 1.2, y + buttons[4].h / 1.4);
        ctx.fillText("Random", x + buttons[4].w / 2, y + buttons[4].h / 1.4);

        buttons[5].x = canvas.width / 2 + buttons[5].w / 1.2;
        buttons[5].y = buttons[5].h * 5;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[5].x, buttons[5].y, buttons[5].w, buttons[5].h);
        ctx.font = fontSize + "px Corbel";

        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Swap word & translation? ", buttons[5].x - buttons[5].w * 1.4, buttons[5].y + buttons[5].h / 1.4);
        l = ["No", "Yes"];
        ctx.fillText(l[swap], buttons[5].x + buttons[5].w / 2, buttons[5].y + buttons[5].h / 1.4);
        ////
        x = canvas.width / 2 + buttons[7].w / 1.2;
        y = buttons[7].h * 6.5;
        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("What to show? ", x - buttons[7].w * 1.2, y + buttons[7].h / 1.4);
        ctx.fillText("Everything", x + buttons[7].w / 2, y + buttons[7].h / 1.4);
        ////
        x = canvas.width / 2 + buttons[10].w / 1.2;
        y = buttons[10].h * 8;
        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Auto play:", x - buttons[10].w * 1.2, y + buttons[10].h / 1.4);
        ctx.fillText("Disabled", x + buttons[10].w / 2, y + buttons[10].h / 1.4);
    }

    buttons[19].x = canvas.width / 2 - buttons[19].w / 2;
    buttons[19].y = canvas.height - buttons[19].h * 4;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[19].x, buttons[19].y, buttons[19].w, buttons[19].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Add Word", buttons[19].x + buttons[19].w / 2, buttons[19].y + buttons[19].h / 1.4);
    ////
    buttons[21].x = canvas.width / 2 - buttons[21].w / 2;
    buttons[21].y = canvas.height - buttons[21].h * 2.5;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[21].x, buttons[21].y, buttons[21].w, buttons[21].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Clear deleted words", buttons[21].x + buttons[21].w / 2, buttons[21].y + buttons[21].h / 1.4);
    ////
    buttons[9].x = canvas.width / 2 - buttons[9].w * (1 + btnMargin * 0.6);
    buttons[9].y = canvas.height - buttons[9].h * 1.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[9].x, buttons[9].y, buttons[9].w, buttons[9].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Import", buttons[9].x + buttons[9].w / 2, buttons[9].y + buttons[9].h / 1.4);
    ////
    buttons[12].x = canvas.width / 2 + buttons[12].w * btnMargin * 0.6;
    buttons[12].y = canvas.height - buttons[12].h * 1.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[12].x, buttons[12].y, buttons[12].w, buttons[12].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Export", buttons[12].x + buttons[12].w / 2, buttons[12].y + buttons[12].h / 1.4);

    if (lastpage != 1) {
        buttons[8].x = buttons[8].w * 0.2;
        buttons[8].y = buttons[8].h * 0.2;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Home", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);
    } else if (lastpage == 1) {
        buttons[0].x = buttons[8].w * 0.2;
        buttons[0].y = buttons[8].h * 0.2;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[0].x, buttons[0].y, buttons[8].w, buttons[8].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Resume", buttons[0].x + buttons[8].w / 2, buttons[0].y + buttons[8].h / 1.4);
    }

    // Add title
    ctx.font = fontSize + "px Impact";
    ctx.fillText("Settings", canvas.width / 2, buttons[8].h * 0.2 + buttons[8].h / 1.4);
}

var editWord = false;
var editWordId = -1;

function renderAddWord() {
    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Create addword textarea box
    ctx.textAlign = "center";

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Word: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 - 100);
    $("#addword_word").attr("style", "position:absolute;left:" + (canvas.width / 2) + ";top:" + (canvas.height / 2 - 118) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("Translation: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 - 50);
    $("#addword_translation").attr("style", "position:absolute;left:" + (canvas.width / 2) + ";top:" + (canvas.height / 2 - 68) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    if (editWord) {
        $("#addword_word").val(wordListMap.get(editWordId).word);
        $("#addword_translation").val(wordListMap.get(editWordId).translation);
    }

    // Add buttons
    buttons[8].x = buttons[8].w * 0.2;
    buttons[8].y = buttons[8].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Back", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);
    ////
    buttons[19].x = canvas.width / 2 - buttons[19].w / 2;
    buttons[19].y = canvas.height - buttons[19].h * 3;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[19].x, buttons[19].y, buttons[19].w, buttons[19].h);
    ////
    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    if (!editWord)
        ctx.fillText("Add", buttons[19].x + buttons[19].w / 2, buttons[19].y + buttons[19].h / 1.4);
    else
        ctx.fillText("Edit", buttons[19].x + buttons[19].w / 2, buttons[19].y + buttons[19].h / 1.4);

    // Add title
    ctx.font = fontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    if (!editWord)
        ctx.fillText("Add Word", canvas.width / 2, buttons[8].h * 0.2 + buttons[8].h / 1.4);
    else
        ctx.fillText("Edit Word", canvas.width / 2, buttons[8].h * 0.2 + buttons[8].h / 1.4);
}

// Render word information on canvas
function renderWord(showSwapped = 0, cancelSpeaker = 0) {
    if (randomDisplayer != -1) {
        clearInterval(randomDisplayer);
        randomDisplayer = -1;
    }

    btninit();

    showWord = false;
    if (swap == 0 || swap == 1 && showSwapped == 1 || swap == 1 && challengeStatus == 1 || swap == 1 && challengeStatus == 3 || displayMode == 1 && wordId == -1) {
        showWord = true;
    }
    showTranslation = false;
    if (swap == 1 || swap == 0 && showSwapped == 1 || swap == 0 && challengeStatus == 1 || swap == 0 && challengeStatus == 3 || displayMode == 1 && wordId == -1) {
        showTranslation = true;
    }

    $("#hiddenSpan").attr("style", "display:none;font:" + fontSize + "px Corbel");
    $("#hiddenSpan").html("test");
    lineHeight = $("#hiddenSpan").height() + 5;
    maxw = window.innerWidth * 0.8;
    curh = window.innerHeight / 2 - 250;

    if (displayId != wordId) {
        displayWord = lineBreak(word, maxw, -1, (fontSize) + "px Corbel");
        displayTranslation = lineBreak(translation, maxw, -1, (fontSize) + "px Corbel");
        displayId = wordId;
    }

    requireH = curh + buttons[0].h * 6;
    if (showWord) {
        requireH += displayWord.split("\n").length * lineHeight;
    }
    if (showTranslation) {
        requireH += displayTranslation.split("\n").length * lineHeight;
    }

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = Math.max(window.innerHeight - 25, requireH);

    // Update word id
    localStorage.setItem("wordId", wordId);

    // Display word or translation
    ctx.font = fontSize + "px Corbel";
    ctx.textAlign = "center";
    ctx.fillStyle = "black";
    if (showWord) {
        var lines = displayWord.split('\n');
        for (var i = 0; i < lines.length; i++) {
            curh += lineHeight;
            ctx.fillText(lines[i], canvas.width / 2, curh);
        }
    }
    curh += 10;

    ctx.fillStyle = "gray";
    if (showTranslation) {
        var lines = displayTranslation.split('\n');
        for (var i = 0; i < lines.length; i++) {
            curh += lineHeight;
            ctx.fillText(lines[i], canvas.width / 2, curh);
        }
    }
    ctx.fillStyle = "black";
    $("#startfrom").val(word);

    // Get random color
    rectcolor = getRndColor(160, 250);
    textcolor = getRndColor(10, 100);

    if ((swap == 0 || swap == 1 && showSwapped == 1 || displayMode == 1 && challengeStatus > 0) && wordId != -1) {
        buttons[3].x = canvas.width / 2 - buttons[3].w / 2;
        buttons[3].y = canvas.height - bottomOffset;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[3].x, buttons[3].y, buttons[3].w, buttons[3].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        ctx.fillText("🔈", buttons[3].x + buttons[3].w / 2, buttons[3].y + buttons[3].h / 1.4);
    }

    if (displayMode == 0) { // Practice mode
        ctx.fillText("Practice Mode", canvas.width / 2, buttons[0].h * 0.2 + buttons[0].h / 1.4);

        // Render buttons
        buttons[1].x = canvas.width / 2 - buttons[1].w * (1 + btnMargin);
        buttons[1].y = canvas.height - bottomOffset;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        ctx.fillText("Previous", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
        ////
        buttons[2].x = canvas.width / 2 + buttons[2].w * btnMargin;
        buttons[2].y = canvas.height - bottomOffset;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[2].x, buttons[2].y, buttons[2].w, buttons[2].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        ctx.fillText("Next", buttons[2].x + buttons[2].w / 2, buttons[2].y + buttons[2].h / 1.4);
        ////
        buttons[6].x = canvas.width / 2 - buttons[6].w * (1 + btnMargin);
        buttons[6].y = canvas.height - bottomOffset - buttons[6].h * 1.5;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[6].x, buttons[6].y, buttons[6].w, buttons[6].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        if (wordStatus == 2)
            ctx.fillText("Untag", buttons[6].x + buttons[6].w / 2, buttons[6].y + buttons[6].h / 1.4);
        else
            ctx.fillText("Tag", buttons[6].x + buttons[6].w / 2, buttons[6].y + buttons[6].h / 1.4);
        ////
        buttons[11].x = canvas.width / 2 + buttons[11].w * btnMargin;
        buttons[11].y = canvas.height - bottomOffset - buttons[11].h * 1.5;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[11].x, buttons[11].y, buttons[11].w, buttons[11].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        if (wordStatus == 3) {
            ctx.font = (fontSize * 0.9) + "px Corbel";
            ctx.fillText("Undelete", buttons[11].x + buttons[11].w / 2, buttons[11].y + buttons[11].h / 1.4);
        } else
            ctx.fillText("Delete", buttons[11].x + buttons[11].w / 2, buttons[11].y + buttons[11].h / 1.4);

    } else if (displayMode == 1) { // Challenge mode
        ctx.fillText("Challenge Mode", canvas.width / 2, buttons[0].h * 0.2 + buttons[0].h / 1.4);

        if (wordId != -1) {
            if (challengeStatus != 3) {
                buttons[16].x = canvas.width / 2 - buttons[16].w * (1 + btnMargin);
                buttons[16].y = canvas.height - bottomOffset - buttons[16].h * 1.5;
                ctx.fillStyle = rectcolor;
                ctx.roundRect(buttons[16].x, buttons[16].y, buttons[16].w, buttons[16].h);

                ctx.font = fontSize + "px Corbel";
                ctx.fillStyle = textcolor;
                ctx.fillText("Yes", buttons[16].x + buttons[16].w / 2, buttons[16].y + buttons[16].h / 1.4);
            }

            ctx.textAlign = "center";
            if (challengeStatus == 0) {
                ctx.fillText("Do you remember it?", canvas.width / 2, buttons[16].y - buttons[16].h / 1.4);
            } else if (challengeStatus == 1) {
                ctx.fillText("Are you correct?", canvas.width / 2, buttons[16].y - buttons[16].h / 1.4);
            } else if (challengeStatus == 3) {
                x = canvas.width / 2 - buttons[16].w * (1 + btnMargin);
                y = canvas.height - bottomOffset - buttons[16].h * 1.5;
                ctx.fillText("Try to memorize it!", canvas.width / 2, y - buttons[16].h / 1.4);
            }
            ////
            buttons[17].x = canvas.width / 2 + buttons[17].w * btnMargin;
            buttons[17].y = canvas.height - bottomOffset - buttons[17].h * 1.5;
            ctx.fillStyle = rectcolor;
            ctx.roundRect(buttons[17].x, buttons[17].y, buttons[17].w, buttons[17].h);

            ctx.font = fontSize + "px Corbel";
            ctx.fillStyle = textcolor;
            if (challengeStatus != 3) {
                ctx.fillText("No", buttons[17].x + buttons[17].w / 2, buttons[17].y + buttons[17].h / 1.4);
            } else {
                ctx.fillText("Next", buttons[17].x + buttons[17].w / 2, buttons[17].y + buttons[17].h / 1.4);
            }
            ////
            buttons[6].x = canvas.width / 2 - buttons[6].w * (1 + btnMargin);
            buttons[6].y = canvas.height - bottomOffset;
            ctx.fillStyle = rectcolor;
            ctx.roundRect(buttons[6].x, buttons[6].y, buttons[6].w, buttons[6].h);

            ctx.font = fontSize + "px Corbel";
            ctx.fillStyle = textcolor;
            if (wordStatus == 2)
                ctx.fillText("Untag", buttons[6].x + buttons[6].w / 2, buttons[6].y + buttons[6].h / 1.4);
            else
                ctx.fillText("Tag", buttons[6].x + buttons[6].w / 2, buttons[6].y + buttons[6].h / 1.4);
            ////
            buttons[11].x = canvas.width / 2 + buttons[11].w * btnMargin;
            buttons[11].y = canvas.height - bottomOffset;
            ctx.fillStyle = rectcolor;
            ctx.roundRect(buttons[11].x, buttons[11].y, buttons[11].w, buttons[11].h);

            ctx.font = fontSize + "px Corbel";
            ctx.fillStyle = textcolor;
            if (wordStatus == 3) {
                ctx.font = (fontSize * 0.9) + "px Corbel";
                ctx.fillText("Undelete", buttons[11].x + buttons[11].w / 2, buttons[11].y + buttons[11].h / 1.4);
            } else
                ctx.fillText("Delete", buttons[11].x + buttons[11].w / 2, buttons[11].y + buttons[11].h / 1.4);
        }
    } else if (displayMode == 2) { // Offline mode
        ctx.fillText("Offline Mode", canvas.width / 2, buttons[0].h * 0.2 + buttons[0].h / 1.4);

        // Render buttons
        buttons[1].x = canvas.width / 2 - buttons[1].w * (1 + btnMargin);
        buttons[1].y = canvas.height - bottomOffset;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        ctx.fillText("Previous", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
        ////
        buttons[2].x = canvas.width / 2 + buttons[2].w * btnMargin;
        buttons[2].y = canvas.height - bottomOffset;
        ctx.fillStyle = rectcolor;
        ctx.roundRect(buttons[2].x, buttons[2].y, buttons[2].w, buttons[2].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = textcolor;
        ctx.fillText("Next", buttons[2].x + buttons[2].w / 2, buttons[2].y + buttons[2].h / 1.4);
    }

    // If autoplayer is on, then autoplay
    if (autoPlay != 0) {
        if (displayMode == 0) {
            buttons[13].x = canvas.width / 2 - buttons[13].w * (1 + btnMargin);
            buttons[13].y = canvas.height - bottomOffset - buttons[13].h * 3;
            ctx.fillStyle = rectcolor;
            ctx.roundRect(buttons[13].x, buttons[13].y, buttons[13].w, buttons[13].h);

            ctx.font = fontSize + "px Corbel";
            ctx.fillStyle = textcolor;
            if (appaused)
                ctx.fillText("Play", buttons[13].x + buttons[13].w / 2, buttons[13].y + buttons[13].h / 1.4);
            else
                ctx.fillText("Pause", buttons[13].x + buttons[13].w / 2, buttons[13].y + buttons[13].h / 1.4);
        } else if (displayMode == 2) {
            buttons[13].x = canvas.width / 2 - buttons[13].w * (1 + btnMargin);
            buttons[13].y = canvas.height - bottomOffset - buttons[13].h * 1.5;
            ctx.fillStyle = rectcolor;
            ctx.roundRect(buttons[13].x, buttons[13].y, buttons[13].w, buttons[13].h);

            ctx.font = fontSize + "px Corbel";
            ctx.fillStyle = textcolor;
            if (appaused)
                ctx.fillText("Play", buttons[13].x + buttons[13].w / 2, buttons[13].y + buttons[13].h / 1.4);
            else
                ctx.fillText("Pause", buttons[13].x + buttons[13].w / 2, buttons[13].y + buttons[13].h / 1.4);
        }
    }

    if (autoPlay != 0 && !appaused && !cancelSpeaker) {
        if (swap == 0) {
            speaker.cancel();
            msg = new SpeechSynthesisUtterance(word);
            speaker.speak(msg);
        }
    }

    if (displayMode != 2) {
        buttons[18].x = canvas.width - buttons[18].w * 1.2;
        buttons[18].y = buttons[18].h * 1.5;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[18].x, buttons[18].y, buttons[18].w, buttons[18].h);

        ctx.font = fontSize * 0.9 + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Statistics", buttons[18].x + buttons[18].w / 2, buttons[18].y + buttons[18].h / 1.4);
    }
    ////
    buttons[8].x = buttons[8].w * 0.2;
    buttons[8].y = buttons[8].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Home", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);
    ////
    buttons[14].x = canvas.width - buttons[14].w * 1.2;
    buttons[14].y = buttons[14].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[14].x, buttons[14].y, buttons[14].w, buttons[14].h);

    ctx.font = fontSize * 0.9 + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Settings", buttons[14].x + buttons[14].w / 2, buttons[14].y + buttons[14].h / 1.4);

    lastpage = 1;
}

// Render word book
function renderWordBook() {
    btninit();

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = Math.max(window.innerHeight - 25, buttons[0].h * 4 + wordBookH * Math.ceil(wordBookCnt / 4) * 1.1);

    // Render buttons
    ctx.textAlign = "center";

    buttons[8].x = buttons[8].w * 0.2;
    buttons[8].y = buttons[8].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Home", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);

    // Add title
    ctx.font = fontSize + "px Impact";
    ctx.fillText("Word Book", canvas.width / 2, buttons[8].h * 0.2 + buttons[8].h / 1.4);
    ctx.font = fontSize + "px Corbel";

    // Render word books
    wordBookRect = [];
    ctx.textAlign = "left";
    for (var i = 0; i < wordBookCnt; i++) {
        x = canvas.width + 1;
        y = canvas.height + 1;

        if (!isphone) {
            if (i % 4 == 0) {
                x = canvas.width / 2 - wordBookW * 2.15;
            } else if (i % 4 == 1) {
                x = canvas.width / 2 - wordBookW * 1.05;
            } else if (i % 4 == 2) {
                x = canvas.width / 2 + wordBookW * 0.05;
            } else if (i % 4 == 3) {
                x = canvas.width / 2 + wordBookW * 1.15;
            }

            y = buttons[8].y + buttons[8].h * 1.2 + parseInt(i / 4) * wordBookH * 1.1;
        } else {
            if (i % 2 == 0) {
                x = canvas.width / 2 - wordBookW * 1.05;
            } else if (i % 2 == 1) {
                x = canvas.width / 2 + wordBookW * 0.05;
            }

            y = buttons[8].y + buttons[8].h * 1.2 + parseInt(i / 2) * wordBookH * 1.1;
        }

        wordBookRect.push({
            "wordBookId": wordBookList[i].wordBookId,
            "x": x,
            "y": y
        });

        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(x, y, wordBookW, wordBookH);

        displayName = lineBreak(wordBookList[i].name, wordBookW * 6 / 8, maxLine = 2, font = (fontSize * 0.75) + "px Corbel");

        ctx.fillStyle = getRndColor(10, 150);
        ctx.font = fontSize * 0.75 + "px Corbel";
        var lines = displayName.split('\n');
        for (var j = 0; j < lines.length; j++) {
            ctx.fillText(lines[j], x + wordBookW / 8, y + wordBookH / (3.6 - 2 * j));
        }

        t = 2;
        if (lines.length == 2) {
            t = 1.2;
        }

        ctx.font = smallFontSize + "px Corbel";
        if (wordBookList[i].words.length <= 1) {
            ctx.fillText(wordBookList[i].words.length + " word", x + wordBookW / 8, y + wordBookH / t);
        } else {
            ctx.fillText(wordBookList[i].words.length + " words", x + wordBookW / 8, y + wordBookH / t);
        }
    }

    ctx.textAlign = "center";
    ctx.font = fontSize + "px Corbel";

    // Render add word book button
    $("#wordBookName").attr("style", "position:absolute;\
    left:" + (canvas.width / 2 - buttons[23].w - 10) + ";top:" + (canvas.height - buttons[23].h * 1.75) + ";\
    height:" + (buttons[23].h) + ";width:" + (buttons[23].w) + ";\
    font-size:" + fontSize * 0.6 + ";font-family:Corbel");
    $("#wordBookName").show();

    buttons[23].x = canvas.width / 2 + 10;
    buttons[23].y = canvas.height - buttons[23].h * 2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[23].x, buttons[23].y, buttons[23].w, buttons[23].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Create Word Book", buttons[23].x + buttons[23].w / 2, buttons[23].y + buttons[23].h / 1.4);
}

// Render word list using dataTables
function renderWordList() {
    btninit();

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Render buttons
    ctx.textAlign = "center";

    buttons[8].x = buttons[8].w * 0.2;
    buttons[8].y = buttons[8].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Back", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);
    ////
    color = getRndColor(160, 250);
    if (selectedWordBook == wordBookId)
        color = "#cccccc";
    buttons[25].x = canvas.width - buttons[25].w * 1.2;
    buttons[25].y = buttons[25].h * 0.2
    ctx.fillStyle = color;
    ctx.roundRect(buttons[25].x, buttons[25].y, buttons[25].w, buttons[25].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    if (selectedWordBook == wordBookId)
        ctx.fillText("Selected", buttons[25].x + buttons[25].w / 2, buttons[25].y + buttons[25].h / 1.4);
    else
        ctx.fillText("Select", buttons[25].x + buttons[25].w / 2, buttons[25].y + buttons[25].h / 1.4);

    // Add title
    ctx.font = fontSize + "px Impact";
    ctx.fillText(wordBookName, canvas.width / 2, buttons[8].h * 0.2 + buttons[8].h / 1.4);
    ctx.font = fontSize + "px Corbel";

    // Status update
    ctx.textAlign = "left";

    fs = smallFontSize;
    if(isphone) fs *= 0.6;
    ctx.font = fs + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    space = getWidth("-----");

    ctx.fillText("Word Status Update (Update the status of all selected words to):", buttons[0].w * 0.5, buttons[8].y + buttons[8].h * 1.8);
    
    ctx.fillText("Default", buttons[0].w * 0.5, buttons[8].y + buttons[8].h * 2.4);
    w1 = getWidth("Default", fs + "px Corbel") + space;
    ctx.fillText("Tag", buttons[0].w * 0.5 + w1, buttons[8].y + buttons[8].h * 2.4);
    w2 = getWidth("Tag", fs + "px Corbel") + space;
    ctx.fillText("Delete", buttons[0].w * 0.5 + w1 + w2, buttons[8].y + buttons[8].h * 2.4);
    w3 = getWidth("Delete", fs + "px Corbel") + space;

    // Word book update
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Word Book Update:", buttons[0].w * 0.5, buttons[8].y + buttons[8].h * 3);

    // If word list is all words
    // Then add new words refer to add new word to database
    // Instead of selecting words from all words
    // And remove selected words refer to remove all selected words permanently
    // Instead of removing them from specific word list
    ctx.fillText("Rename", buttons[0].w * 0.5, buttons[8].y + buttons[8].h * 3.6);
    w4 = getWidth("Rename", fs + "px Corbel") + space;
    ctx.fillText("Add", buttons[0].w * 0.5 + w4, buttons[8].y + buttons[8].h * 3.6);
    w5 = getWidth("Add", fs + "px Corbel") + space;
    ctx.fillText("Remove", buttons[0].w * 0.5 + w4 + w5, buttons[8].y + buttons[8].h * 3.6);
    w6 = getWidth("Remove", fs + "px Corbel") + space;
    if(wordBookId != 0){
        ctx.fillStyle = "red";
        ctx.fillText("Delete Word Book", buttons[0].w * 0.5 + w4 + w5 + w6, buttons[8].y + buttons[8].h * 3.6);
        w7 = getWidth("Delete Word Book", fs + "px Corbel") + space;
        ctx.fillStyle = getRndColor(10, 100);
    }
    
    // Word book update
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Share:", buttons[0].w * 0.5, buttons[8].y + buttons[8].h * 4.2);
    w8 = getWidth("Share:", fs + "px Corbel") + space;
    if(wordBookShareCode == ""){
        ctx.fillText("Private", buttons[0].w * 0.5 + w8, buttons[8].y + buttons[8].h * 4.2);
    } else {
        ctx.fillText(wordBookShareCode, buttons[0].w * 0.5 + w8, buttons[8].y + buttons[8].h * 4.2);
    }

    // Render table
    $("#wordList_wrapper").show();
    $("#wordList_wrapper").attr("style", "test-align:center;position:absolute;\
    left:" + (buttons[0].w * 0.5) + ";top:" + (buttons[8].x + buttons[8].h * 4.4) + ";\
    ;width:" + (window.innerWidth - 25 - buttons[0].w) + ";\
    font-size:" + fs + ";font-family:Corbel;z-index:999");
    $("#wordList").attr("style", "width:100%;font-size:" + smallFontSize * 0.8 + ";font-family:Corbel");
    updateTable();

    ctx.font = fontSize + "px Corbel";
}

// Render word book add word page
// A full word list
function renderWordBookAddWord() {
    btninit();

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Render buttons
    ctx.textAlign = "center";

    buttons[8].x = buttons[8].w * 0.2;
    buttons[8].y = buttons[8].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Back", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);
    ////
    buttons[24].x = canvas.width - buttons[24].w * 1.2;
    buttons[24].y = buttons[24].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[24].x, buttons[24].y, buttons[24].w, buttons[24].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Add", buttons[24].x + buttons[24].w / 2, buttons[24].y + buttons[24].h / 1.4);

    // Add title
    ctx.font = fontSize + "px Impact";
    ctx.fillText("Add word to " + wordBookName, canvas.width / 2, buttons[8].h * 0.2 + buttons[8].h / 1.4);
    ctx.font = fontSize + "px Corbel";

    // Status update
    ctx.textAlign = "left";
    ctx.font = smallFontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    space = getWidth("-----");

    // Render table
    $("#wordList_wrapper").show();
    $("#wordList_wrapper").attr("style", "test-align:center;position:absolute;\
    left:" + (buttons[0].w * 0.5) + ";top:" + (buttons[8].x + buttons[8].h * 1.2) + ";\
    ;width:" + (window.innerWidth - 25 - buttons[0].w) + ";\
    font-size:" + smallFontSize * 0.8 + ";font-family:Corbel;z-index:999");
    $("#wordList").attr("style", "width:100%;font-size:" + smallFontSize * 0.8 + ";font-family:Corbel");

    table = $("#wordList").DataTable();
    table.clear();
    table.row.add([
        [""],
        ["Loading..."],
        [""]
    ])
    table.draw();

    table.clear();

    curid = wordBookId;
    wordBookId = 0;
    updateWordList(false, true);
    wordBookId = curid;
}

// Render current page
var loaded = false;

function renderCurrentPage() {
    localStorage.setItem("currentpage", currentpage);
    wordBookRect = [];
    loaded = false;
    sleep(50).then(() => {
        $("#wordBookName").hide();
        $("#wordList_wrapper").hide();
        $("#startfrom").hide();
        $("#addword_word").hide();
        $("#addword_translation").hide();

        if (currentpage == 0) {
            renderHomePage();
        } else if (currentpage == 1) {
            renderWord();
        } else if (currentpage == 2) {
            renderSettings();
        } else if (currentpage == 3) {
            renderAddWord();
        } else if (currentpage == 4) {
            renderWordList();
        } else if (currentpage == 5) {
            renderWordBook();
        } else if (currentpage == 6) {
            renderWordBookAddWord();
        }
        loaded = true;
    })
}

function renderCurrentPageResize() {
    $('#wordList').DataTable().destroy();
    $('#wordList').DataTable({
        pagingType: "full_numbers"
    });
    $("#wordList_length").append('&nbsp;&nbsp;|&nbsp;&nbsp;<a onClick="selectAll();">Select All</a>');
    $("#wordList_length").append('&nbsp;&nbsp;|&nbsp;&nbsp;<a onClick="deselectAll();">Deselect All</a>');
    $("#wordList_length").append('&nbsp;&nbsp;|&nbsp;&nbsp;Double click word to edit');
    btnresize();
    fontresize();
    renderCurrentPage();
}

// Update canvas when page resizes to prevent content floating out of the page
if (!isphone) {
    window.onresize = renderCurrentPageResize;
}


// Auto word player
apdelay = [99999, 8, 5, 3];

function autoPlayer() { // = auto next button presser + sound maker
    console.log("auto player running");

    moveType = 1 - random;

    if (displayMode == 0) {
        // Get next word
        $.ajax({
            url: "/api/getNext",
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                wordId: wordId,
                status: showStatus,
                moveType: moveType,
                wordBookId: selectedWordBook,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                word = r.word;
                translation = r.translation;
                wordStatus = r.status;
                wordId = r.wordId;
                displayingAnswer = 0;
                renderCurrentPage();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    alert("Login session expired! Please login again!");
                    localStorage.removeItem("userId");
                    localStorage.removeItem("token");
                    window.location.href = "/user";
                } else {
                    $("#startfrom").hide();
                    word = r.status + " " + errorThrown;
                    translation = "Maybe change the settings?\nOr check your connection?";
                    renderWord(1, 1);
                }
            }
        });
    } else if (displayMode == 2) {
        displayingAnswer = 0;

        requiredList = [];
        for (var i = 0; i < selectedWordList.length; i++) {
            if (showStatus == 1 && (selectedWordList[i].status == 1 || selectedWordList[i].status == 2)) {
                requiredList.push(selectedWordList[i]);
            } else if (showStatus == 2 && selectedWordList[i].status == 2) {
                requiredList.push(selectedWordList[i]);
            } else if (showStatus == 3 && selectedWordList[i].status == 3) {
                requiredList.push(selectedWordList[i]);
            }
        }

        if (moveType == 0) {
            index = parseInt(Math.random() * requiredList.length);
            wordId = requiredList[index].wordId;
            word = requiredList[index].word;
            translation = requiredList[index].translation;
            wordStatus = requiredList[index].status;
        } else if (moveType == 1 || moveType == -1) {
            index = -1;
            for (var i = 0; i < requiredList.length; i++) {
                if (requiredList[i].wordId == wordId) {
                    index = i;
                    break;
                }
            }
            if (index == -1) {
                word = "";
                translation = "Unknown error";
                renderWord(1, 1);
                return;
            }

            if (moveType == -1 && index > 0 || moveType == 1 && index < requiredList.length - 1) {
                index += moveType;
            } else if (moveType == -1 && index == 0) {
                index = requiredList.length - 1;
            } else if (moveType == 1 && index == requiredList.length - 1) {
                index = 0;
            }

            wordId = requiredList[index].wordId;
            word = requiredList[index].word;
            translation = requiredList[index].translation;
            wordStatus = requiredList[index].status;
        }

        renderCurrentPage();
    }
}

function startfunc() {
    if (displayMode == 0) { // Practice mode
        // If autoplayer is on, then autoplay
        if ($("#startfrom").val() != "") {
            startword = $("#startfrom").val();
            // User decided a word to start from
            // Get its word id
            $.ajax({
                url: '/api/getWordId',
                method: 'POST',
                async: false,
                dataType: "json",
                data: {
                    word: startword,
                    userId: localStorage.getItem("userId"),
                    token: localStorage.getItem("token")
                },
                success: function (r) {
                    lastpage = currentpage;
                    currentpage = 1;
                    wordId = r.wordId;
                    started = 1;
                    btninit();

                    // Word exist and get info of the word
                    $.ajax({
                        url: '/api/getWord',
                        method: 'POST',
                        async: false,
                        dataType: "json",
                        data: {
                            wordId: wordId,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            word = r.word;
                            translation = r.translation;
                            wordStatus = r.status;
                            wordId = r.wordId;
                            renderCurrentPage();
                            if (apinterval == -1 && autoPlay != 0) {
                                apinterval = setInterval(autoPlayer, apdelay[autoPlay] * 1000);
                            }
                        },
                        error: function (r, textStatus, errorThrown) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            } else {
                                word = r.status + " " + errorThrown;
                                translation = "Maybe change the settings?\nOr check your connection?";
                                renderWord(1, 1);
                            }
                        }
                    });
                },

                // Word doesn't exist then start from default
                error: function (r, textStatus, errorThrown) {
                    if (r.status == 404) {
                        $("#startfrom").val("Not found!");
                        if (currentpage == 2) {
                            lastpage = currentpage;
                            currentpage = 1;
                            started = 1;
                            displayRandomWord();
                            renderCurrentPage();
                        }

                    } else if (r.status == 401) {
                        alert("Login session expired! Please login again!");
                        localStorage.removeItem("userId");
                        localStorage.removeItem("token");
                        window.location.href = "/user";
                    } else {
                        word = r.status + " " + errorThrown;
                        translation = "Maybe change the settings?\nOr check your connection?";
                        renderWord(1, 1);
                    }
                }
            });
        } else {
            $.ajax({
                url: '/api/getNext',
                method: 'POST',
                async: false,
                dataType: "json",
                data: {
                    status: showStatus,
                    moveType: 0,
                    wordBookId: selectedWordBook,
                    userId: localStorage.getItem("userId"),
                    token: localStorage.getItem("token")
                },
                success: function (r) {
                    lastpage = currentpage;
                    currentpage = 1;
                    wordId = r.wordId;
                    started = 1;
                    btninit();

                    word = r.word;
                    translation = r.translation;
                    wordStatus = r.status;

                    renderCurrentPage();
                    appaused = 0;
                    if (apinterval == -1 && autoPlay != 0) {
                        apinterval = setInterval(autoPlayer, apdelay[autoPlay] * 1000);
                    }
                },
                error: function (r, textStatus, errorThrown) {
                    if (r.status == 401) {
                        alert("Login session expired! Please login again!");
                        localStorage.removeItem("userId");
                        localStorage.removeItem("token");
                        window.location.href = "/user";
                    } else {
                        word = r.status + " " + errorThrown;
                        translation = "Maybe change the settings?\nOr check your connection?";
                        renderWord(1, 1);
                    }
                }
            });
        }
    } else if (displayMode == 1) { // Challenge mode
        started = 1;
        lastpage = currentpage;
        currentpage = 1;
        $.ajax({
            url: '/api/getNextChallenge',
            method: 'POST',
            async: false,
            dataType: "json",
            data: {
                wordBookId: selectedWordBook,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                word = r.word;
                $("#startfrom").val(word);
                translation = r.translation;
                wordStatus = r.status;
                wordId = r.wordId;
                btninit();
                renderCurrentPage();
            },
            error: function (r) {
                if (r.status == 401) {
                    alert("Login session expired! Please login again!");
                    localStorage.removeItem("userId");
                    localStorage.removeItem("token");
                    window.location.href = "/user";
                }
            }
        });
    } else if (displayMode == 2) { // Offline Mode
        if (selectedWordList == []) {
            alert("Unable to start offline mode: No data in word list!");
            return;
        }

        if ($("#startfrom").val() != "") {
            startword = $("#startfrom").val();
            found = false;
            for (var i = 0; i < selectedWordList.length; i++) {
                if (selectedWordList[i].word == startword) {
                    lastpage = currentpage;
                    currentpage = 1;
                    started = 1;

                    wordId = selectedWordList[i].wordId;
                    word = selectedWordList[i].word;
                    translation = selectedWordList[i].translation;
                    wordStatus = selectedWordList[i].status;

                    found = true;
                }
            }
            if (!found) {
                if (currentpage == 0) {
                    $("#startfrom").val("Not found!");
                } else {
                    started = 1;
                    lastpage = currentpage;
                    currentpage = 1;

                    index = parseInt(Math.random() * selectedWordList.length);
                    wordId = selectedWordList[index].wordId;
                    word = selectedWordList[index].word;
                    translation = selectedWordList[index].translation;
                    wordStatus = selectedWordList[index].status;
                }
            }
        } else {
            started = 1;
            lastpage = currentpage;
            currentpage = 1;

            index = parseInt(Math.random() * selectedWordList.length);
            wordId = selectedWordList[index].wordId;
            word = selectedWordList[index].word;
            translation = selectedWordList[index].translation;
            wordStatus = selectedWordList[index].status;
        }

        btninit();

        appaused = 0;
        renderCurrentPage();
        if (apinterval == -1 && autoPlay != 0) {
            apinterval = setInterval(autoPlayer, apdelay[autoPlay] * 1000);
        }
    }
}

function createWordBook() {
    wordBookName = $("#wordBookName").val();

    if (wordBookName == "") {
        alert("Enter a word book name!");
        return;
    }

    $.ajax({
        url: '/api/createWordBook',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            name: wordBookName,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if(r.success == true){
                $("#wordBookName").val("");
                updateWordBookList(false, true);
                renderCurrentPage();
            } else { 
                alert(r.msg);
            }
        },
        error: function (r) {
            if (r.status == 401) {
                alert("Login session expired! Please login again!");
                localStorage.removeItem("userId");
                localStorage.removeItem("token");
                window.location.href = "/user";
            }
        }
    });
}

// Handle user click
var lastpress = Date.now();

function clickHandler(e) {
    if (Date.now() - lastpress < 50) return;
    lastpress = Date.now();
    // Get mouse position
    var absoluteX = e.pageX - canvas.offsetLeft;
    var absoluteY = e.pageY - canvas.offsetTop;
    var btntriggered = 0;
    for (var k = 0; k < btncnt; k++) {
        if (absoluteX >= buttons[k].x && absoluteX <= buttons[k].x + buttons[k].w && absoluteY >= buttons[k].y &&
            absoluteY <= buttons[k].y + buttons[k].h) {
            btntriggered = 1;
            // A button has been triggered
            console.log(buttons[k].name + " button triggered");
            // Start memorizing mode
            if (buttons[k].name == "start") {
                sleep(50).then(() => {
                    startfunc();
                })
            } else if (started && (buttons[k].name == "previous" || buttons[k].name == "next")) {
                if (displayMode == 0) {
                    // Go to previous / next word
                    moveType = 0;
                    if (buttons[k].name == "previous") {
                        moveType = -1;
                    } else if (buttons[k].name == "next") {
                        moveType = 1;
                    }
                    if (random) {
                        moveType = 0;
                    }

                    displayingAnswer = 0;

                    $.ajax({
                        url: '/api/getNext',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            wordId: wordId,
                            status: showStatus,
                            moveType: moveType,
                            wordBookId: selectedWordBook,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            word = r.word;
                            translation = r.translation;
                            wordStatus = r.status;
                            wordId = r.wordId;
                            renderCurrentPage();
                        },
                        error: function (r, textStatus, errorThrown) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            } else {
                                word = r.status + " " + errorThrown;
                                translation = "Maybe change the settings?\nOr check your connection?";
                                renderWord(1, 1);
                            }
                        }
                    });
                } else if (displayMode == 2) {
                    // Get next word from local word list (may not contain real time updates)
                    moveType = 0;
                    if (buttons[k].name == "previous") {
                        moveType = -1;
                    } else if (buttons[k].name == "next") {
                        moveType = 1;
                    }
                    if (random) {
                        moveType = 0;
                    }

                    displayingAnswer = 0;

                    requiredList = [];
                    for (var i = 0; i < selectedWordList.length; i++) {
                        if (showStatus == 1 && (selectedWordList[i].status == 1 || selectedWordList[i].status == 2)) {
                            requiredList.push(selectedWordList[i]);
                        } else if (showStatus == 2 && selectedWordList[i].status == 2) {
                            requiredList.push(selectedWordList[i]);
                        } else if (showStatus == 3 && selectedWordList[i].status == 3) {
                            requiredList.push(selectedWordList[i]);
                        }
                    }

                    if (moveType == 0) {
                        index = parseInt(Math.random() * requiredList.length);
                        wordId = requiredList[index].wordId;
                        word = requiredList[index].word;
                        translation = requiredList[index].translation;
                        wordStatus = requiredList[index].status;
                    } else if (moveType == 1 || moveType == -1) {
                        index = -1;
                        for (var i = 0; i < requiredList.length; i++) {
                            if (requiredList[i].wordId == wordId) {
                                index = i;
                                break;
                            }
                        }
                        if (index == -1) {
                            word = "";
                            translation = "Unknown error";
                            renderWord(1, 1);
                            return;
                        }

                        if (moveType == -1 && index > 0 || moveType == 1 && index < requiredList.length - 1) {
                            index += moveType;
                        } else if (moveType == -1 && index == 0) {
                            index = requiredList.length - 1;
                        } else if (moveType == 1 && index == requiredList.length - 1) {
                            index = 0;
                        }

                        wordId = requiredList[index].wordId;
                        word = requiredList[index].word;
                        translation = requiredList[index].translation;
                        wordStatus = requiredList[index].status;
                    }

                    renderCurrentPage();
                }
            } else if (started && (buttons[k].name == "tag" || buttons[k].name == "remove")) {
                // Update word status
                if (buttons[k].name == "tag") {
                    if (wordStatus == 2) wordStatus = 1;
                    else if (wordStatus == 1 || wordStatus == 3) wordStatus = 2;
                } else if (buttons[k].name == "remove") {
                    if (wordStatus == 3) wordStatus = 1;
                    else if (wordStatus == 1 || wordStatus == 2) wordStatus = 3;
                }
                $.ajax({
                    url: '/api/updateWordStatus',
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        words: JSON.stringify([wordId]),
                        status: wordStatus,
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        ctx.fillStyle = rectcolor;
                        ctx.roundRect(buttons[6].x, buttons[6].y, buttons[6].w, buttons[6].h);
                        ctx.font = fontSize + "px Corbel";
                        ctx.fillStyle = textcolor;
                        if (wordStatus == 2)
                            ctx.fillText("Untag", buttons[6].x + buttons[6].w / 2, buttons[6].y +
                                buttons[6].h / 1.4);
                        else
                            ctx.fillText("Tag", buttons[6].x + buttons[6].w / 2, buttons[6].y + buttons[
                                6].h / 1.4);

                        ctx.fillStyle = rectcolor;
                        ctx.roundRect(buttons[11].x, buttons[11].y, buttons[11].w, buttons[11].h);
                        ctx.font = fontSize + "px Corbel";
                        ctx.fillStyle = textcolor;
                        if (wordStatus == 3) {
                            ctx.font = (fontSize * 0.9) + "px Corbel";
                            ctx.fillText("Undelete", buttons[11].x + buttons[11].w / 2, buttons[11].y +
                                buttons[11].h / 1.4);
                        } else
                            ctx.fillText("Delete", buttons[11].x + buttons[11].w / 2, buttons[11].y +
                                buttons[11].h / 1.4);
                    },
                    error: function (r) {
                        if (r.status == 401) {
                            alert("Login session expired! Please login again!");
                            localStorage.removeItem("userId");
                            localStorage.removeItem("token");
                            window.location.href = "/user";
                        }
                    }
                });
            } else if (started && buttons[k].name == "sound" && !speaker.speaking) {
                msg = new SpeechSynthesisUtterance(word);
                speaker.speak(msg);
            } else if (buttons[k].name == "challengeyes") {
                if (challengeStatus == 0) {
                    challengeStatus = 1;
                    renderCurrentPage();
                } else if (challengeStatus == 1) {
                    $.ajax({
                        url: '/api/updateChallengeRecord',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            wordId: wordId,
                            memorized: 1,
                            getNext: 1,
                            wordBookId: selectedWordBook,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            challengeStatus = 0;
                            word = r.word;
                            translation = r.translation;
                            wordStatus = r.status;
                            wordId = r.wordId;
                            renderCurrentPage();
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            } else if (buttons[k].name == "challengeno") {
                if (challengeStatus == 0 || challengeStatus == 1) {
                    challengeStatus = 3;
                    $.ajax({
                        url: '/api/updateChallengeRecord',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            wordId: wordId,
                            memorized: 0,
                            getNext: 0,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                    });
                    renderCurrentPage();
                } else if (challengeStatus == 3) {
                    $.ajax({
                        url: '/api/getNextChallenge',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            wordBookId: selectedWordBook,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            challengeStatus = 0;
                            word = r.word;
                            translation = r.translation;
                            wordStatus = r.status;
                            wordId = r.wordId;
                            renderCurrentPage();
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            } else if (buttons[k].name == "homepage") {
                if (currentpage == 4) {
                    lastpage = currentpage;
                    currentpage = 5;
                } else if (currentpage == 3) {
                    currentpage = lastpage;
                    lastpage = 2;
                    if(editWord) {
                        currentpage = 1;
                        lastpage = 3;
                        started = 1;
                        renderCurrentPage();
                        appaused = 0;
                        if (apinterval == -1 && autoPlay != 0) {
                            apinterval = setInterval(autoPlayer, apdelay[autoPlay] * 1000);
                        }
                        return;
                    }
                } else if (currentpage == 6) {
                    currentpage = lastpage;
                    lastpage = 6;
                } else {
                    lastpage = currentpage;
                    currentpage = 0;
                }
                started = 0;
                appaused = 0;
                clearInterval(apinterval);
                apinterval = -1;
                speaker.cancel();
                sleep(50).then(() => {
                    renderCurrentPage();
                })
            } else if (buttons[k].name == "settings") {
                lastpage = currentpage;
                currentpage = 2;
                started = 0;
                appaused = 0;
                clearInterval(apinterval);
                apinterval = -1;
                speaker.cancel();
                sleep(50).then(() => {
                    renderCurrentPage();
                })
            } else if (buttons[k].name == "wordbook") {
                lastpage = currentpage;
                currentpage = 5;
                started = 0;
                appaused = 0;
                clearInterval(apinterval);
                apinterval = -1;
                speaker.cancel();
                sleep(50).then(() => {
                    renderCurrentPage();
                })
            } else if (buttons[k].name == "account") {
                window.location.href = "/user";
            } else if (buttons[k].name == "addword") {
                ctx.font = fontSize + "px Corbel";
                ctx.textAlign = "center";

                word = $("#addword_word").val();
                translation = $("#addword_translation").val();
                if (word == "" || translation == "") {
                    ctx.fillStyle = "white";
                    ctx.roundRect(0, buttons[19].y - buttons[19].h * 2.5, canvas.width, buttons[19].h * 1.5 + 5);
                    ctx.fillStyle = "red";
                    ctx.fillText("Both fields must be filled!", canvas.width / 2, buttons[19].y - buttons[19].h * 1.5);
                    return;
                }

                ctx.fillStyle = "white";
                ctx.roundRect(0, buttons[19].y - buttons[19].h * 2.5, canvas.width, buttons[19].h * 1.5 + 5);
                ctx.fillStyle = "blue";
                ctx.fillText("Submitting...", canvas.width / 2, buttons[19].y - buttons[19].h * 1.5);

                if (!editWord) {
                    $.ajax({
                        url: '/api/addWord',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            word: word,
                            translation: translation,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            ctx.fillStyle = "white";
                            ctx.roundRect(0, buttons[19].y - buttons[19].h * 2.5, canvas.width, buttons[19].h * 1.5 + 5);
                            if (r.duplicate == true) {
                                ctx.fillStyle = "red";
                                ctx.fillText("Word duplicated! Add again to ignore.", canvas.width / 2, buttons[19].y - buttons[19].h * 1.5);
                            } else {
                                ctx.fillStyle = "green";
                                ctx.fillText("Word added!", canvas.width / 2, buttons[19].y - buttons[19].h * 1.5);
                                updateWordBookWordList(true);
                            }
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                } else {
                    $.ajax({
                        url: '/api/editWord',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            wordId: editWordId,
                            word: word,
                            translation: translation,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            ctx.fillStyle = "white";
                            ctx.roundRect(0, buttons[19].y - buttons[19].h * 2.5, canvas.width, buttons[19].h * 1.5 + 5);
                            if (r.success != true) {
                                ctx.fillStyle = "red";
                                ctx.fillText(r.msg, canvas.width / 2, buttons[19].y - buttons[19].h * 1.5);
                            } else {
                                ctx.fillStyle = "green";
                                ctx.fillText("Word edited!", canvas.width / 2, buttons[19].y - buttons[19].h * 1.5);
                                updateWordBookWordList(true);
                                currentpage = lastpage;
                                lastpage = 3;
                                if(currentpage == 1){
                                    started = 1;
                                    renderCurrentPage();
                                    appaused = 0;
                                    if (apinterval == -1 && autoPlay != 0) {
                                        apinterval = setInterval(autoPlayer, apdelay[autoPlay] * 1000);
                                    }
                                }
                                renderCurrentPage();
                            }
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            } else if (buttons[k].name == "cleardeleted") {
                if (confirm('Are you sure to delete all the words that are marked as "Deleted" permanently? This operation cannot be undone!')) {
                    $.ajax({
                        url: '/api/clearDeleted',
                        method: 'POST',
                        async: true,
                        dataType: "json",
                        data: {
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            alert("Done");
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            } else if (buttons[k].name == "statistics") {
                statson = 1;
                statistics = "[Failed to fetch statistics]"
                $.ajax({
                    url: '/api/getWordStat',
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        wordId: wordId,
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        statistics = r.msg;
                        ctx.fillStyle = getRndColor(10, 100);
                        ctx.roundRect(buttons[6].x - 5, canvas.height / 2 - 240 - 5, buttons[11].x - buttons[6].x + buttons[11].w + 10, canvas.height - bottomOffset - (canvas.height / 2 - 220) + 50);
                        ctx.fillStyle = getRndColor(160, 250);
                        ctx.roundRect(buttons[6].x, canvas.height / 2 - 240, buttons[11].x - buttons[6].x + buttons[11].w, canvas.height - bottomOffset - (canvas.height / 2 - 220) + 40);
                        ctx.font = smallFontSize + "px Corbel";
                        ctx.fillStyle = getRndColor(10, 100);
                        ctx.textAlign = "center";
                        var lines = statistics.split('\n');
                        $("#hiddenSpan").attr("style", "display:none;font:" + smallFontSize + "px Corbel");
                        $("#hiddenSpan").html("test");
                        lineHeight = $("#hiddenSpan").height() + 5;
                        for (var i = 0; i < lines.length; i++)
                            ctx.fillText(lines[i], canvas.width / 2, canvas.height / 2 - 220 + (i * lineHeight));
                    },
                    error: function (r) {
                        if (r.status == 401) {
                            alert("Login session expired! Please login again!");
                            localStorage.removeItem("userId");
                            localStorage.removeItem("token");
                            window.location.href = "/user";
                        }
                    }
                });
            } else if (buttons[k].name == "mode1") {
                random = 1 - random;
                localStorage.setItem("random", random);
                renderCurrentPage();
            } else if (buttons[k].name == "mode2") {
                swap = 1 - swap;
                localStorage.setItem("swap", swap);
                renderCurrentPage();
            } else if (buttons[k].name == "mode3") {
                showStatus += 1;
                if (showStatus == 4) showStatus = 1;
                localStorage.setItem("showStatus", showStatus);
                renderCurrentPage();
            } else if (buttons[k].name == "mode4") {
                autoPlay += 1;
                if (autoPlay == 4) autoPlay = 0;
                localStorage.setItem("autoPlay", autoPlay);
                renderCurrentPage();
            } else if (buttons[k].name == "mode0") {
                displayMode += 1;
                if (displayMode == 3) {
                    displayMode = 0;
                }
                localStorage.setItem("displayMode", displayMode);
                renderCurrentPage();
            } else if (buttons[k].name == "pauseap") {
                if(autoPlay == 0) return;
                if (appaused && apinterval == -1) apinterval = setInterval(autoPlayer, apdelay[autoPlay] * 1000);
                else {
                    clearInterval(apinterval);
                    apinterval = -1;
                }
                appaused = 1 - appaused;
                renderCurrentPage();
            } else if (buttons[k].name == "import") {
                window.location.href = "/importData";
            } else if (buttons[k].name == "export") {
                window.location.href = "/exportData";
            } else if (buttons[k].name == "createwordbook") {
                createWordBook();
            } else if (buttons[k].name == "wordbookaddword") {
                if (selected.length == 0) {
                    alert("Select at least one word!");
                    return;
                }

                $.ajax({
                    url: '/api/addToWordBook',
                    method: 'POST',
                    async: false,
                    dataType: "json",
                    data: {
                        words: JSON.stringify(selected),
                        wordBookId: wordBookId,
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        currentpage = 4;
                        updateWordBookWordList(true, true);
                        lastpage = 6;
                        renderCurrentPage();
                    },
                    error: function (r) {
                        if (r.status == 401) {
                            alert("Login session expired! Please login again!");
                            localStorage.removeItem("userId");
                            localStorage.removeItem("token");
                            window.location.href = "/user";
                        }
                    }
                });

                selected = [];
            } else if (buttons[k].name == "selectwordbook") {
                if (selectedWordBook != wordBookId) {
                    selectedWordBook = wordBookId;
                    localStorage.setItem("selectedWordBook", selectedWordBook);
                    for (var i = 0; i < wordBookList.length; i++) {
                        if (wordBookList[i].wordBookId == selectedWordBook) {
                            selectedWordBookName = wordBookList[i].name;
                            selectedWordList = [];
                            for (var j = 0; j < wordBookList[i].words.length; j++) {
                                wordId = wordBookList[i].words[j];
                                wordData = wordListMap.get(wordId);
                                selectedWordList.push({
                                    "wordId": wordId,
                                    "word": wordData.word,
                                    "translation": wordData.translation,
                                    "status": wordData.status
                                });
                            }
                        }
                    }
                    renderCurrentPage();
                }
            }
        }
    }

    for (var i = 0; i < wordBookRect.length; i++) {
        if (absoluteX >= wordBookRect[i].x && absoluteX <= wordBookRect[i].x + wordBookW && absoluteY >= wordBookRect[i].y &&
            absoluteY <= wordBookRect[i].y + wordBookH) {
            // A word book has been pressed
            wordBookId = wordBookList[i].wordBookId;
            wordBookName = wordBookList[i].name;
            wordBookShareCode = wordBookList[i].shareCode;
            localStorage.setItem("wordBookId", wordBookId);

            currentpage = 4;
            updateWordBookWordList();
            renderCurrentPage();
        }
    }

    if (!btntriggered && started) {
        if (statson == 0) {
            displayingAnswer = 1 - displayingAnswer;
        } else statson = 0;
        if (displayMode == 0 || displayMode == 2)
            renderWord(displayingAnswer);
    }

    if (currentpage == 4 && loaded) {
        space = getWidth("-----");
        if (absoluteY >= buttons[8].y + buttons[8].h * 2 && absoluteY <= buttons[8].y + buttons[8].h * 2.6) {
            // Word Status Update
            fs = smallFontSize;
            if(isphone) fs *= 0.6;
            w1 = getWidth("Default", fs + "px Corbel") + space;
            w2 = getWidth("Tag", fs + "px Corbel") + space;
            w3 = getWidth("Delete", fs + "px Corbel") + space;

            updateTo = 0;
            if (absoluteX >= buttons[0].w * 0.5 && absoluteX <= buttons[0].w * 0.5 + w1 - space) {
                updateTo = 1;
            } else if (absoluteX >= buttons[0].w * 0.5 + w1 && absoluteX <= buttons[0].w * 0.5 + w1 + w2 - space) {
                updateTo = 2;
            } else if (absoluteX >= buttons[0].w * 0.5 + w1 + w2 && absoluteX <= buttons[0].w * 0.5 + w1 + w2 + w3 - space) {
                updateTo = 3;
            }

            if (selected.length == 0) {
                return;
            }

            table = $("#wordList").DataTable();
            table.clear();
            table.draw();

            $.ajax({
                url: '/api/updateWordStatus',
                method: 'POST',
                async: false,
                dataType: "json",
                data: {
                    words: JSON.stringify(selected),
                    status: updateTo,
                    userId: localStorage.getItem("userId"),
                    token: localStorage.getItem("token")
                },
                success: function (r) {
                    updateWordBookWordList(true);
                    renderCurrentPage();
                },
                error: function (r) {
                    if (r.status == 401) {
                        alert("Login session expired! Please login again!");
                        localStorage.removeItem("userId");
                        localStorage.removeItem("token");
                        window.location.href = "/user";
                    }
                }
            });

            selected = [];
        } else if (absoluteY >= buttons[8].y + buttons[8].h * 3.2 && absoluteY <= buttons[8].y + buttons[8].h * 3.8) {
            // Word book update
            fs = smallFontSize;
            if(isphone) fs *= 0.6;
            w4 = getWidth("Rename", fs + "px Corbel") + space;
            w5 = getWidth("Add", fs + "px Corbel") + space;
            w6 = getWidth("Remove", fs + "px Corbel") + space;
            w7 = getWidth("Delete Word Book", fs + "px Corbel") + space;

            if (absoluteX >= buttons[0].w * 0.5 && absoluteX <= buttons[0].w * 0.5 + w4 - space) {
                newName = prompt("Enter new word book name:", wordBookName);
                if(newName != null) {
                    $.ajax({
                        url: '/api/renameWordBook',
                        method: 'POST',
                        async: false,
                        dataType: "json",
                        data: {
                            wordBookId: wordBookId,
                            name: newName,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            updateWordBookWordList(true);
                            renderCurrentPage();
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            } else if (absoluteX >= buttons[0].w * 0.5 + w4 && absoluteX <= buttons[0].w * 0.5 + w4 + w5 - space) {
                if (wordBookId == 0) {
                    lastpage = currentpage;
                    currentpage = 3;
                    renderCurrentPage();
                } else {
                    lastpage = currentpage;
                    currentpage = 6;
                    renderCurrentPage();
                }
            } else if (absoluteX >= buttons[0].w * 0.5 + w4 + w5 && absoluteX <= buttons[0].w * 0.5 + w4 + w5 + w6 - space) {
                if (wordBookId == 0) {
                    if (confirm('Are you sure to delete selected words from your word database? This will remove them from all word books no matter its status is default, tagged or deleted. This operation cannot be undone!')) {
                        table = $("#wordList").DataTable();
                        table.clear();
                        table.draw();
                        $.ajax({
                            url: '/api/deleteWord',
                            method: 'POST',
                            async: false,
                            dataType: "json",
                            data: {
                                words: JSON.stringify(selected),
                                userId: localStorage.getItem("userId"),
                                token: localStorage.getItem("token")
                            },
                            success: function (r) {
                                updateWordBookWordList(true);
                                renderCurrentPage();
                            },
                            error: function (r) {
                                if (r.status == 401) {
                                    alert("Login session expired! Please login again!");
                                    localStorage.removeItem("userId");
                                    localStorage.removeItem("token");
                                    window.location.href = "/user";
                                }
                            }
                        });
                    }
                } else {
                    $.ajax({
                        url: '/api/deleteFromWordBook',
                        method: 'POST',
                        async: false,
                        dataType: "json",
                        data: {
                            words: JSON.stringify(selected),
                            wordBookId: wordBookId,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            updateWordBookWordList(true);
                            renderCurrentPage();
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            } else if (wordBookId != 0 && absoluteX >= buttons[0].w * 0.5 + w4 + w5 + w6 && absoluteX <= buttons[0].w * 0.5 + w4 + w5 + w6 + w7 - space) {
                if (confirm("Are you sure to delete this word book? The words will not be deleted but they will no longer belong to this word book. This operation cannot be undone!")) {
                    $.ajax({
                        url: '/api/deleteWordBook',
                        method: 'POST',
                        async: false,
                        dataType: "json",
                        data: {
                            wordBookId: wordBookId,
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            updateWordBookList(true, true);
                            currentpage = 5;
                            lastpage = 4;
                            renderCurrentPage();
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            }
        } else if (absoluteY >= buttons[8].y + buttons[8].h * 3.8 && absoluteY <= buttons[8].y + buttons[8].h * 4.4) {
            // Word book update
            fs = smallFontSize;
            if(isphone) fs *= 0.6;
            w8 = getWidth("Share:", fs + "px Corbel") + space;
            w9 = getWidth(wordBookShareCode, fs + "px Corbel") + space;
            if(wordBookShareCode == ""){
                w9 = getWidth("Private", fs + "px Corbel") + space;
            }
            if (absoluteX >= buttons[0].w * 0.5 + w8 && absoluteX <= buttons[0].w * 0.5 + w8 + w9 - space) {
                if(wordBookShareCode == ""){
                    $.ajax({
                        url: '/api/shareWordBook',
                        method: 'POST',
                        async: false,
                        dataType: "json",
                        data: {
                            wordBookId: wordBookId,
                            operation: "share",
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            if(r.success == true){
                                updateWordBookList(true, true);
                            }
                            alert(r.msg);
                            if(r.success == true){
                                renderCurrentPage();
                            }
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                } else {
                    $.ajax({
                        url: '/api/shareWordBook',
                        method: 'POST',
                        async: false,
                        dataType: "json",
                        data: {
                            wordBookId: wordBookId,
                            operation: "unshare",
                            userId: localStorage.getItem("userId"),
                            token: localStorage.getItem("token")
                        },
                        success: function (r) {
                            if(r.success == true){
                                updateWordBookList(true, true);
                            }
                            alert(r.msg);
                            if(r.success == true){
                                renderCurrentPage();
                            }
                        },
                        error: function (r) {
                            if (r.status == 401) {
                                alert("Login session expired! Please login again!");
                                localStorage.removeItem("userId");
                                localStorage.removeItem("token");
                                window.location.href = "/user";
                            }
                        }
                    });
                }
            }
        }
    }
}

$("#startfrom").on('keypress', function (e) {
    if (e.which == 13) {
        startfunc();
    }
});

$("#wordBookName").on('keypress', function (e) {
    if (e.which == 13) {
        createWordBook();
    }
});

$(document).on('keydown', function (e) {
    if(currentpage == 1) {
        btnid = -1;
        if(e.which == 32 || e.which == 13) {
            clickHandler({pageX: -1, pageY: -1});
            return;
        } else if(e.which == 37) {
            btnid = 1;
        } else if(e.which == 39) {
            btnid = 2;
        } else if(e.which == 46 || e.which == 68) {
            btnid = 11;
        } else if(e.which == 84) {
            btnid = 6;
        } else if(e.which == 83) {
            btnid = 3;
        } else if(e.which == 80) {
            btnid = 13;
        }
        if(btnid != -1)
            clickHandler({pageX: buttons[btnid].x + canvas.offsetLeft, pageY: buttons[btnid].y + canvas.offsetTop});
    }
});

$('#wordList tbody').on('click', 'tr', function () {
    wid = parseInt($(this).attr("id"));
    if ($(this).hasClass("selected")) {
        idx = selected.indexOf(wid);
        if (idx > -1) {
            selected.splice(idx, 1);
        }
    } else {
        selected.push(wid);
    }
    $(this).toggleClass('selected');
});

$('#wordList tbody').on('dblclick', 'tr', function () {
    wid = parseInt($(this).attr("id"));
    console.log(wid);
    editWordId = wid;
    editWord = true;

    lastpage = currentpage;
    currentpage = 3;
    renderCurrentPage();
});

$("#canvas").dblclick(function () {
    if(currentpage == 1 && displayMode != 2){
        editWordId = wordId;
        editWord = true;

        lastpage = currentpage;
        currentpage = 3;
        started = 0;
        appaused = 0;
        clearInterval(apinterval);
        apinterval = -1;
        speaker.cancel();
        sleep(50).then(() => {
            renderCurrentPage();
        })
    }
});

document.addEventListener("click", clickHandler, false);

if (currentpage == 1) {
    startfunc();
} else {
    if (currentpage == 4) {
        updateWordBookWordList(true);
    }
    renderCurrentPage();
}