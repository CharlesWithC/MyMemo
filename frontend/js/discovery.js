// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

function lsGetItem(lsItemName, defaultValue = 0) {
    if (localStorage.getItem(lsItemName) == null || localStorage.getItem(lsItemName) == "undefined") {
        localStorage.setItem(lsItemName, defaultValue);
        return defaultValue;
    } else {
        return localStorage.getItem(lsItemName);
    }
}

var discoveryId = -1;
var discoveryList = [];
var liked = false;
var shareCode = "";
var distype = 1;
var title = "";
var description = "";

function SessionExpired() {
    new Noty({
        theme: 'mint',
        text: 'Login session expired! Please login again!',
        type: 'error',
        layout: 'bottomRight',
        timeout: 3000
    }).show();
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

function BackToHome() {
    window.location.href = '/';
}

function GoToUser() {
    window.location.href = "/user"
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
    localStorage.removeItem("userid");
    localStorage.removeItem("username");
    localStorage.removeItem("token");
    localStorage.removeItem("memo-question-id");
    localStorage.removeItem("memo-book-id");
    localStorage.removeItem("book-list");
    localStorage.removeItem("question-list");

    $("#navusername").html("Sign in");

    new Noty({
        theme: 'mint',
        text: 'Success! You are now signed out!',
        type: 'success',
        layout: 'bottomRight',
        timeout: 3000
    }).show();
}

function RefreshDiscovery() {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');

    table = $("#discoveryList").DataTable();
    table.clear();
    table.row.add([
        [""],
        [""],
        [""],
        ["Loading <i class='fa fa-spinner fa-spin'></i>"],
        [""],
        [""],
        [""]
    ]);
    table.draw();
    if (localStorage.getItem("settings-theme") == "dark") {
        $("td").attr("style", "background-color:#333333");
    }
    table.clear();

    $.ajax({
        url: "/api/discovery",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            discoveryList = r;
            l = ["", "Book", "Group"]
            for (var i = 0; i < discoveryList.length; i++) {
                table.row.add([
                    [discoveryList[i].title],
                    [discoveryList[i].description],
                    [l[discoveryList[i].type]],
                    [discoveryList[i].publisher],
                    [discoveryList[i].views],
                    [discoveryList[i].likes],
                    //[discoveryList[i].views + " <i class='fa fa-eye'></i>&nbsp;&nbsp;" + discoveryList[i].likes + "<i class='fa fa-heart' style='color:red'></i>"],
                    ['<button class="btn btn-primary btn-sm" type="button" onclick="ShowDiscovery(' + discoveryList[i].discoveryId + ')">Show</button>']
                ]);
            }

            table.draw();

            if (localStorage.getItem("settings-theme") == "dark") {
                $("td").attr("style", "background-color:#333333");
            }

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });
}

function UpdateDiscoveryWordList() {
    table = $("#questionList").DataTable();
    table.clear();
    table.row.add([
        ["Loading <i class='fa fa-spinner fa-spin'></i>"],
        [""]
    ]);
    table.draw();
    table.clear();

    $.ajax({
        url: "/api/discovery/" + discoveryId,
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            title = r.title;
            description = r.description;
            liked = r.liked;
            if (liked) {
                $(".title").html(r.title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
            } else {
                $(".title").html(r.title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart-o" style="color:red"></i></a>');
            }
            $("#detail-publisher").html(r.publisher);
            $("#detail-description").html(r.description);

            shareCode = r.shareCode;
            $("#shareCode").html(shareCode);
            $("#groupCode").html(shareCode);

            if (r.isPublisher) {
                $(".publisher-only").show();
            } else {
                $(".publisher-only").hide();
            }

            if (localStorage.getItem("userId") == null) {
                $(".user-only").hide();
            } else {
                $(".user-only").show();
                distype = r.type;
                if (distype == 1) {
                    $(".book-only").show();
                    $(".group-only").hide();
                } else if (distype == 2) {
                    $(".book-only").hide();
                    $(".group-only").show();
                }
            }

            questionList = r.questions;

            for (var i = 0; i < questionList.length; i++) {
                table.row.add([
                    [questionList[i].question],
                    [questionList[i].answer]
                ]);
            }
            table.draw();
        },
        error: function (r) {
            new Noty({
                theme: 'mint',
                text: r.msg,
                type: 'error',
                layout: 'bottomRight',
                timeout: 3000
            }).show();
            $(".discovery-list").show();
            $(".discovery-detail").hide();
            discoveryId = -1;
        }
    });
}

function ImportBook() {
    $.ajax({
        url: '/api/book/create',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            name: shareCode,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success!',
                    type: 'success',
                    layout: 'topLeft',
                    timeout: 3000
                }).show();
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'topLeft',
                    timeout: 3000
                }).show();
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

function ShowDiscovery(discoveryId) {
    window.location.href = "/discovery?discoveryId=" + discoveryId
}

function UpdateInformationShow() {
    $("#discovery-title").val(title);
    $("#discovery-description").val(description);
    $('#editPostModal').modal('toggle');
}

function UpdateInformation() {
    title = $("#discovery-title").val();
    description = $("#discovery-description").val();

    $.ajax({
        url: '/api/discovery/update',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            discoveryId: discoveryId,
            title: title,
            description: description,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                if (liked) {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
                } else {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart-o" style="color:red"></i></a>');
                }
                $("#detail-description").html(description);

                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
                $('#editPostModal').modal('toggle');
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
                $('#editPostModal').modal('toggle');
            }
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function LikePost() {
    liked = 1 - liked;
    if (liked) {
        $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
    } else {
        $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart-o" style="color:red"></i></a>');
    }
    $.ajax({
        url: '/api/discovery/like',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: discoveryId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                liked = r.liked;
                if (liked) {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
                } else {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart-o" style="color:red"></i></a>');
                }

                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
            }
        },
        error: function (r) {
            liked = 1 - liked;
            if (liked) {
                $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
            } else {
                $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart-o" style="color:red"></i></a>');
            }
        }
    });
}

function PageInit() {
    discoveryId = getUrlParameter("discoveryId");
    if (discoveryId == -1) {
        RefreshDiscovery();
    } else {
        $(".discovery-list").hide();
        $(".discovery-detail").show();
        UpdateDiscoveryWordList();
    }

    // Update username
    if (localStorage.getItem("username") != null && localStorage.getItem("username") != "") {
        username = localStorage.getItem("username");
        if (username.length <= 16) {
            $("#navusername").html(username);
        } else {
            $("#navusername").html("Account");
        }
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
                if (r.username.length <= 16) {
                    $("#navusername").html(r.username);
                } else {
                    $("#navusername").html("Account");
                }
                localStorage.setItem("username", r.username);
            },
            error: function (r) {
                $("#navusername").html("Sign in");
                localStorage.setItem("username", "");
            }
        });
    }
}