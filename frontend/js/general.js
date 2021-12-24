// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

function NotyNotification(text, type = 'success', timeout = 3000, layout = 'topRight') {
    new Noty({
        theme: 'mint',
        text: text,
        type: type,
        layout: layout,
        timeout: timeout
    }).show();
}

function GoToUser() {
    window.location.href = "/user"
}

function BackToHome() {
    window.location.href = '/';
}

function Import() {
    window.location.href = '/data/import';
}

function Export() {
    window.location.href = '/data/export';
}

function UserEvents() {
    window.location.href = '/notifications';
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
    localStorage.clear();
    localStorage.setItem("first-use", "0");
    localStorage.setItem("sign-out", "1");

    $("#navusername").html("<a href='/user/login'>Sign in</a>&nbsp;&nbsp;  ");

    NotyNotification('You are now signed out!');

    setTimeout(function () {
        window.location.href = "/user/login";
    }, 1000);
}

function SessionExpired() {
    NotyNotification('Login session expired! Please login again!', type = 'error');
    localStorage.clear();
    localStorage.setItem("first-use", "0");
    localStorage.setItem("sign-out", "1");
    setTimeout(function () {
        window.location.href = "/user/login"
    }, 3000);
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

function ssGetItem(lsItemName, defaultValue = 0) {
    if (sessionStorage.getItem(lsItemName) == null || sessionStorage.getItem(lsItemName) == "undefined") {
        sessionStorage.setItem(lsItemName, defaultValue);
        return defaultValue;
    } else {
        return sessionStorage.getItem(lsItemName);
    }
}


bookList = JSON.parse(ssGetItem("book-list", JSON.stringify([])));

function UpdateBookDisplay() {
    $(".book").remove();
    for (var i = 0; i < bookList.length; i++) {
        book = bookList[i];
        wcnt = "";
        if (book.bookId == 0) {
            wcnt = book.questions.length + ' questions';
        } else {
            wcnt = book.progress + ' memorized / ' + book.questions.length + ' questions';
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

function UpdateBookList() {
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
                sessionStorage.setItem("book-list", JSON.stringify(bookList));
            } catch {
                console.warning("Cannot store book list to Session Storage, aborted!");
            }
            UpdateBookDisplay();
        }
    });
}

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
                sessionStorage.setItem("book-list", JSON.stringify(bookList));
            } catch {
                console.warning("Cannot store book list to Session Storage, aborted!");
            }
            UpdateBookDisplay();
            $("#book-list-refresh-btn").html('<i class="fa fa-sync"></i>');
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
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
                NotyNotification('Success! Book created!');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
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
            }
        }
    });
}

function GeneralUpdateTheme() {
    navusername = $("#navusername").html();
    shortUserctrl = false;
    setInterval(function () {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
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
        $(".subcontainer table").addClass("table-dark-subcontainer");
        $("tr").css("color", "#ffffff");
        $("th").css("color", "#ffffff");
        $("tr").css("background-color", "#333333");
        $("th").css("background-color", "#333333");
        $(".subcontainer tr").css("background-color", "#444444");
        $(".subcontainer th").css("background-color", "#444444");
    } else {
        $("table").addClass("table-light");
        $(".subcontainer table").addClass("table-light-subcontainer");
        $("tr").css("color", "#000000");
        $("th").css("color", "#000000");
        $("tr").css("background-color", "#ffffff");
        $("th").css("background-color", "#ffffff");
        $(".subcontainer tr").css("background-color", "#eeeeee");
        $(".subcontainer th").css("background-color", "#eeeeee");
    }

    setInterval(function () {
        $("thead tr").removeClass("table-active");
        $(".dataTables_paginate > span > span").removeClass("ellipsis");
        $(".dataTables_paginate > span > span").addClass("btn btn-outline-secondary btn-sm btn-paginate");
        $(".dataTables_paginate > span > span").css("margin", "0.2em");
        $(".paginate_button").addClass("btn btn-outline-secondary btn-sm btn-paginate");
        $(".paginate_button").css("margin", "0.2em");
        $(".paginate_button").removeClass("paginate_button");
        $("table,.dataTables_scrollHeadInner").css("width", "100%");
        if ($("table").DataTable != undefined)
            $("table").DataTable().columns.adjust();
        $(".fa-picture-o").addClass("fa-image");
        $(".fa-image").removeClass("fa-picture-o");
        if (localStorage.getItem("settings-theme") == "dark") {
            $("body").css("color", "#ffffff");
            $("body").css("background-color", "#333333");
            $(".subcontainer").css("background-color", "#444444");
            $("#content a,.container a").css("color", "#dddddd");

            $("hr").css("background-color", "#cccccc");
            $(".modal-content").css("background-color", "#333333");
            $(".fa-times").css("color", "white");

            $("textarea").css("color", "#ffffff");
            $("textarea").css("background-color", "#444444");
            $(".card,.card-body,.card-header").css("background-color", "#555555");

            //$(".dataTables_paginate a").css("background-color", "#d3d3d3");
            //$(".dataTables_paginate span").css("background-color", "#d3d3d3");
            $(".dataTables_info").css("color", "#ffffff");
            $(".dataTables_length").css("color", "#ffffff");
            $(".dataTables_length a").css("color", "#ffffff");
        } else {
            $("body").css("color", "#000000");
            $("body").css("background-color", "#ffffff");
            $(".subcontainer").css("background-color", "#eeeeee");
            $("#content a,.container a").css("color", "#222222");

            $("hr").css("background-color", "#222222");
            $(".modal-content").css("background-color", "#ffffff");
            $(".fa-times").css("color", "black");

            $("textarea").css("color", "#000000");
            $("textarea").css("background-color", "#eeeeee");
            $(".card,.card-body,.card-header").css("background-color", "#dddddd");

            //$(".dataTables_paginate a").css("background-color", "#ffffff");
            //$(".dataTables_paginate span").css("background-color", "#ffffff");
            $(".dataTables_info").css("color", "#000000");
            $(".dataTables_length").css("color", "#000000");
            $(".dataTables_length a").css("color", "#000000");
        }
    }, 50);
}

// ModifyDataTableSearchBox
function MDTSB(tableName) {
    $("#" + tableName + "_length").css("float", "left");
    $("#" + tableName + "_length").after('<div id="tmp' + tableName + '" class="dataTables_filter input-group mb-3" style="float:right;max-width:15em">\
        <span class="input-group-text" id="basic-addon1">Search</span>\
    </div>');
    $("#" + tableName + "_filter > label > input").addClass("form-control");
    $("#" + tableName + "_filter > label > input").css("max-width", "15em");
    $("#" + tableName + "_filter > label > input").appendTo("#tmp" + tableName);
    $("#" + tableName + "_filter").attr("id", "ttmp" + tableName);
    $("#tmp" + tableName).attr("id", tableName + "_filter");
    $("#ttmp" + tableName).remove();
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
                }
            }
        });
    }

    if (!/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
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
            <a href="/admin/cli" id="book-btn"><i class="fa fa-terminal"></i></a><br>
        </div><div class="sqbtn">
            <a href="/admin/userlist" id="book-btn"><i class="fa fa-address-book"></i></a><br>
        </div>`);
    }

    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
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
    }

    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        $('head').append('<link rel="stylesheet" href="/css/mobile.css" type="text/css" />');
    }
    GeneralUpdateTheme();

    $("#book-btn").hover(function () {
        ShowBook();
    });
    $("#content").hover(function () {
        $("#book-div").fadeOut();
    });
    $("#create-book-name").on('keypress', function (e) {
        if (e.which == 13 || e.which == 13 && e.ctrlKey) {
            CreateBook("#create-book-name");
        }
    });

    $(".btn-paginate").click(function () {
        $("#dataTables_paginate").fadeOut();
        setTimeout(function () {
            $("#dataTables_paginate").fadeIn();
        }, 50);
    })
});