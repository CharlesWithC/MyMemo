// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var isphone = false;
if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
    isphone = true;
}

function NotyNotification(text, type = 'success', timeout = 3000, layout = 'topRight') {
    new Noty({
        theme: 'mint',
        text: text,
        type: type,
        layout: layout,
        timeout: timeout
    }).show();
}

function AjaxErrorHandler(r, textStatus, errorThrown) {
    if (r.status == 401) {
        $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        SessionExpired();
    } else if (r.status == 503) {
        NotyNotification("503 Service Unavailable. Try refreshing your page and pass the CloudFlare's JS Challenge. Otherwise server is down.", type = 'error', timeout = 5000);
    } else {
        NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
    }
}

function GenRandomString(length) {
    var result = '';
    var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    var charactersLength = characters.length;
    for (var i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}

function CopyToClipboard(text) {
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val(text).select();
    document.execCommand("copy");
    $temp.remove();
    NotyNotification("Copied!");
}

function GenCPBtn(text){
    if(text == "@pvtgroup") return "";
    return '<button type="button" class="btn btn-primary btn-sm" onclick="CopyToClipboard(\'' + text + '\')"><i class="fa fa-copy"></i></button>';
}

function TimestampToLocale(text) {
    tempid = "temp-" + GenRandomString();
    $("body").append("<div id='" + tempid + "'>" + text + "</div>")
    $("#" + tempid + " time").each(function () {
        t = parseInt($(this).text());
        if (t != NaN) {
            dt = new Date(t * 1000).toLocaleString();
            $(this).text(dt);
        }
    });
    ret = $("#" + tempid).html();
    $("#" + tempid).remove();
    return ret;
}

function BeautifyMarkdownEditor() {
    $(".cursor").remove();
}

function BeautifyC3Chart() {
    $(".c3 text").css("font-family", "Comic Sans MS");
    if (localStorage.getItem("settings-theme") == "dark") {
        setInterval(function () {
            $(".c3 text").css("fill", "#ffffff");
            $(".c3-tooltip tr").css("color", "black")
        }, 50);
    }
}

var modalz = 1000;

function GenModal(title, content, control, onhide = function () {}, addClass = "") {
    modalId = "modal-" + GenRandomString(8);
    modalz += 2;
    if (control == undefined) control = "";
    $(".footer").before(`<div class="modal fade ` + addClass + `" id="` + modalId + `" tabindex="-1" role="dialog"
        aria-labelledby="` + modalId + `-label" aria-hidden="true" style="z-index:` + modalz + `">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="` + modalId + `-label">` + title + `</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="` + modalId + `" aria-label="Close"
                        onclick="$('#` + modalId + `').modal('hide')">
                        <span aria-hidden="true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">` + content + `</div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="` + modalId + `" onclick="$('#` + modalId + `').modal('hide')">Close</button>
                ` + control + `</div>
            </div>
        </div>
    </div>`);
    $("#" + modalId).modal("show");
    $.each($(".modal-backdrop"), function () {
        if ($(this).attr("id") == undefined) {
            $(this).attr("id", modalId + "-backdrop");
            $(this).css("z-index", modalz - 1);
        }
    });
    $('.modal').on('hidden.bs.modal', function () {
        tmodalId = $(this).attr("id");
        $("#" + tmodalId).remove();
        $("#" + tmodalId + "-backdrop").remove();
        if (tmodalId == modalId) onhide();
    });

    return modalId;
}

function OnSubmit(element, func, needctrl = false) {
    $(element).off("keypress");
    $(element).unbind("keypress");
    $(element).keypress(function (e) {
        if (e.which == 13 && !needctrl || e.which == 13 && e.ctrlKey) {
            func();
        }
    });
}

function BackToHome() {
    window.location.href = '/';
}

function ClearUserData() {
    theme = localStorage.getItem("settings-theme");
    localStorage.clear();
    localStorage.setItem("first-use", "0");
    localStorage.setItem("sign-out", "1");
    localStorage.setItem("settings-theme", theme);
}

function SignOut() {
    $.ajax({
        url: "/api/user/logout",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        }
    });
    ClearUserData();
    $("#navusername").html("<a href='/user/login'>Sign in</a>&nbsp;&nbsp;  ");

    NotyNotification('You are now signed out!');

    setTimeout(function () {
        window.location.href = "/user/login";
    }, 1000);
}

function SessionExpired(noredirect = false) {
    if (!noredirect) NotyNotification('Login to proceed!', type = 'error');
    else {
        if (localStorage.getItem("token") != null)
            NotyNotification('Login session expired!', type = 'error');
    }
    ClearUserData();
    $("#navusername").html("<a href='/user/login'>Sign in</a>&nbsp;&nbsp;  ");
    if (!noredirect) {
        setTimeout(function () {
            window.location.href = "/user/login"
        }, 3000);
    }
}

function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return typeof sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
    return -1;
}

function lsGetItem(lsItemName, defaultValue = 0) {
    if (localStorage.getItem(lsItemName) == null || localStorage.getItem(lsItemName) == "undefined") {
        localStorage.setItem(lsItemName, defaultValue);
        return defaultValue;
    } else {
        return localStorage.getItem(lsItemName);
    }
}

bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));

function UpdateBookDisplay() {
    $(".book").remove();
    for (var i = 0; i < bookList.length; i++) {
        book = bookList[i];
        wcnt = "";
        if (book.bookId == 0) {
            wcnt = book.total + ' questions';
        } else {
            wcnt = book.progress + ' memorized / ' + book.total + ' questions';
        }
        btn = "";
        if (book.bookId != localStorage.getItem("memo-book-id")) {
            btn = '<button type="button" class="btn btn-primary " onclick="SelectBook(' + book.bookId + ')">Select</button>';
        } else {
            btn = '<button type="button" class="btn btn-secondary">Selected</button>'
        }
        bname = book.name;
        if (book.groupId != -1) {
            bname = "[Group] " + bname;
        }

        $("#book-list").append('<div class="book">\
        <p>' + bname + '</p>\
        <p>' + wcnt + '</p>\
        <button type="button" class="btn btn-primary " onclick="OpenBook(' + book.bookId + ')">Open</button>\
        ' + btn + '\
        <hr>\
        </div>');
    }
}

function UpdateBookList(async = true) {
    $.ajax({
        url: "/api/book",
        method: 'POST',
        async: async,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            bookList = r;
            try {
                localStorage.setItem("book-list", JSON.stringify(bookList));
            } catch {
                console.warning("Cannot store book list in local storage, gave up!");
            }
            UpdateBookDisplay();
        }
    });
}

if (new Date().getTime() - lsGetItem("last-book-update", 0) > 600000) {
    UpdateBookList();
    localStorage.setItem("last-book-update", new Date().getTime());
}
setInterval(function () {
    UpdateBookList();
}, 300000);

function OpenBook(bookId) {
    window.location.href = '/book?bookId=' + bookId;
}

function ShowBook() {
    $("#book-div").fadeIn();
    UpdateBookDisplay();
}

function SelectBook(bookId) {
    localStorage.setItem("memo-book-id", bookId);
    UpdateBookDisplay();
}

function RefreshBookList() {
    $("#book-list-refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');
    $.ajax({
        url: "/api/book",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            bookList = r;
            try {
                localStorage.setItem("book-list", JSON.stringify(bookList));
            } catch {
                console.warning("Cannot store book list in local storage, gave up!");
            }
            UpdateBookDisplay();
            $("#book-list-refresh-btn").html('<i class="fa fa-sync"></i>');
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function CreateBook(element) {
    bookName = $(element).val();

    if (bookName == "") {
        NotyNotification('Please enter the book name!', type = 'warning');
        return;
    }

    $.ajax({
        url: '/api/book/create',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            name: bookName,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                UpdateBookList();
                NotyNotification('Book created!');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function LoadShow() {
    $(".footer").before("<div id='general-loader' class='loader' style='display:none;padding-left:0.5em;padding-top:0.2em'><i class='fa fa-spinner fa-spin'></i></div>");
    $("#general-loader").fadeIn();
}

function LoadHide() {
    $("#general-loader").fadeOut();
    setTimeout(function () {
        $("#general-loader").remove()
    }, 500);
}

function LoadDetect() {
    if ($.active > 0 && $("#general-loader").length == 0) {
        LoadShow();
    } else if ($.active == 0) {
        LoadHide();
    }
}

setInterval(LoadDetect, 100);

var updnu_interval = -1;

function UpdateNavUsername() {
    $.ajax({
        url: "/api/user/info",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            $("#navusername").html(r.username);
            $(".only-signed-in").show();
            localStorage.setItem("username", r.username);
            if (window.location.pathname.indexOf("/login") != -1) {
                window.location.href = "/";
            }
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                $("#navusername").html("<a href='/user/login'>Sign in</a>&nbsp;&nbsp;  ");
                localStorage.setItem("username", "");
                clearInterval(updnu_interval);
                SessionExpired(true);
            }
        }
    });
}

function GeneralUpdateTheme() {
    navusername = $("#navusername").html();
    shortUserctrl = false;
    setInterval(function () {
        if (isphone) {
            if ($("#navusername").html() != "") {
                navusername = $("#navusername").html();
            }
            $("#navusername").html("");
            if (window.location.pathname == "/") {
                $("#progress-div").hide();
                $(".userctrl").attr("style", "");
            }
            return;
        }
        if ($(".userctrl").length != 0) {
            t = $(".userctrl").css("left");
            if (parseInt(t.slice(0, t.indexOf("px"))) / window.innerWidth < 0.6 && !shortUserctrl) {
                shortUserctrl = true;
                if ($("#navusername").html() != "") {
                    navusername = $("#navusername").html();
                }
                $("#navusername").html("");
                if (window.location.pathname == "/") {
                    $("#progress-div").hide();
                    $(".userctrl").attr("style", "");
                }
            } else if (parseInt(t.slice(0, t.indexOf("px"))) / window.innerWidth > 0.8 && shortUserctrl) {
                shortUserctrl = false;
                $("#navusername").html(navusername);
                if (window.location.pathname == "/") {
                    $("#progress-div").show();
                    $(".userctrl").attr("style", "height:4.5em;min-width: 14em;");
                }
            }
        }
    }, 50);

    $("table").addClass("table");
    if (localStorage.getItem("settings-theme") == "dark") {
        $("table").addClass("table-dark");
        $(".sub-div table").addClass("table-dark-subcontainer");
        $("tr").css("color", "#ffffff");
        $("th").css("color", "#ffffff");
        $("tr").css("background-color", "#333333");
        $("th").css("background-color", "#333333");
        $(".sub-div tr").css("background-color", "#444444");
        $(".sub-div th").css("background-color", "#444444");
    } else {
        $("table").addClass("table-light");
        $(".sub-div table").addClass("table-light-subcontainer");
        $("tr").css("color", "#000000");
        $("th").css("color", "#000000");
        $("tr").css("background-color", "#ffffff");
        $("th").css("background-color", "#ffffff");
        $(".sub-div tr").css("background-color", "#eeeeee");
        $(".sub-div th").css("background-color", "#eeeeee");
    }

    setInterval(function () {
        $("thead tr").removeClass("table-active");
        $(".fa-picture-o").addClass("fa-image");
        $(".fa-image").removeClass("fa-picture-o");
        if (localStorage.getItem("settings-theme") == "dark") {
            $("body").css("color", "#ffffff");
            $("body").css("background-color", "#333333");
            $(".sub-div ").css("background-color", "#444444");
            $("#content a,.container a").css("color", "#dddddd");

            $("hr").css("background-color", "#cccccc");
            $(".modal-content").css("background-color", "#333333");
            $(".fa-times").css("color", "white");

            $("textarea").css("color", "#ffffff");
            $("textarea").css("background-color", "#444444");
            $(".card,.card-body,.card-header").css("background-color", "#555555");
        } else {
            $("body").css("color", "#000000");
            $("body").css("background-color", "#ffffff");
            $(".sub-div ").css("background-color", "#eeeeee");
            $("#content a,.container a").css("color", "#222222");

            $("hr").css("background-color", "#222222");
            $(".modal-content").css("background-color", "#ffffff");
            $(".fa-times").css("color", "black");

            $("textarea").css("color", "#000000");
            $("textarea").css("background-color", "#eeeeee");
            $(".card,.card-body,.card-header").css("background-color", "#dddddd");
        }
    }, 50);
}

function GetUploadResult() {
    t = setInterval(function () {
        $.ajax({
            url: "/api/data/import",
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token"),
                getResult: true
            },
            success: function (r) {
                $("#result").html(r.msg);
                if (r.success == 0) {
                    $("#result").css("color", "red");
                    clearInterval(t);
                } else if (r.msg == "Success!") {
                    $("#result").css("color", "green");
                    clearInterval(t);
                }
                if (r.success == 2 || r.success == 0) {
                    clearInterval(t);
                }
            }
        });
    }, 3500);
}

$(document).ready(function () {
    if (localStorage.getItem("version") != null) {
        $("#version").html(localStorage.getItem("version") + '  <i class="fa fa-check-circle"></i>');
    }
    if (new Date().getTime() - lsGetItem("version-last-update", 0) > 600000) {
        $.ajax({
            url: "/api/version",
            method: 'GET',
            async: true,
            dataType: "json",
            success: function (r) {
                $("#version").html(r.version + '  <i class="fa fa-check-circle"></i>');
                localStorage.setItem("version", r.version);
                localStorage.setItem("version-last-update", new Date().getTime());
            }
        });
    }

    if (localStorage.getItem("username") != null && localStorage.getItem("username") != "") {
        username = localStorage.getItem("username");
        $("#navusername").html(username);
        $(".only-signed-in").show();
        setInterval(UpdateNavUsername, 600000);
    } else {
        $.ajax({
            url: "/api/user/info",
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                $("#navusername").html(r.username);
                $(".only-signed-in").show();
                localStorage.setItem("username", r.username);
                setInterval(UpdateNavUsername, 60000);
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    $("#navusername").html("<a href='/user/login'>Sign in</a>&nbsp;&nbsp;  ");
                    localStorage.setItem("username", "");
                    SessionExpired(true);
                }
            }
        });
    }

    if (!isphone) {
        if (window.location.pathname.indexOf("/book") == -1) {
            $("#navigate").after(`<div id="book-div" class="book-side" style="display:none">
            <div class="book-side-content">
                <h2 style="float:left">Books</h2>
                <button type="button" class="btn btn-outline-secondary btn-sm" style="margin:0.5em;font-size:0.7em" onclick="RefreshBookList()"
                    id="book-list-refresh-btn"><i class="fa fa-sync"></i></button>
                <button type="button" class="close" style="float:right;background-color:transparent;border:none" aria-label="Close"
                    onclick="$('#book-div').fadeOut()">
                    <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                </button>

            </div>
            <div class="book-side-content-scroll" id="book-list">
                <div>
                    <p>Create Book: </p>
                    <div class="input-group mb-3 w-75">
                        <span class="input-group-text" id="basic-addon1">Name</span>
                        <input type="text" class="form-control" id="create-book-name" aria-describedby="basic-addon1">
                        <div class="input-group-append">
                            <button class="btn btn-outline-primary" type="button"
                                onclick="CreateBook('#create-book-name')">Create</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>`);
        }
    }

    if (window.location.pathname.indexOf("/book") == -1) {
        $(".leftside").append(`<div class="sqbtn">
            <a id="book-btn" href="/book"><i class="fa fa-book"></i></a><br>
        </div>`);
    } else {
        $(".leftside").append(`<div class="sqbtn">
            <a id="book-btn" href="#" onclick="BackToList()"><i class="fa fa-book"></i></a><br>
        </div>`);
    }
    if (localStorage.getItem("userId") != null && localStorage.getItem("userId") != "-1") {
        $(".leftside").append(`<div class="sqbtn">
            <a href="/share"><i class="fa fa-share-alt"></i></a><br>
        </div>`);
    }
    if (window.location.pathname.indexOf("/discovery") == -1) {
        $(".leftside").append(`<div class="sqbtn">
            <a href="/discovery"><i class="fa fa-paper-plane"></i></a><br>
        </div>`);
    } else {
        $(".leftside").append(`<div class="sqbtn">
            <a href="#" onclick="BackToList()"><i class="fa fa-paper-plane"></i></a><br>
        </div>`);
    }
    if (localStorage.getItem("isAdmin") == true) {
        $(".leftside").append("<hr>");
        $(".leftside").append(`<div class="sqbtn">
            <a href="/admin/gui" id="book-btn"><i class="fa fa-screwdriver-wrench"></i></a><br>
        </div>
        <div class="sqbtn">
            <a href="/admin/cli" id="book-btn"><i class="fa fa-terminal"></i></a><br>
        </div>`);
    }

    if (isphone) {
        $(".leftside br").remove();
        $(".leftside").css("top", "0");
        $(".leftside").css("left", "2%");
        $(".leftside").css("height", "3em");
        $(".leftside").css("width", "fit-content");
        $(".leftside").css("padding-top", "0.7em");
        $(".leftside").css("padding-left", "0.6em");
        $(".leftside").css("padding-right", "0.4em");
        $(".leftside").css("padding-bottom", "0.7em");
        $(".leftside").css("border-bottom-left-radius", "0.5em");
        $(".leftside").css("border-top-right-radius", "0");
        $(".leftside .icon").css("margin", "0.2em");
        $(".leftside .icon").css("margin-top", "-0.7em");
        $(".leftside .sqbtn").css("margin", "0.3em");
        $(".leftside .sqbtn").css("font-size", "0.8em");
        $(".leftside .sqbtn").css("display", "inline-block");
        $(".userctrl").css("right", "2%");
        $(".leftside hr").remove();
        $("#footer-text").children().css("float", "none");

        $('head').append('<link rel="stylesheet" href="/css/mobile.css" type="text/css" />');
    }
    GeneralUpdateTheme();

    $("#book-btn").hover(function () {
        ShowBook();
    });
    $("#content").hover(function () {
        $("#book-div").fadeOut();
    });
    $("#create-book-name").keypress(function (e) {
        if (e.which == 13 || e.which == 13 && e.ctrlKey) {
            CreateBook("#create-book-name");
        }
    });
});

var captchaToken = undefined;

function RefreshCaptcha(submitfunc) {
    $.ajax({
        url: "/api/captcha",
        method: 'GET',
        async: true,
        success: function (r) {
            if (r.success == true) {
                $("#captcha-answer").val("");
                setTimeout(function () {
                    $("#captcha-answer").focus();
                }, 300);
                captchaToken = r.captchaToken;
                captchaBase64 = r.captchaBase64;
                $("#captcha").html("<img style='height:2em' src='data:image/png;base64," + captchaBase64 + "'>");
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function ShowCaptcha(submitfunc) {
    GenModal(`<i class="fa fa-robot"></i>  Captcha`,
        `<p>Please solve this captcha to prove that you are not a robot:</p>
            <div class="input-group mb-3">
                <input type="text" class="form-control" id="captcha-answer" aria-describedby="captcha">
                <span class="input-group-text" id="captcha" onclick="RefreshCaptcha();">Fetching captcha&nbsp;&nbsp;<i class='fa fa-spinner fa-spin'></i></span>
            </div>`,
        `<button type="button" class="btn btn-primary" id="captcha-submit" onclick="` + submitfunc + `();">Submit</button>`,
        function () {
            captchaToken = undefined;
        }, "captchaModal"
    );
    OnSubmit("#captcha-answer", function () {
        $("#captcha-submit").click();
    });

    $.ajax({
        url: "/api/captcha",
        method: 'GET',
        async: true,
        success: function (r) {
            if (r.success == true) {
                setTimeout(function () {
                    $("#captcha-answer").focus();
                }, 300);
                captchaToken = r.captchaToken;
                captchaBase64 = r.captchaBase64;
                $("#captcha").html("<img style='height:2em' src='data:image/png;base64," + captchaBase64 + "'>");
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}