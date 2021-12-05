// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var groupId = -1;
var bookId = -1;
var bookName = "";
var selected = [];
var member = [];
var isOwner = false;

function UpdateGroupMember() {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');

    table = $("#memberList").DataTable();
    table.clear();
    table.row.add([
        [""],
        ["Loading... <i class='fa fa-spinner fa-spin'></i>"],
        [""],
    ]);
    table.draw();

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
            table.clear();
            bookName = r.name;
            member = r.member;

            isOwner = r.isOwner;

            if (isOwner) {
                $('#memberList').DataTable().column(2).visible(true);
            } else {
                $('#memberList').DataTable().column(2).visible(false);
            }

            $("title").html(bookName + " | My Memo");
            $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="UpdateGroupMember()" id="refresh-btn"><i class="fa fa-refresh"></i></button>');

            $("#groupDescription").html(marked.parse(r.description.replaceAll("\n", "<br>")));

            for (var i = 0; i < r.member.length; i++) {
                btns = '';
                if (isOwner) {
                    if (r.member[i].username.indexOf("(Editor)") != -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-primary btn-sm" type="button" onclick="GroupOperation(2, ' + r.member[i].userId + ')"><i class="fa fa-edit"></i> Undo make editor</button>';
                    } else if (r.member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-primary btn-sm" type="button" onclick="GroupOperation(2, ' + r.member[i].userId + ')"><i class="fa fa-edit"></i> Make editor</button>';
                    }
                    if (r.member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-warning btn-sm" type="button" onclick="GroupOperation(1, ' + r.member[i].userId + ')"><i class="fa fa-ban"></i> Kick</button>';
                    }
                    if (r.member[i].username.indexOf("(Owner)") == -1) {
                        btns += '&nbsp;&nbsp;<button class="btn btn-danger btn-sm" type="button" onclick="TransferOwnershipShow(' + r.member[i].userId + ')"><i class="fa fa-random"></i> Transfer ownership</button>';
                    }
                }
                r.member[i].username = r.member[i].username.replaceAll("(Owner)", '<i class="fa fa-key"></i>');
                r.member[i].username = r.member[i].username.replaceAll("(Editor)", '<i class="fa fa-edit"></i>');
                table.row.add([
                    [r.member[i].username],
                    [r.member[i].progress],
                    [btns]
                ]).node().id = r.member[i].userId;
            }
            table.draw();

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        },
        error: function (r, textStatus, errorThrown) {
            table.row.add([
                [""],
                ["Failed to fetch group member list"],
                [""],
            ]);
            table.draw();

            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });

    selected = [];
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
    groupId = getUrlParameter("groupId");
    UpdateGroupMember();
}