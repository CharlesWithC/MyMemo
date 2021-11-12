// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var discoveryId = -1;
var discoveryList = [];
var liked = false;
var shareCode = "";
var distype = 1;
var title = "";
var description = "";

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
    } else {
        $("#questionList tr").attr("style", "background-color:#ffffff");
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
            l = ["", "Book", "Group"];
            for (var i = 0; i < discoveryList.length; i++) {
                btns = '';
                if (localStorage.getItem("isAdmin") == "1" || discoveryList[i].publisher == localStorage.getItem("username")) {
                    btns += '&nbsp;&nbsp;<button id="admin-delete-' + discoveryList[i].discoveryId + '" class="btn btn-outline-danger btn-sm" type="button" onclick="AdminUnpublishDiscoveryConfirm(' + discoveryList[i].discoveryId + ')">Delete</button>';
                }
                table.row.add([
                    [discoveryList[i].title],
                    [discoveryList[i].description],
                    [l[discoveryList[i].type]],
                    [discoveryList[i].publisher],
                    [discoveryList[i].views],
                    [discoveryList[i].likes],
                    //[discoveryList[i].views + " <i class='fa fa-eye'></i>&nbsp;&nbsp;" + discoveryList[i].likes + "<i class='fa fa-heart' style='color:red'></i>"],
                    [btns]
                ]).node().id = discoveryList[i].discoveryId;
            }

            table.draw();

            if (localStorage.getItem("settings-theme") == "dark") {
                $("td").attr("style", "background-color:#333333");
            } else {
                $("#questionList tr").attr("style", "background-color:#ffffff");
            }

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });
}

function AdminUnpublishDiscoveryConfirm(disid) {
    $("#admin-delete-" + disid).html("Confirm?");
    $("#admin-delete-" + disid).attr("onclick", "AdminUnpublishDiscovery(" + disid + ");");
}

function AdminUnpublishDiscovery(disid) {
    publisher = "";
    for (var i = 0; i < discoveryList.length; i++) {
        if (discoveryList[i].discoveryId == disid) {
            publisher = discoveryList[i].publisher;
            break;
        }
    }
    if (localStorage.getItem("isAdmin") != "1" && publisher != localStorage.getItem("username")) {
        return;
    }
    $.ajax({
        url: '/api/discovery/unpublish',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: disid,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                RefreshDiscovery();

                NotyNotification(r.msg);
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

function UpdateDiscoveryQuestionList() {
    $(".title").html('Discovery');
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

            if (r.isPublisher || localStorage.getItem("isAdmin") == "1") {
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
        error: function (r, textStatus, errorThrown) {
            NotyNotification('Error ' + r.status + ": " + errorThrown, type = 'error');
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
                NotyNotification("Success! Book imported!");
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

function ShowDiscovery(discoveryId) {
    window.location.href = "/discovery?discoveryId=" + discoveryId
}

function UpdateInformationShow() {
    $("#discovery-title").val(title);
    $("#discovery-description").val(description);
    $('#editPostModal').modal('show');
}

function UpdateInformation() {
    title = $("#discovery-title").val();
    description = $("#discovery-description").val();

    $.ajax({
        url: '/api/discovery/update',
        method: 'POST',
        async: true,
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

                NotyNotification(r.msg);
                $('#editPostModal').modal('hide');
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

                NotyNotification(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
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
        UpdateDiscoveryQuestionList();
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
            error: function (r, textStatus, errorThrown) {
                $("#navusername").html("Sign in");
                localStorage.setItem("username", "");
            }
        });
    }
}