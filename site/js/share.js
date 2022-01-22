// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var shareList = [];
var page = 1;
var pageLimit = 10;
var orderBy = "name";
var order = "asc";
var search = "";

var bookName = "";
var shareCode = "";

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
                AppendTableData("shareList", [shareList[i].name, shareList[i].shareCode + " " + GenCPBtn(shareList[i].shareCode),
                    GenCPBtn("http://" + window.location.hostname + "/share/import/" + shareList[i].shareCode.substr(1)),
                    shareList[i].importCount, time.toLocaleString(), btns
                ], shareList[i].bookId);
            }
            l = (page - 1) * pageLimit + 1;
            r = l + shareList.length - 1;
            if (shareList.length == 0) {
                AppendTableData("shareList", ["No data available"], undefined, "100%");
                l = 0;
            }

            PaginateTable("shareList", page, total, "ShareListPage");
            SetTableInfo("shareList", "<p style='opacity:80%'>Showing " + l + " - " +
                r + " / " + totalShare + "</p>");

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

function ImportPageInit() {
    shareCode = window.location.href.split("/").pop();
    if (shareCode.startsWith("!")) shareCode = shareCode.substr(1);
    $.ajax({
        url: "/api/share/preview",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            shareCode: shareCode,
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
            $("#sharer").html(r.sharerUsername);
            $("#import-count").html(r.importCount);

            $("#shareCode").html("!" + shareCode + " "+GenCPBtn("!" + shareCode));
            $("#shareLink").html(GenCPBtn("http://" + window.location.hostname + "/share/import/" + shareCode));

            questionList = r.preview;

            for (var i = 0; i < questionList.length; i++)
                AppendTableData("questionList", [marked.parse(questionList[i].question), marked.parse(questionList[i].answer)]);
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function ImportBook() {
    if (shareCode == undefined) window.location.reload();

    $.ajax({
        url: '/api/share/import',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            shareCode: shareCode,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Imported ' + bookName + '!');
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