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
var btncnt = 9;

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
buttons[0]={name:"submit",x:0,y:0,w:300,h:50,orgw:300,orgh:50},
buttons[1]={name:"home",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[2]={name:"logout",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[3]={name:"switchToRegister",x:0,y:0,w:100,h:25,orgw:100,orgh:25},
buttons[4]={name:"switchToLogin",x:0,y:0,w:100,h:25,orgw:100,orgh:25},
buttons[5]={name:"deleteacc",x:0,y:0,w:400,h:50,orgw:400,orgh:50},
buttons[6]={name:"settings",x:0,y:0,w:200,h:50,orgw:200,orgh:50},
buttons[7]={name:"changepwd",x:0,y:0,w:400,h:50,orgw:400,orgh:50},
buttons[8]={name:"restart",x:0,y:0,w:400,h:50,orgw:400,orgh:50};

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
}

function fontresize() {
    fontSize = Math.min(orgFontSize, parseInt(orgFontSize * window.innerWidth / windowOrgW));
    largeFontSize = Math.min(orglargeFontSize, parseInt(orglargeFontSize * window.innerWidth / windowOrgW));
    smallFontSize = Math.min(orgsmallFontSize, parseInt(orgsmallFontSize * window.innerWidth / windowOrgW));
}
btninit();
btnresize();
fontresize();





// Fetch user info

var currentpage = 0;
var username = "";
var email = "";
var invitationCode = "";
var inviter = "";
var cnt = 0;
var tagcnt = 0;
var delcnt = 0;
var chcnt = 0;
var age = 0;

if(localStorage.getItem("userId") == null || localStorage.getItem("userId") == 0)
    localStorage.removeItem("admin");

$.ajax({
    url: "/api/getUserInfo",
    method: 'POST',
    async: true,
    dataType: "json",
    data: {
        userId: localStorage.getItem("userId"),
        token: localStorage.getItem("token")
    },
    success: function (r) {
        username = r.username;
        email = r.email;
        invitationCode = r.invitationCode;
        cnt = r.cnt;
        tagcnt = r.tagcnt;
        delcnt = r.delcnt;
        chcnt = r.chcnt;
        inviter = r.inviter;
        age = r.age;
    }
});

function renderHomePage() {
    btninit();
    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Render title & subtitle
    ctx.textAlign = "center";

    ctx.font = largeFontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Word Memo", canvas.width / 2, canvas.height / 2 - 6.25 * fontSize);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText("User Information", canvas.width / 2, canvas.height / 2 - 4.5 * fontSize);

    // Render buttons
    buttons[1].x = buttons[1].w * 0.2;
    buttons[1].y = buttons[1].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Home", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
    ////
    buttons[2].x = canvas.width - buttons[2].w * 1.2;
    buttons[2].y = buttons[2].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[2].x, buttons[2].y, buttons[2].w, buttons[2].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Logout", buttons[2].x + buttons[2].w / 2, buttons[2].y + buttons[2].h / 1.4);
    ////
    buttons[6].x = canvas.width - buttons[6].w * 1.2;
    buttons[6].y = buttons[6].h * 1.5;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[6].x, buttons[6].y, buttons[6].w, buttons[6].h);

    ctx.font = fontSize * 0.9 + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Settings", buttons[6].x + buttons[6].w / 2, buttons[6].y + buttons[6].h / 1.4);

    // Render user information
    if (username == "") {
        $.ajax({
            url: "/api/getUserInfo",
            method: 'POST',
            async: false,
            dataType: "json",
            data: {
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                username = r.username;
                email = r.email;
                invitationCode = r.invitationCode;
                cnt = r.cnt;
                tagcnt = r.tagcnt;
                delcnt = r.delcnt;
                chcnt = r.chcnt;
                inviter = r.inviter;
                age = r.age;
            }
        });
    }

    ctx.font = fontSize + "px Corbel";
    ctx.fillText(username + "  [UID: " + userId +"]", canvas.width / 2, canvas.height / 2 - 2.5 * fontSize);

    ctx.font = fontSize * 0.7 + "px Corbel";
    ctx.fillText("You have already been here for " + age + " days!", canvas.width / 2, canvas.height / 2 - 1.75 * fontSize);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText("Email: " + email, canvas.width / 2, canvas.height / 2 - 0.5 * fontSize);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText("Invitation Code: " + invitationCode, canvas.width / 2, canvas.height / 2 + 0.75 * fontSize);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText("Invited By: " + inviter, canvas.width / 2, canvas.height / 2 + 2 * fontSize);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText(cnt + " words in list", canvas.width / 2, canvas.height / 2 + 3.75 * fontSize);
    ctx.font = fontSize + "px Corbel";
    ctx.fillText(tagcnt + " tagged and " + delcnt + " deleted", canvas.width / 2, canvas.height / 2 + 5 * fontSize);
    ctx.font = fontSize + "px Corbel";
    ctx.fillText(chcnt + " challenges done so far", canvas.width / 2, canvas.height / 2 + 6.25 * fontSize);
}

function renderLoginPage() {
    btninit();
    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Render title & subtitle
    ctx.textAlign = "center";

    ctx.font = largeFontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Word Memo", canvas.width / 2, canvas.height / 2 - 200);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText("Login", canvas.width / 2, canvas.height / 2 - 130);

    // Show input box
    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Username: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 - 30);
    $("#username").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 - 48) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("Password: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 + 20);
    $("#password").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 + 2) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    $("#email").hide();
    $("#invitationCode").hide();

    // Render buttons
    buttons[1].x = buttons[1].w * 0.2;
    buttons[1].y = buttons[1].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Home", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
    ////
    buttons[0].x = canvas.width / 2 - buttons[0].w / 2;
    buttons[0].y = canvas.height / 2 + buttons[0].h * 2;
    ctx.fillStyle = getRndColor(160, 250);

    ctx.roundRect(buttons[0].x, buttons[0].y, buttons[0].w, buttons[0].h);
    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Login", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h / 1.4);
    ////
    buttons[3].x = canvas.width / 2 + buttons[3].w / 2;
    buttons[3].y = canvas.height / 2 - 120;
    ctx.font = smallFontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.textAlign = "left";
    ctx.fillText("Register", buttons[3].x + buttons[3].w / 2, buttons[3].y + buttons[3].h / 1.4);
    ////
    ctx.font = fontSize + "px Corbel";
    ctx.textAlign = "center";
}

function renderRegisterPage() {
    btninit();
    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Render title & subtitle
    ctx.textAlign = "center";

    ctx.font = largeFontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Word Memo", canvas.width / 2, canvas.height / 2 - 200);

    ctx.font = fontSize + "px Corbel";
    ctx.fillText("Register", canvas.width / 2, canvas.height / 2 - 130);

    // Show input box
    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Username: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 - 30);
    $("#username").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 - 48) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("Email: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 + 20);
    $("#email").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 + 2) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("Password: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 + 70);
    $("#password").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 + 52) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("Invitation code: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 + 120);
    $("#invitationCode").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 + 102) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    // Render buttons
    buttons[1].x = buttons[1].w * 0.2;
    buttons[1].y = buttons[1].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Home", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
    ////
    buttons[0].x = canvas.width / 2 - buttons[0].w / 2;
    buttons[0].y = canvas.height / 2 + buttons[0].h * 4;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[0].x, buttons[0].y, buttons[0].w, buttons[0].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Register", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h / 1.4);
    ////
    buttons[4].x = canvas.width / 2 + buttons[4].w / 2;
    buttons[4].y = canvas.height / 2 - 120;
    ctx.font = smallFontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.textAlign = "left";
    ctx.fillText("Login", buttons[4].x + buttons[4].w / 2, buttons[4].y + buttons[4].h / 1.4);
    ////
    ctx.font = fontSize + "px Corbel";
    ctx.textAlign = "center";
}

function renderSettings() {
    $("#oldpwd").hide();
    $("#newpwd").hide();
    $("#cfmpwd").hide();

    btninit();
    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    isAdmin = (localStorage.getItem("admin") == "true");

    // Render title
    ctx.font = fontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.textAlign = "center";
    if (isAdmin) {
        ctx.fillText("Admin settings", canvas.width / 2, buttons[1].h * 0.2 + buttons[1].h / 1.4);
    } else {
        ctx.fillText("Account settings", canvas.width / 2, buttons[1].h * 0.2 + buttons[1].h / 1.4);
    }

    // Render buttons
    buttons[1].x = buttons[1].w * 0.2;
    buttons[1].y = buttons[1].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Back", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
    ////
    buttons[7].x = canvas.width / 2 - buttons[7].w / 2;
    buttons[7].y = canvas.height / 2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[7].x, buttons[7].y, buttons[7].w, buttons[7].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Change Password", buttons[7].x + buttons[7].w / 2, buttons[7].y + buttons[7].h / 1.4);
    ////
    if (!isAdmin) {
        buttons[5].x = canvas.width / 2 - buttons[5].w / 2;
        buttons[5].y = canvas.height * 3 / 4;
        ctx.fillStyle = "red";
        ctx.roundRect(buttons[5].x, buttons[5].y, buttons[5].w, buttons[5].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = "black"
        ctx.fillText("Delete Account", buttons[5].x + buttons[5].w / 2, buttons[5].y + buttons[5].h / 1.4);
    } else {
        buttons[8].x = canvas.width / 2 - buttons[8].w / 2;
        buttons[8].y = canvas.height * 3 / 4;
        ctx.fillStyle = getRndColor(160, 250);
        ctx.roundRect(buttons[8].x, buttons[8].y, buttons[8].w, buttons[8].h);

        ctx.font = fontSize + "px Corbel";
        ctx.fillStyle = getRndColor(10, 100);
        ctx.fillText("Restart Server", buttons[8].x + buttons[8].w / 2, buttons[8].y + buttons[8].h / 1.4);
        // This will only restart the Word Memo backend program
    }
}

function renderChangepwd() {
    btninit();
    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Render title
    ctx.textAlign = "center";

    ctx.font = fontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Change Password", canvas.width / 2, buttons[1].h * 0.2 + buttons[1].h / 1.4);

    // Render buttons
    buttons[1].x = buttons[1].w * 0.2;
    buttons[1].y = buttons[1].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Back", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
    ////
    buttons[0].x = canvas.width / 2 - buttons[0].w / 2;
    buttons[0].y = canvas.height / 2 + buttons[0].h * 4;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[0].x, buttons[0].y, buttons[0].w, buttons[0].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Change", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h / 1.4);

    // Show input box
    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Old password: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 - 30);
    $("#oldpwd").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 - 48) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("New password: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 + 20);
    $("#newpwd").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 + 2) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    ctx.fillText("Confirm password: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 + 70);
    $("#cfmpwd").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 + 52) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");
}

function renderDeleteacc() {
    btninit();
    // Get page width & height
    canvas.width = window.innerWidth - 25;
    canvas.height = window.innerHeight - 25;

    // Clear existing canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Render title
    ctx.textAlign = "center";

    ctx.font = fontSize + "px Impact";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Delete Account", canvas.width / 2, buttons[1].h * 0.2 + buttons[1].h / 1.4);

    // Render buttons
    buttons[1].x = buttons[1].w * 0.2;
    buttons[1].y = buttons[1].h * 0.2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[1].x, buttons[1].y, buttons[1].w, buttons[1].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Back", buttons[1].x + buttons[1].w / 2, buttons[1].y + buttons[1].h / 1.4);
    ////
    buttons[0].x = canvas.width / 2 - buttons[0].w / 2;
    buttons[0].y = canvas.height / 2 + buttons[0].h * 2;
    ctx.fillStyle = getRndColor(160, 250);
    ctx.roundRect(buttons[0].x, buttons[0].y, buttons[0].w, buttons[0].h);

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.fillText("Delete", buttons[0].x + buttons[0].w / 2, buttons[0].y + buttons[0].h / 1.4);

    // Show input box
    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = getRndColor(10, 100);
    ctx.textAlign = "center";
    ctx.fillText("Password: ", canvas.width / 2 - buttons[0].w / 2, canvas.height / 2 - 30);
    $("#password").attr("style", "position:absolute;left:" + (canvas.width / 2 + buttons[0].w / 4) + ";top:" + (canvas.height / 2 - 48) + ";font-size:" + fontSize * 0.4 + ";font-family:Corbel");

    // Hints
    ctx.font = smallFontSize + "px Corbel";
    ctx.fillText("* Your account will be deleted after 14 days.", canvas.width / 2, buttons[0].y + buttons[0].h * 1.75);
    ctx.fillText("You can recover it by logging in during that period.", canvas.width / 2, buttons[0].y + buttons[0].h * 2.25);
    ctx.fillText("After 14 days it will be deleted permanently and cannot be recovered.", canvas.width / 2, buttons[0].y + buttons[0].h * 2.75);
}

userId = localStorage.getItem("userId");
token = localStorage.getItem("token");

// Validate login
var validation = false;
$.ajax({
    url: "/api/validateToken",
    method: 'POST',
    async: false,
    dataType: "json",
    data: {
        userId: localStorage.getItem("userId"),
        token: localStorage.getItem("token")
    },
    success: function (r) {
        validation = r.validation;
    }
});

if (validation == false) {
    renderLoginPage();
    currentpage = 1;
} else {
    renderHomePage();
    currentpage = 0;
}

function renderCurrentPage() {
    btnresize();
    fontresize();
    sleep(50).then(() => {
        $("#username").hide();
        $("#password").hide();
        if (currentpage == 0) {
            renderHomePage();
        } else if (currentpage == 1) {
            renderLoginPage();
        } else if (currentpage == 2) {
            renderRegisterPage();
        } else if (currentpage == 3) {
            renderSettings();
        } else if (currentpage == 4) {
            renderChangepwd();
        } else if (currentpage == 5) {
            renderDeleteacc();
        }
    });
}
if (!isphone) {
    window.onresize = renderCurrentPage;
}

function loginfunc() {
    username = $("#username").val();
    password = $("#password").val();

    ctx.fillStyle = "white";
    ctx.roundRect(0, buttons[0].y - buttons[0].h * 1.5 - 5, canvas.width, buttons[0].h + 20);

    if (username == "" || password == "") {
        ctx.fillStyle = "red";
        ctx.fillText("Both fields must be filled!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
        return;
    }

    $.ajax({
        url: "/api/login",
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            username: username,
            password: password
        },
        success: function (r) {
            if (r.success == true) {
                localStorage.setItem("userId", r.userId);
                localStorage.setItem("token", r.token);
                userId = r.userId;
                ctx.fillStyle = "green";
                ctx.fillText("Logged in successfully!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
                $.ajax({
                    url: "/api/getUserInfo",
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        username = r.username;
                        email = r.email;
                        invitationCode = r.invitationCode;
                        cnt = r.cnt;
                        tagcnt = r.tagcnt;
                        delcnt = r.delcnt;
                        chcnt = r.chcnt;
                        inviter = r.inviter;
                        age = r.age;
                        if (r.isAdmin) {
                            localStorage.setItem("admin", "true");
                        } else {
                            localStorage.removeItem("admin");
                        }
                    }
                });
                sleep(2000).then(() => {
                    $("#username").hide();
                    $("#password").hide();
                    $("#username").val("");
                    $("#password").val("");
                    currentpage = 0;
                    renderCurrentPage();
                })
            } else {
                ctx.fillStyle = "red";
                ctx.fillText(r.msg, canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
            }
        }
    });
}

function registerfunc() {
    username = $("#username").val();
    password = $("#password").val();
    email = $("#email").val();
    invitationCode = $("#invitationCode").val();

    ctx.fillStyle = "white";
    ctx.roundRect(0, buttons[0].y - buttons[0].h * 1.5 - 5, canvas.width, buttons[0].h + 20);

    if (username == "" || password == "" || email == "" || invitationCode == "") {
        ctx.fillStyle = "red";
        ctx.fillText("All fields must be filled!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
        return;
    }

    $.ajax({
        url: "/api/register",
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            username: username,
            password: password,
            email: email,
            invitationCode: invitationCode
        },
        success: function (r) {
            if (r.success == true) {
                ctx.fillStyle = "green";
                ctx.fillText("Registered successfully!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
                sleep(2000).then(() => {
                    $("#email").hide();
                    $("#invitationCode").hide();
                    $("#email").val("");
                    $("#invitationCode").val("");
                    currentpage = 1;
                    renderCurrentPage();
                })
            } else {
                ctx.fillStyle = "red";
                ctx.fillText(r.msg, canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
            }
        }
    });
}

function changepwdfunc() {
    oldpwd = $("#oldpwd").val();
    newpwd = $("#newpwd").val();
    cfmpwd = $("#cfmpwd").val();

    ctx.fillStyle = "white";
    ctx.roundRect(0, buttons[0].y - buttons[0].h * 1.5 - 5, canvas.width, buttons[0].h + 20);

    if (oldpwd == "" || newpwd == "" || cfmpwd == "") {
        ctx.fillStyle = "red";
        ctx.fillText("All fields must be filled!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
        return;
    }

    $.ajax({
        url: "/api/changePassword",
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            oldpwd: oldpwd,
            newpwd: newpwd,
            cfmpwd: cfmpwd,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                $("#oldpwd").hide();
                $("#newpwd").hide();
                $("#cfmpwd").hide();
                $("#oldpwd").val("");
                $("#newpwd").val("");
                $("#cfmpwd").val("");
                ctx.fillStyle = "green";
                localStorage.removeItem("userid");
                localStorage.removeItem("token");
                currentpage = 1;
                renderCurrentPage();
                sleep(100).then(() => {
                    ctx.fillStyle = "green";
                    ctx.fillText("Password changed successfully!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
                });
            } else {
                ctx.fillStyle = "red";
                ctx.fillText(r.msg, canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
            }
        }
    });
}

function deleteaccfunc() {
    password = $("#password").val();

    ctx.font = fontSize + "px Corbel";
    ctx.fillStyle = "white";
    ctx.roundRect(0, buttons[0].y - buttons[0].h * 1.5 - 5, canvas.width, buttons[0].h + 20);

    if (password == "") {
        ctx.fillStyle = "red";
        ctx.fillText("You must enter your password!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
        return;
    }

    $.ajax({
        url: "/api/deleteAccount",
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            password: password,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                $("#password").hide();
                $("#password").val("");
                ctx.fillStyle = "green";
                localStorage.removeItem("userid");
                localStorage.removeItem("token");
                currentpage = 1;
                renderCurrentPage();
                sleep(100).then(() => {
                    ctx.fillStyle = "green";
                    ctx.fillText("Accounted marked for deletion!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
                });
            } else {
                ctx.fillStyle = "red";
                ctx.fillText(r.msg, canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
            }
        }
    });
}

// Handle user click
function clickHandler(e) {
    // Get mouse position
    var relativeX = e.clientX - canvas.offsetLeft;
    var relativeY = e.clientY - canvas.offsetTop;
    var btntriggered = 0;
    for (var i = 0; i < btncnt; i++) {
        if (relativeX >= buttons[i].x && relativeX <= buttons[i].x + buttons[i].w && relativeY >= buttons[i].y &&
            relativeY <= buttons[i].y + buttons[i].h) {
            btntriggered = 1;
            // A button has been triggered
            console.log(buttons[i].name + " button triggered");
            if (buttons[i].name == "submit") {
                if (currentpage == 1) {
                    loginfunc();
                } else if (currentpage == 2) {
                    registerfunc();
                } else if (currentpage == 4) {
                    changepwdfunc();
                } else if (currentpage == 5) {
                    deleteaccfunc();
                }
            } else if (buttons[i].name == "home") {
                if (currentpage < 3) {
                    window.location.href = "/";
                } else if (currentpage == 3) {
                    currentpage = 0;
                    renderCurrentPage();
                } else if (currentpage == 4 || currentpage == 5) {
                    currentpage = 3;
                    renderCurrentPage();
                }
            } else if (buttons[i].name == "switchToRegister") {
                currentpage = 2;
                renderCurrentPage();
            } else if (buttons[i].name == "switchToLogin") {
                currentpage = 1;
                renderCurrentPage();
            } else if (buttons[i].name == "settings") {
                currentpage = 3;
                renderCurrentPage();
            } else if (buttons[i].name == "changepwd") {
                currentpage = 4;
                renderCurrentPage();
            } else if (buttons[i].name == "deleteacc") {
                currentpage = 5;
                renderCurrentPage();
            } else if (buttons[i].name == "logout") {
                $.ajax({
                    url: "/api/logout",
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    }
                });
                localStorage.removeItem("userid");
                localStorage.removeItem("token");
                currentpage = 1;
                renderCurrentPage();
                sleep(100).then(() => {
                    ctx.fillStyle = "green";
                    ctx.fillText("Loggod out successfully!", canvas.width / 2, buttons[0].y - buttons[0].h * 0.5);
                });
            } else if (buttons[i].name == "restart") {
                $.ajax({
                    url: "/api/admin/restart",
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        if (r.success == false) {
                            alert(r.msg);
                        }
                    }
                });
            }
        }
    }
}

$("#password").on('keypress', function (e) {
    if (e.which == 13) {
        if (currentpage == 1) {
            loginfunc();
        } else if (currentpage == 2) {
            registerfunc();
        } else if (currentpage == 5) {
            deleteaccfunc();
        }
    }
});

$("#cfmpwd").on('keypress', function (e) {
    changepwdfunc();
})

document.addEventListener("click", clickHandler, false);