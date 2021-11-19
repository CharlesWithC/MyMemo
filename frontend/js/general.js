// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

function NotyNotification(text, type = 'success', timeout = 3000, layout = 'bottomRight') {
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
    window.location.href = '/data/import'
}

function Export() {
    window.location.href = '/data/export'
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
    localStorage.removeItem("userId");
    localStorage.removeItem("username");
    localStorage.removeItem("token");
    localStorage.removeItem("memo-question-id");
    localStorage.removeItem("memo-book-id");
    localStorage.removeItem("book-list");
    localStorage.removeItem("question-list");

    $("#navusername").html("Sign in");

    NotyNotification('You are now signed out!');
}

function SessionExpired() {
    NotyNotification('Login session expired! Please login again!', type = 'error');
    localStorage.removeItem("userId");
    localStorage.removeItem("token");
    setTimeout(GoToUser, 3000);
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
};

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
            localStorage.setItem("book-list", JSON.stringify(bookList));
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
    $("#book-list-refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');
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
            localStorage.setItem("book-list", JSON.stringify(bookList));
            UpdateBookDisplay();
            $("#book-list-refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });
}

function CreateBook() {
    bookName = $("#create-book-name").val();

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
    $(".footer").before("<div id='general-loader' class='loader' style='display:none'><i class='fa fa-spinner fa-spin'></i></div>");
    $("#general-loader").fadeIn();
}

function LoadHide() {
    $("#general-loader").fadeOut();
    setTimeout(function () {
        $("#general-loader").remove()
    }, 500);
}

function LoadDetect() {
    if ($.active > 0) {
        LoadShow();
    } else {
        LoadHide();
    }
}

setInterval(LoadDetect, 10);

var updnu_interval = -1;

function UpdateNavUsername(){
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
            $("#sign-out-btn").show();
            localStorage.setItem("username", r.username);
        },
        error: function (r, textStatus, errorThrown) {
            $("#navusername").html("Sign in");
            localStorage.setItem("username", "");
            clearInterval(updnu_interval);
        }
    });
}

$(document).ready(function () {
    if (localStorage.getItem("username") != null && localStorage.getItem("username") != "") {
        username = localStorage.getItem("username");
        $("#navusername").html(username);
        $("#sign-out-btn").show();
        setInterval(UpdateNavUsername, 60000);
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
                $("#sign-out-btn").show();
                localStorage.setItem("username", r.username);
                setInterval(UpdateNavUsername, 60000);
            },
            error: function (r, textStatus, errorThrown) {
                $("#navusername").html("Sign in");
                localStorage.setItem("username", "");
            }
        });
    }

    if(localStorage.getItem("isAdmin") == true){
        $(".leftside").append("<hr>");
        $(".leftside").append('<div class="sqbtn">\
            <a href="#" onclick="window.location.href=\'/admin/cli\'" id="book-btn"><i class="fa fa-terminal"></i><br>Terminal</a>\
        </div>');
        $(".leftside").append('<div class="sqbtn">\
            <a href="#" onclick="window.location.href=\'/admin/userlist\'" id="book-btn"><i class="fa fa-users"></i><br>Users</a>\
        </div>');
    }
});

function sort_object(obj) {
    items = Object.keys(obj).map(function(key) {
        return [key, obj[key]];
    });
    items.sort(function(first, second) {
        return second[1] - first[1];
    });
    sorted_obj={}
    $.each(items, function(k, v) {
        use_key = v[0]
        use_value = v[1]
        sorted_obj[use_key] = use_value
    })
    return(sorted_obj)
} 