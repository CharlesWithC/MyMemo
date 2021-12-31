// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var groupId = -1;
var bookId = -1;
var bookName = "";
var selected = [];
var member = [];
var isOwner = false;

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

            $("title").html(bookName + " | My Memo");
            $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="UpdateGroupMember()" id="refresh-btn"><i class="fa fa-sync"></i></button>');

            $("#groupDescription").html(marked.parse(r.description.replaceAll("\n", "<br>")));

            for (var i = 0; i < member.length; i++) {
                btns = '';
                if (isOwner) {
                    if (member[i].username.indexOf("(Editor)") != -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-primary btn-sm" type="button" onclick="GroupOperation(2, ' + member[i].userId + ')"><i class="fa fa-edit"></i> Undo make editor</button>';
                    } else if (member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-primary btn-sm" type="button" onclick="GroupOperation(2, ' + member[i].userId + ')"><i class="fa fa-edit"></i> Make editor</button>';
                    }
                    if (member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-warning btn-sm" type="button" onclick="GroupOperation(1, ' + member[i].userId + ')"><i class="fa fa-ban"></i> Kick</button>';
                    }
                    if (member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-danger btn-sm" type="button" onclick="TransferOwnershipShow(' + member[i].userId + ')"><i class="fa fa-random"></i> Transfer ownership</button>';
                    }
                }
                member[i].username = member[i].username.replaceAll("(Owner)", '<i class="fa fa-crown"></i>');
                member[i].username = member[i].username.replaceAll("(Editor)", '<i class="fa fa-edit"></i>');
                AppendTableData("memberList", [member[i].username, member[i].progress, btns], member[i].userId);
            }
            l = (page - 1) * pageLimit + 1;
            r = l + member.length - 1;
            if (member.length == 0) {
                AppendTableData("memberList", ["No data available"], undefined, "100%");
                l = 0;
            }

            SetTableInfo("memberList", "<p style='opacity:80%'>Showing " + l + " - " +
                r + " / " + totalMember);
            PaginateTable("memberList", page, total, "MemberListPage");

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

    selected = [];
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
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-random"></i> Transfer Ownership
                    </h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to transfer ownership? Make sure you trust that user!</p>
                    <p>You cannot undo this operation unless the new owner transferred ownership back.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button id="transfer-ownership-btn" type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="GroupOperation(3, ` + uid + `)">Transfer</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    setTimeout(function () {
        selected = [];
    }, 100);
}

function GroupOperation(operation, uid = -1) {
    if (uid != -1) {
        list = [uid];
    } else {
        list = selected;
    }
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
    groupId = getUrlParameter("groupId");
    UpdateGroupMember();
}