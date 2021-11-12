// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var groupId = -1;
var bookId = -1;
var bookName = "";
var selected = [];
var member = [];

function UpdateGroupMember() {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');

    table = $("#memberList").DataTable();
    table.clear();
    table.row.add([
        ["Loading... <i class='fa fa-spinner fa-spin'></i>"],
        [""],
    ]);
    table.draw();
    if (localStorage.getItem("settings-theme") == "dark") {
        $("tr").attr("style", "background-color:#333333");
    }
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
            $("title").html(bookName + " | My Memo");
            $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="UpdateGroupMember()" id="refresh-btn"><i class="fa fa-refresh"></i></button>');

            $("#groupDescription").html(r.description.replaceAll("\n", "<br>"));

            for (var i = 0; i < r.member.length; i++) {
                table.row.add([
                    [r.member[i].username],
                    [r.member[i].progress]
                ]).node().id = r.member[i].userId;
            }
            table.draw();
            if (localStorage.getItem("settings-theme") == "dark") {
                $("tr").attr("style", "background-color:#333333");
            }

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        },
        error: function (r, textStatus, errorThrown) {
            table.row.add([
                ["Failed to fetch group member list"],
                [""],
            ]);
            table.draw();
            if (localStorage.getItem("settings-theme") == "dark") {
                $("tr").attr("style", "background-color:#333333");
            }

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });

    selected = [];
}

function TransferOwnershipShow() {
    $("#transferOwnershipModal").modal("show");
}

function GroupOperation(operation) {
    if (operation == "makeEditor" || operation == "kick" || operation == "transferOwnership") {
        if (selected.length == 0) {
            return;
        }
        if (operation == "transferOwnership" && selected.length > 1) {
            NotyNotification("Please select only one user!", type = 'warning');
            return;
        }
        $.ajax({
            url: '/api/group/manage',
            method: 'POST',
            async: true,
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
                    NotyNotification(r.msg);
                    if (operation == "transferOwnership") {
                        $("#transferOwnershipModal").modal("hide");
                    }
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
            error: function (r, textStatus, errorThrown) {
                $("#navusername").html("Sign in");
                localStorage.setItem("username", "");
            }
        });
    }

    groupId = getUrlParameter("groupId");
    UpdateGroupMember();
}