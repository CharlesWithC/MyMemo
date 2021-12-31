// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var shareList = [];
var page = 1;
var pageLimit = 10;
var orderBy = "name";
var order = "asc";
var search = "";

function UpdateShareList() {
    $("#refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');
    $.ajax({
        url: "/api/share",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            operation: "list",
            page: page,
            pageLimit: pageLimit,
            orderBy: orderBy,
            order: order,
            search: search,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            shareList = r.data;
            total = r.total;
            totalShare = r.totalShare;
            $("tbody tr").remove();

            for (var i = 0; i < shareList.length; i++) {
                btns = '<button type="button" class="btn btn-warning btn-sm" onclick="Unshare(\'' + shareList[i].shareCode + '\')"><i class="fa fa-trash"></i></button>';
                var time = new Date(parseInt(shareList[i].timestamp) * 1000);
                AppendTableData("shareList", [shareList[i].name, shareList[i].shareCode, shareList[i].importCount, time.toLocaleString(), btns], shareList[i].bookId);
            }
            l = (page - 1) * pageLimit + 1;
            r = l + shareList.length - 1;
            if (shareList.length == 0) {
                AppendTableData("shareList", ["No data available"], undefined, "100%");
                l = 0;
            }

            SetTableInfo("shareList", "<p style='opacity:80%'>Showing " + l + " - " +
                r + " / " + totalShare);
            PaginateTable("shareList", page, total, "ShareListPage");

            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function ShareListPage(p) {
    page = p;
    UpdateShareList();
}

function Search() {
    search = $("#search-content").val();
    orderBy = "none";
    SortTable(orderBy);
    UpdateShareList();
}

function UserListSort(id) {
    orderBy = id;
    if ($("#sorting_" + id).hasClass("sorting-desc")) {
        order = "desc";
    } else {
        order = "asc";
    }
    UpdateShareList();
}

function UpdatePageLimit(pl) {
    if (pageLimit != pl) {
        page = Math.ceil((page - 1) * pageLimit / pl + 1);
        pageLimit = pl;
        UpdateShareList();
    }
}

function PageInit() {
    UpdateShareList();
}

function Unshare(shareCode) {
    $.ajax({
        url: "/api/share",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            operation: "remove",
            shareCode: shareCode,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification(r.msg, type = 'success');
                UpdateShareList();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function CreateShareShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title"><i class="fa fa-share-alt"></i> Share Book
                    </h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Select a book to share: </p>
                    <select name="bookId" id="book" class="form-select">
                    </select>
                    <p>An unique share code will be generated.</p>
                    <p><span id="share-msg"></span></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button id="share-btn" type="button" class="btn btn-primary" data-dismiss="modal"
                        onclick="Share();">Share</button>
                </div>
            </div>
        </div>
    </div>`);
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
            for (var i = 1; i < r.length; i++)
                $("#book").append("<option value=" + r[i].bookId + ">" + r[i].name +
                    "</option>");
        }
    });
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    setTimeout(function () {
        selected = [];
    }, 100);
}

function Share() {
    bookId = $('select[name="bookId"]').val();
    $.ajax({
        url: "/api/share",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            operation: "create",
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification(r.msg, type = 'success');
                $("#share-msg").html("Book share created! Share code: " + r.shareCode);
                UpdateShareList();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}