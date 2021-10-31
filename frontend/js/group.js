// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var groupId = -1;
var wordBookName = "";
var selected = [];

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
    table = $("#memberList").DataTable();
    table.clear();
    table.row.add([
        ["Loading... <i class='fa fa-spinner fa-spin'></i>"],
        [""],
    ]);
    table.draw();
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
            wordBookName = r.name;
            $("title").html("Word Memo - " + wordBookName);
            $(".title").html(wordBookName);

            $("#groupDescription").html(r.description.replaceAll("\n", "<br>"));

            for (var i = 0; i < r.member.length; i++) {
                table.row.add([
                    [r.member[i].username],
                    [r.member[i].progress]
                ]).node().id = r.member[i].userId;
            }
            table.draw();
        },
        error: function (r) {
            table.row.add([
                ["Failed to fetch group member list"],
                [""],
            ]);
            table.draw();
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
    groupId = getUrlParameter("groupId");
    UpdateGroupMember();
}