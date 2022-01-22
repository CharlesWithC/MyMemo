// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var groupId = -1;
var bookId = -1;
var bookName = "";
var member = [];
var isOwner = false;
var curModalId = "";
var groupCode = "";

var page = 1;
var pageLimit = 10;
var orderBy = "progress";
var order = "desc";
var search = "";

function UpdateGroupMember() {
    $("#refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');

    $.ajax({
        url: "/api/group/member",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupId: groupId,
            page: page,
            pageLimit: pageLimit,
            orderBy: orderBy,
            order: order,
            search: search,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            bookName = r.name;
            member = r.data;
            isOwner = r.isOwner;
            total = r.total;
            totalMember = r.totalMember;
            $("tbody tr").remove();

            $("title").html(bookName + " - My Memo");
            $(".title").html(bookName);

            $("#groupName").html(bookName);
            $("#groupDescription").html(marked.parse(r.description.replaceAll("\n", "<br>")));

            for (var i = 0; i < member.length; i++) {
                btns = '';
                if (isOwner) {
                    if (member[i].username.indexOf("(Editor)") != -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-primary btn-sm" type="button" onclick="GroupOperation(2, ' + member[i].userId + ')"><i class="fa fa-user-pen"></i> Undo make editor</button>';
                    } else if (member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-primary btn-sm" type="button" onclick="GroupOperation(2, ' + member[i].userId + ')"><i class="fa fa-user-pen"></i> Make editor</button>';
                    }
                    if (member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-warning btn-sm" type="button" onclick="GroupOperation(1, ' + member[i].userId + ')"><i class="fa fa-ban"></i> Kick</button>';
                    }
                    if (member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-danger btn-sm" type="button" onclick="TransferOwnershipShow(' + member[i].userId + ')"><i class="fa fa-random"></i> Transfer ownership</button>';
                    }
                }
                member[i].username = member[i].username.replaceAll("(Owner)", '<i class="fa fa-crown"></i>');
                member[i].username = member[i].username.replaceAll("(Editor)", '<i class="fa fa-user-pen"></i>');
                AppendTableData("memberList", [member[i].username, member[i].progress, btns], member[i].userId);
            }
            l = (page - 1) * pageLimit + 1;
            r = l + member.length - 1;
            if (member.length == 0) {
                AppendTableData("memberList", ["No data available"], undefined, "100%");
                l = 0;
            }

            PaginateTable("memberList", page, total, "MemberListPage");
            SetTableInfo("memberList", "<p style='opacity:80%'>Showing " + l + " - " +
                r + " / " + totalMember + "</p>");

            if (!isOwner) {
                $("#memberList tr > *:nth-child(3)").hide();
            } else {
                $("#memberList tr > *:nth-child(3)").show();
            }
            for (var i = 0; i < member.length; i++) {
                if (member[i].username.indexOf("(Owner)") != -1) {
                    $("#" + member[i].userId).css("color", "#ff5555");
                } else if (member[i].username.indexOf("(Editor)") != -1) {
                    $("#" + member[i].userId).css("color", "yellow");
                }
            }

            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function MemberListPage(p) {
    page = p;
    UpdateGroupMember();
}

function Search() {
    search = $("#search-content").val();
    orderBy = "none";
    SortTable(orderBy);
    UpdateGroupMember();
}

function MemberListSort(id) {
    orderBy = id;
    if ($("#sorting_" + id).hasClass("sorting-desc")) {
        order = "desc";
    } else {
        order = "asc";
    }
    UpdateGroupMember();
}

function UpdatePageLimit(pl) {
    if (pageLimit != pl) {
        page = Math.ceil((page - 1) * pageLimit / pl + 1);
        pageLimit = pl;
        UpdateGroupMember();
    }
}

function TransferOwnershipShow(uid) {
    curModalId = GenModal(`<i class="fa fa-random"></i> Transfer Ownership`,
        `<p>Are you sure to transfer ownership? Make sure you trust that user!</p>
        <p>You cannot undo this operation unless the new owner transferred ownership back.</p>`,
        `<button id="transfer-ownership-btn" type="button" class="btn btn-danger" onclick="GroupOperation(3, ` + uid + `)">Transfer</button>`);
}

function GroupOperation(operation, uid) {
    list = [uid];
    if (operation == 2 || operation == 1 || operation == 3) {
        if (list.length == 0) {
            return;
        }
        if (operation == 3 && list.length > 1) {
            NotyNotification("Please select only one user!", type = 'warning');
            return;
        }
        l = ["", "kick", "makeEditor", "transferOwnership"]
        $.ajax({
            url: '/api/group/manage',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                groupId: groupId,
                operation: l[operation],
                users: JSON.stringify(list),
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success == true) {
                    UpdateGroupMember();
                    NotyNotification(r.msg);
                    if (operation == 3) {
                        $("#transferOwnershipModal").modal("hide");
                    }
                } else {
                    NotyNotification(r.msg, type = 'error');
                }
            },
            error: function (r, textStatus, errorThrown) {
                AjaxErrorHandler(r, textStatus, errorThrown);
            }
        });
    }
}

function PageInit() {
    groupId = window.location.href.split("/").pop();
    if (!$.isNumeric(groupId)) groupId = -1;
    UpdateGroupMember();
}

function JoinPageInit() {
    groupCode = window.location.href.split("/").pop();
    if (groupCode.startsWith("@")) groupCode = groupCode.substr(1);
    $.ajax({
        url: "/api/group/preview",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupCode: groupCode,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == false) {
                NotyNotification(r.msg, type = 'error');
                setTimeout(function () {
                    window.location.href = "/book";
                }, 1000);
                return;
            }

            bookName = r.name;
            $(".title").html(r.name);
            $("#name").html(r.name);
            $("#description").html(marked.parse(r.description));
            $("#owner").html(r.ownerUsername);
            $("#member-count").html(r.memberCount);

            $("#groupCode").html("@" + groupCode + " " + GenCPBtn("@" + groupCode));
            $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode));

            questionList = r.preview;

            for (var i = 0; i < questionList.length; i++)
                AppendTableData("questionList", [marked.parse(questionList[i].question), marked.parse(questionList[i].answer)]);
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function JoinGroup() {
    if (groupCode == undefined) window.location.reload();

    $.ajax({
        url: '/api/group/join',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupCode: groupCode,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Joined ' + bookName + '!');
                setTimeout(function () {
                    window.location.href = "/book/" + r.bookId;
                }, 3000);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}