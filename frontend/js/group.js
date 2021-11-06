// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var groupId = -1;
var bookId = -1;
var bookName = "";
var selected = [];
var member = [];

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

function BackToHome() {
    window.location.href = '/';
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
    return false;
};

function UpdateGroupMember() {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');

    table = $("#memberList").DataTable();
    table.clear();
    table.row.add([
        ["Loading... <i class='fa fa-spinner fa-spin'></i>"],
        [""],
    ]);
    table.draw();
    $("tr").attr("style", "background-color:#333333");
    table.clear();

    $.ajax({
        url: "/api/group/member",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token"),
            groupId: groupId
        },
        success: function (r) {
            bookName = r.name;
            member = r.member;
            
            if (r.isOwner) {
                $(".manage").show();
                $(".member").attr("style", "position:relative;width:55%;float:left;");
            } else {
                $(".manage").hide();
                $(".member").attr("style", "width:100%");
            }
            $("title").html("My Memo - " + bookName);
            $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="UpdateGroupMember()" id="refresh-btn"><i class="fa fa-refresh"></i></button>');

            $("#groupDescription").html(r.description.replaceAll("\n", "<br>"));

            for (var i = 0; i < r.member.length; i++) {
                table.row.add([
                    [r.member[i].username],
                    [r.member[i].progress]
                ]).node().id = r.member[i].userId;
            }
            table.draw();
            $("tr").attr("style", "background-color:#333333");

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        },
        error: function (r) {
            table.row.add([
                ["Failed to fetch group member list"],
                [""],
            ]);
            table.draw();
            $("tr").attr("style", "background-color:#333333");

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });

    selected = [];
}

function TransferOwnershipShow() {
    $("#transferOwnershipModal").modal("toggle");
}

function GroupOperation(operation) {
    if (operation == "makeEditor" || operation == "kick" || operation == "transferOwnership") {
        if (selected.length == 0) {
            return;
        }
        if (operation == "transferOwnership" && selected.length > 1) {
            new Noty({
                theme: 'mint',
                text: "Make sure you only selected one user!",
                type: 'warning',
                layout: 'bottomRight',
                timeout: 3000
            }).show();
            return;
        }
        $.ajax({
            url: '/api/group/manage',
            method: 'POST',
            async: false,
            dataType: "json",
            data: {
                groupId: groupId,
                operation: operation,
                users: JSON.stringify(selected),
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success == true) {
                    UpdateGroupMember();
                    new Noty({
                        theme: 'mint',
                        text: r.msg,
                        type: 'success',
                        layout: 'bottomRight',
                        timeout: 3000
                    }).show();
                    if (operation == "transferOwnership") {
                        $("#transferOwnershipModal").modal("toggle");
                    }
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
                if (r.status == 401) {
                    SessionExpired();
                }
            }
        });
    }
}

function PageInit() {
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

    groupId = getUrlParameter("groupId");
    UpdateGroupMember();
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