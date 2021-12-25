// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var bookId = -1;
var bookName = "";
var groupId = -1;
var groupCode = "";
var isGroupOwner = false;
var isGroupEditor = false;
var discoveryId = -1;
var groupDiscoveryId = -1;
var bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
setInterval(function () {
    bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
}, 5000); // this will be updated by general.js
var selected = [];

var page = 1;
var pageLimit = 10;
var orderBy = "question";
var order = "asc";
var search = "";
var data = [];
var showDB = false;
var total = 0;
var totalQ = 0;

function GenOPBtn(questionId) {
    btns = '<button type="button" class="btn btn-primary btn-sm" onclick="ShowStatistics(' + questionId + ')"><i class="fa fa-chart-bar"></i></button>';
    btns += '<button type="button" class="btn btn-primary btn-sm" onclick="EditQuestionShow(' + questionId + ')"><i class="fa fa-edit"></i></button>';
    if ($("#removeFromDB").is(":checked") || bookId == 0) {
        btns += '<button type="button" class="btn btn-danger btn-sm remove-question-btn" onclick="RemoveFromBook(' + questionId + ')"><i class="fa fa-trash"></i></button>';
    } else {
        btns += '<button type="button" class="btn btn-warning btn-sm remove-question-btn" onclick="RemoveFromBook(' + questionId + ')"><i class="fa fa-trash"></i></button>';
    }
    return btns;
}

function UpdateStatusColor() {
    for (var i = 0; i < data.length; i++) {
        if (data[i].status == 2) {
            $("#" + data[i].questionId).attr("style", "color: red");
        } else if (data[i].status == 3) {
            if (localStorage.getItem("settings-theme") == "dark") {
                $("#" + data[i].questionId).attr("style", "color: lightgray");
            } else {
                $("#" + data[i].questionId).attr("style", "color: gray");
            }
        }
    }
}

function UpdateTable() {
    $("tbody tr").remove();
    statusIntToStr = ["", "Default", "Tagged", "Deleted"];
    for (var i = 0; i < data.length; i++) {
        AppendTableData("questionList", [
            data[i].question.replaceAll("\n", "<br>"),
            data[i].answer.replaceAll("\n", "<br>"),
            statusIntToStr[data[i].status],
            id = GenOPBtn(data[i].questionId)
        ], data[i].questionId);
        if (selected.indexOf(data[i].questionId) != -1) {
            $("#" + data[i].questionId).addClass("table-active");
        }
    }
    l = (page - 1) * pageLimit + 1;
    r = l + data.length - 1;
    if (data.length == 0) {
        l = 0;
        AppendTableData("questionList", ["No data available"], undefined, "100%");
    }
    if (showDB) {
        $("#questionList tr > *:nth-child(4)").hide();
    }
    content = "<p style='opacity:80%'>Showing " + l + " - " + r + " / " + totalQ + " | ";
    content += "<span style='cursor:pointer' onclick='SelectAll()'>Select All</span> | ";
    content += "<span style='cursor:pointer' onclick='DeselectAll()'>Deselect All</span></p>";
    SetTableInfo("questionList", content);
    PaginateTable("questionList", page, total, "BookPage");
    UpdateStatusColor();
}

function UpdateQuestionList() {
    $("#refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');
    bid = bookId;
    if (showDB) {
        bid = 0;
    }
    pageLimit = $('select[name="questionList_range_select"]').val();
    // Update list
    $.ajax({
        url: "/api/book/questionList",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: bid,
            page: page,
            pageLimit: pageLimit,
            orderBy: orderBy,
            order: order,
            search: search,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
            if (!r.success) {
                NotyNotification(r.msg, 'warning', 5000);
                $("#questionList tbody tr").remove();
                AppendTableData("questionList", [r.msg], undefined, "100%");
                SetTableInfo("questionList", "Forbidden");
                PaginateTable("questionList", 1, 1, "BookPage");
                return;
            }
            data = r.data;
            total = r.total;
            UpdateTable();
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BookPage(p) {
    page = p;
    UpdateQuestionList();
}

function Search() {
    search = $("#search-content").val();
    UpdateQuestionList();
}

function OpenBook(bid = null) {
    $("tbody tr").remove();
    if (bid != null) {
        bookId = bid;
    }

    if (bookId == 0) {
        $("#removeFromDB").prop("checked", true);
        $("#removeFromDB").attr("disabled", "disabled");
        $(".not-for-all-questions").hide();
    } else {
        $("#removeFromDB").prop("checked", false);
        $("#removeFromDB").removeAttr("disabled");
        $(".not-for-all-questions").show();
    }
    $(".group").hide();

    page = 1;
    ShowManage();
    UpdateQuestionList();

    window.history.pushState("My Memo", "My Memo", "/book?bookId=" + bookId);

    found = false;

    for (var i = 0; i < bookList.length; i++) {
        if (bookList[i].bookId == bookId) {
            found = true;
            $(".book-list-content-div").hide();
            $(".book-data-div").fadeIn();

            totalQ = bookList[i].total;
            bookName = bookList[i].name;
            btns = '<button type="button" class="btn btn-outline-secondary" onclick="UpdateQuestionList()" id="refresh-btn"><i class="fa fa-sync"></i></button>';
            $(".title").html(bookName + '&nbsp;&nbsp;' + btns);
            $("title").html(bookName + " | My Memo");
            groupId = bookList[i].groupId;
            groupCode = bookList[i].groupCode;
            $("#groupCode").html(groupCode);
            isGroupOwner = bookList[i].isGroupOwner;
            isGroupEditor = bookList[i].isGroupEditor;
            $(".group").show();
            if (bookId == 0) {
                $(".not-for-all-questions").hide();
            } else {
                $(".not-for-all-questions").show();
            }
            if (groupId == -1) {
                $(".only-group-owner").hide();
                $(".only-group-exist").hide();
                $(".only-group-inexist").show();
                $(".only-group-owner-if-group-exist").show();
                $(".only-group-editor-if-group-exist").show();
            } else {
                $(".only-group-exist").show();
                $(".only-group-inexist").hide();

                if (isGroupOwner) {
                    $(".only-group-owner").show();
                    $(".only-group-owner-if-group-exist").show();
                } else {
                    $(".only-group-owner").hide();
                    $(".only-group-owner-if-group-exist").hide();
                }
                if (isGroupEditor) {
                    $(".only-group-editor-if-group-exist").show();
                } else if (!isGroupEditor && !isGroupOwner) {
                    $(".only-group-editor-if-group-exist").hide();
                }
            }
            discoveryId = bookList[i].discoveryId;
            if (discoveryId == -1) {
                $(".not-published-to-discovery").show();
                $(".published-to-discovery").hide();
            } else if (discoveryId != -1) {
                $(".not-published-to-discovery").hide();
                $(".published-to-discovery").show();
                $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + discoveryId + "'");
            }
            if (groupId != -1) {
                groupDiscoveryId = bookList[i].groupDiscoveryId;
                if (groupDiscoveryId == -1 && groupCode != "") {
                    $(".group-not-published-to-discovery").show();
                    $(".group-published-to-discovery").hide();
                } else if (groupDiscoveryId != -1) {
                    $(".group-not-published-to-discovery").hide();
                    $(".group-published-to-discovery").show();
                    $("#group-go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + groupDiscoveryId + "'");
                }
            } else {
                $(".group-not-published-to-discovery").hide();
                $(".group-published-to-discovery").hide();
            }

            $(".group-anonymous-btn").removeClass("btn-primary btn-secondary");
            $(".group-anonymous-btn").addClass("btn-secondary");
            if (bookList[i].anonymous == 0) {
                $("#group-anonymous-0").removeClass("btn-secondary");
                $("#group-anonymous-0").addClass("btn-primary");
            } else if (bookList[i].anonymous == 1) {
                $("#group-anonymous-1").removeClass("btn-secondary");
                $("#group-anonymous-1").addClass("btn-primary");
            } else if (bookList[i].anonymous == 2) {
                $("#group-anonymous-2").removeClass("btn-secondary");
                $("#group-anonymous-2").addClass("btn-primary");
            }
        }
    }
    if (!found) {
        UpdateBookContentDisplay();
    }
}

function BookListSort(id) {
    orderBy = id;
    if ($("#sorting_" + id).hasClass("sorting-desc")) {
        order = "desc";
    } else {
        order = "asc";
    }
    UpdateQuestionList();
}

function UpdatePageLimit(pl) {
    if (pageLimit != pl) {
        page = Math.ceil((page - 1) * pageLimit / pl + 1);
        pageLimit = pl;
        UpdateQuestionList();
    }
}

function PageInit() {
    InitTable("questionList", [10, 25, 50, 100], 10, "UpdatePageLimit", "Search");
    InitSorting("questionList", ["question", "answer", "status"], ["asc", undefined, undefined], "BookListSort");
    bookId = getUrlParameter("bookId");

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
            bookList = r;
            if (bookId != -1)
                OpenBook();
            UpdateBookContentDisplay();
            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        }
    });

    if (bookId == 0) {
        $(".not-for-all-questions").hide();
    } else {
        $(".not-for-all-questions").show();
    }
    $(".group").hide();
}

function ShowStatistics(wid) {
    question = "";
    answer = "";
    for (var i = 0; i < data.length; i++) {
        if (data[i].questionId == wid) {
            question = data[i].question;
            answer = data[i].answer;
            break;
        }
    }

    $.ajax({
        url: '/api/question/stat',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questionId: wid,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            statistics = r.msg.replaceAll("\n", "<br>");

            $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
                aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modal">Statistics of ` + question + `</h5>
                            <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                                onclick="$('#modal').modal('hide')">
                                <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p>` + statistics + `</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal"
                                onclick="$('#modal').modal('hide')">Close</button>
                        </div>
                    </div>
                </div>
            </div>`);
            $("#modal").modal("show");
            $('#modal').on('hidden.bs.modal', function () {
                $("#modal").remove();
            });
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

var editQuestionId = -1;

function EditQuestionShow(wid) {
    editQuestionId = wid;
    question = "";
    answer = "";
    for (var i = 0; i < data.length; i++) {
        if (data[i].questionId == wid) {
            question = data[i].question;
            answer = data[i].answer;
            break;
        }
    }
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalLabel">Edit Question</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <form>
                        <div class="form-group">
                            <label for="edit-question" class="col-form-label">Question:</label>
                            <textarea class="form-control" id="edit-question"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="edit-answer" class="col-form-label">Answer:</label>
                            <textarea class="form-control" id="edit-answer"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="edit-question-btn" type="button" class="btn btn-primary"
                        onclick="EditQuestion()">Edit</button>
                </div>
            </div>
        </div>
    </div>`)
    $("#edit-question").val(question);
    $("#edit-answer").val(answer);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $("#edit-question,#edit-answer").keypress(function (e) {
        if (e.which == 13 && e.ctrlKey) {
            EditQuestion();
        }
    });
}

function EditQuestionFromBtn() {
    if (selected.length != 1) {
        NotyNotification("Make sure you selected one question!", type = 'warning');
        return;
    }

    EditQuestionShow(selected[0]);
}

function EditQuestion() {
    question = $("#edit-question").val();
    answer = $("#edit-answer").val();
    $.ajax({
        url: '/api/question/edit',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questionId: editQuestionId,
            question: question,
            answer: answer,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            for (var i = 0; i < data.length; i++) {
                if (data[i].questionId == wid) {
                    data[i].question = question;
                    data[i].answer = answer;
                    break;
                }
            }
            UpdateTable();

            if (r.success == true) {
                NotyNotification(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }

            $("#modal").modal('hide');
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BookUpdateStatus(updateTo) {
    $.ajax({
        url: '/api/question/status/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify(selected),
            status: updateTo,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            for (var i = 0; i < data.length; i++) {
                for (var j = 0; j < selected.length; j++) {
                    if (data[i].questionId == selected[j]) {
                        data[i].status = updateTo;
                        break;
                    }
                }
            }
            UpdateTable();
            UpdateStatusColor();
            NotyNotification("Success! Question status updated!");
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function ShowQuestionDatabase() {
    $("#questionList tr > *:nth-child(4)").hide();
    $(".manage").hide();
    $("#addExistingQuestion").show();
    $(".book-name").html("All questions");
    selected = [];
    showDB = true;
    UpdateQuestionList();
}

function ShowManage() {
    $("#addExistingQuestion").hide();
    $(".manage").show();
    $("#questionList tr > *:nth-child(4)").show();
    showDB = false;
}

function AddExistingQuestion() {
    $.ajax({
        url: '/api/book/addQuestion',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify(selected),
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Added ' + selected.length + ' question(s)!');

                ShowManage();
                UpdateQuestionList();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function AddQuestionShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalLabel">Add a new question to ` + bookName + `</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <form>
                        <div class="form-group">
                            <label for="edit-question" class="col-form-label">Question:</label>
                            <textarea class="form-control" id="edit-question"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="edit-answer" class="col-form-label">Answer:</label>
                            <textarea class="form-control" id="edit-answer"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="edit-question-btn" type="button" class="btn btn-primary"
                        onclick="AddQuestion()">Add</button>
                </div>
            </div>
        </div>
    </div>`)
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $("#edit-question,#edit-answer").keypress(function (e) {
        if (e.which == 13 && e.ctrlKey) {
            AddQuestion();
        }
    });
}

function AddQuestion() {
    question = $("#edit-question").val();
    answer = $("#edit-answer").val();
    $.ajax({
        url: '/api/question/add',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            question: question,
            answer: answer,
            addToBook: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Added a new question!');

                UpdateQuestionList();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function RemoveFromBook(wid = -1) {
    questions = [];
    if (wid == -1) {
        questions = selected;
    } else {
        questions = [wid];
    }
    if ($("#removeFromDB").is(":checked") || bookId == 0) {
        RemoveQuestionShow();
        return;
    }
    $.ajax({
        url: '/api/book/deleteQuestion',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify(questions),
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Removed ' + questions.length + ' question(s) from this book!');

                UpdateQuestionList();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function RemoveQuestionShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-trash"></i> Remove Question from
                        Database
                    </h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to remove all select questions from database? This will remove them from all
                        books.
                    </p>
                    <p>This operation cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="RemoveQuestion()">Remove</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
}

function RemoveQuestion() {
    $.ajax({
        url: '/api/question/delete',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify(selected),
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Removed ' + selected.length + ' question(s) from database!');

                $("#modal").modal('hide');

                UpdateQuestionList();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BookClone() {
    $.ajax({
        url: '/api/book/clone',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            fromBook: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Book cloned!');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BookRenameShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalLabel">Rename Book</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <form>
                        <div class="input-group mb-3 center">
                            <span class="input-group-text" id="basic-addon1">Name</span>
                            <input type="text" class="form-control" id="book-rename" aria-describedby="basic-addon1">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button type="button" class="btn btn-primary" onclick="BookRename()">Rename</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#book-rename").val(bookName);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $("#book-rename").keypress(function (e) {
        if (e.which == 13 || e.which == 13 && e.ctrlKey) {
            BookRename();
        }
    });
}

function BookRename() {
    newName = $("#book-rename").val();
    if (newName == "") {
        NotyNotification('Please enter a new name!', type = 'warning');
        return;
    }

    $.ajax({
        url: '/api/book/rename',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: bookId,
            name: newName,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                bookName = newName;
                $(".book-name").html(bookName);
                btns = '<button type="button" class="btn btn-outline-secondary" onclick="UpdateQuestionList()" id="refresh-btn"><i class="fa fa-sync"></i></button>';
                $(".title").html(bookName + '&nbsp;&nbsp;' + btns);
                $("title").html(bookName + " | My Memo");
                $("title").html(bookName + " | My Memo");
                NotyNotification('Success! Book renamed!');
                $("#modal").modal("hide");
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BookDeleteShow() {
    $("#content").after(`
    <div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-trash"></i> Delete Book</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to delete this book? The questions will be preserved in the question database
                        but
                        they will no longer belong to this book.</p>
                    <p>This operation cannot be undone.</p>
                    <br>
                    <p>Type the name of the book <b>` + bookName + `</b> to continue:</p>
                    <form>
                        <div class="input-group mb-3 center">
                            <input type="text" class="form-control" id="book-delete" aria-describedby="basic-addon1">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="BookDelete()">Delete</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
}

function BookDelete() {
    if ($("#book-delete").val() != bookName) {
        NotyNotification('Please type the name of the book correctly to continue!', type = 'warning');
        return;
    }
    $.ajax({
        url: '/api/book/delete',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: bookId,
            removeAll: $("#removeAllFromDB").is(":checked"),
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Book deleted!');
                setTimeout(function () {
                    $(".book-data-div").hide();
                    $(".book-list-content-div").fadeIn();
                    window.history.pushState("My Memo", "My Memo", "/book");
                    $(".title").html(`Book&nbsp;&nbsp;<button type="button" id="refresh-btn" class="btn btn-outline-secondary"
                    onclick="UpdateBookContentList()"><i class="fa fa-sync"></i></button>`);
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

function PublishToDiscoveryShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modallLabel"><i class="fa fa-paper-plane"></i>
                        Publish
                        To Discovery</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>You are about to publish the book to Discovery.</p>
                    <p>This will make it able to be found by any people.</p>
                    <p>All your updates made within this book will be synced to Discovery. (But people already
                        imported it will not get the sync, use Group function to do that)</p>
                    <br>
                    <p>Please enter title and description below. Make them beautiful and others may get engaged.</p>
                    <form>
                        <div class="input-group mb-3">
                            <span class="input-group-text" id="basic-addon1">Title</span>
                            <input type="text" class="form-control" id="discovery-title" aria-describedby="basic-addon1">
                        </div>
                        <div class="form-group">
                            <label for="discovery-description" class="col-form-label">Description:</label>
                            <script>var descriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
                            <textarea class="form-control" id="discovery-description"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="publish-to-discovery-btn" type="button" class="btn btn-primary"
                        onclick="PublishToDiscovery()">Publish <i class="fa fa-paper-plane"></i></button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $(".editor-toolbar").css("background-color", "white");
    $(".editor-toolbar").css("opacity", "1");
    $(".cursor").remove();
    $("#discovery-title,#discovery-description").keypress(function (e) {
        if (e.which == 13 && e.ctrlKey) {
            PublishToDiscovery();
        }
    });
}

function PublishToDiscovery() {
    title = $("#discovery-title").val();
    description = descriptionMDE.value();

    $.ajax({
        url: '/api/discovery/publish',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: bookId,
            title: title,
            description: description,
            type: 1,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                discoveryId = r.discoveryId;
                $(".not-published-to-discovery").hide();
                $(".published-to-discovery").show();
                $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + discoveryId + "'");

                NotyNotification(r.msg);

                $('#modal').modal('hide');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function UnpublishDiscoveryShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-trash"></i> Unpublish From Discovery
                    </h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden="true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to unpublish the book from Discovery?</p>
                    <p>You will lose all the views and likes of your post.</p>
                    <p>This operation cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="UnpublishDiscovery()">Unpublish</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
}

function GroupPublishToDiscoveryShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalLabel"><i class="fa fa-paper-plane"></i>
                        Publish To Discovery</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>You are about to publish the group to Discovery.</p>
                    <p>This will make it able to be found by any people.</p>
                    <p>Any people will be able to find it and join your group.</p>
                    <p>You can make your group a private group if you want to temporarily make it invisible on
                        Discovery.</p>
                    <br>
                    <p>Please enter title and description below. Make them beautiful and others may get engaged.</p>
                    <form>
                        <div class="input-group mb-3">
                            <span class="input-group-text" id="basic-addon1">Title</span>
                            <input type="text" class="form-control" id="group-discovery-title" aria-describedby="basic-addon1">
                        </div>
                        <div class="form-group">
                            <label for="group-discovery-description" class="col-form-label">Description:</label>
                            <script>var descriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
                            <textarea class="form-control" id="group-discovery-description"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="publish-to-discovery-btn" type="button" class="btn btn-primary"
                        onclick="GroupPublishToDiscovery()">Publish <i class="fa fa-paper-plane"></i></button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $(".editor-toolbar").css("background-color", "white");
    $(".editor-toolbar").css("opacity", "1");
    $(".cursor").remove();
    $("#group-discovery-title,#group-discovery-description").keypress(function (e) {
        if (e.which == 13 && e.ctrlKey) {
            GroupPublishToDiscovery();
        }
    });
}

function GroupPublishToDiscovery() {
    title = $("#group-discovery-title").val();
    description = descriptionMDE.value();

    $.ajax({
        url: '/api/discovery/publish',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: groupId,
            title: title,
            description: description,
            type: 2,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                discoveryId = r.discoveryId;
                $(".group-not-published-to-discovery").hide();
                $(".group-published-to-discovery").show();
                $("#group-go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + discoveryId + "'");

                NotyNotification(r.msg, type = 'success', timeout = 30000);

                $('#modal').modal('hide');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupUnpublishDiscoveryShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog"
        aria-labelledby="modalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-trash"></i> Unpublish From Discovery
                    </h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to unpublish the group from Discovery?</p>
                    <p>You will lose all the views and likes of your post.</p>
                    <p>This operation cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="GroupUnpublishDiscovery()">Unpublish</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
}

function UnpublishDiscovery() {
    $.ajax({
        url: '/api/discovery/unpublish',
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
                discoveryId = -1;
                $(".not-published-to-discovery").show();
                $(".published-to-discovery").hide();
                $("#go-to-discovery-btn").attr("onclick", "");

                NotyNotification(r.msg);
                $('#modal').modal('hide');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupUnpublishDiscovery() {
    $.ajax({
        url: '/api/discovery/unpublish',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: groupDiscoveryId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                groupDiscoveryId = -1;
                $(".group-not-published-to-discovery").show();
                $(".group-published-to-discovery").hide();
                $("#go-to-discovery-btn").attr("onclick", "");

                NotyNotification(r.msg);
                $('#modal').modal('hide');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function CreateGroupShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalLabel">Create Group</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Your group need a name and a description so others can know what it do. Please enter them
                        below!
                    </p>
                    <form>
                        <div class="input-group mb-3">
                            <span class="input-group-text" id="basic-addon1">Name</span>
                            <input type="text" class="form-control" id="group-name" aria-describedby="basic-addon1">
                        </div>
                        <div class="form-group">
                            <label for="group-description" class="col-form-label">Description:</label>
                            <script>var groupDescriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
                            <textarea class="form-control" id="group-description"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="create-group-btn" type="button" class="btn btn-primary"
                        onclick="CreateGroup()">Create</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $(".editor-toolbar").css("background-color", "white");
    $(".editor-toolbar").css("opacity", "1");
    $(".cursor").remove();
    $("#group-name,#group-description").keypress(function (e) {
        if (e.which == 13 && e.ctrlKey) {
            CreateGroup();
        }
    });
}

function CreateGroup() {
    gname = $("#group-name").val();
    gdescription = groupDescriptionMDE.value();
    if (gname == "" || gdescription == "") {
        NotyNotification('Group name and description must be filled', type = 'warning');
        return;
    }
    $.ajax({
        url: '/api/group',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: bookId,
            name: gname,
            description: gdescription,
            operation: "create",
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < bookList.length; i++) {
                    if (bookList[i].bookId == bookId) {
                        bookList[i].groupId = r.groupId;
                        bookList[i].groupCode = r.groupCode;
                        bookList[i].isGroupOwner = r.isGroupOwner;
                        groupId = r.groupId;
                        groupCode = r.groupCode;
                        isGroupOwner = r.isGroupOwner;

                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();

                        break;
                    }
                }
                NotyNotification(r.msg, type = 'info', timeout = 30000);
                $("#modal").modal("hide");
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupMember() {
    window.location.href = "/group?groupId=" + groupId;
}

function QuitGroupShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-arrow-right-from-bracket"></i> Quit Group</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to quit the group? Your progress will no longer be shared with other members and
                        the
                        book sync will stop.</p>
                    <p>You will not be able to join the group again unless you have the invite code.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="QuitGroup()">Quit</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
}

function QuitGroup() {
    $.ajax({
        url: '/api/group/quit',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupId: groupId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < bookList.length; i++) {
                    if (bookList[i].bookId == bookId) {
                        bookList[i].groupId = -1;
                        bookList[i].groupCode = "";
                        bookList[i].isGroupOwner = false;
                        groupId = -1;
                        groupCode = "";
                        isGroupOwner = false;

                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();

                        localStorage.setItem("groupId", "-1");
                        break;
                    }
                }
                $("#modal").modal('hide');
                NotyNotification(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupInfoUpdateShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modal"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modal">Update Group Information</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <form>
                        <div class="input-group mb-3">
                            <span class="input-group-text" id="basic-addon1">Name</span>
                            <input type="text" class="form-control" id="group-name" aria-describedby="basic-addon1">
                        </div>
                        <div class="form-group">
                            <label for="group-description" class="col-form-label">Description:</label>
                            <script>var groupDescriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
                            <textarea class="form-control" id="group-description"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="create-group-btn" type="button" class="btn btn-primary"
                        onclick="GroupInfoUpdate()">Update</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $(".editor-toolbar").css("background-color", "white");
    $(".editor-toolbar").css("opacity", "1");
    $(".cursor").remove();
}

function GroupAnonymousSwitch(anonymous) {
    $(".group-anonymous-btn").removeClass("btn-primary btn-secondary");
    $(".group-anonymous-btn").addClass("btn-secondary");
    if (anonymous == 0) {
        $("#group-anonymous-0").removeClass("btn-secondary");
        $("#group-anonymous-0").addClass("btn-primary");
    } else if (anonymous == 1) {
        $("#group-anonymous-1").removeClass("btn-secondary");
        $("#group-anonymous-1").addClass("btn-primary");
    } else if (anonymous == 2) {
        $("#group-anonymous-2").removeClass("btn-secondary");
        $("#group-anonymous-2").addClass("btn-primary");
    }

    $.ajax({
        url: '/api/group/manage',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupId: groupId,
            anonymous: anonymous,
            operation: "anonymous",
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < bookList.length; i++) {
                    if (bookList[i].bookId == bookId) {
                        bookList[i].anonymous = r.anonymous;
                        break;
                    }
                }
                $(".group-anonymous-btn").removeClass("btn-primary btn-secondary");
                $(".group-anonymous-btn").addClass("btn-secondary");
                if (r.anonymous == 0) {
                    $("#group-anonymous-0").removeClass("btn-secondary");
                    $("#group-anonymous-0").addClass("btn-primary");
                } else if (r.anonymous == 1) {
                    $("#group-anonymous-1").removeClass("btn-secondary");
                    $("#group-anonymous-1").addClass("btn-primary");
                } else if (r.anonymous == 2) {
                    $("#group-anonymous-2").removeClass("btn-secondary");
                    $("#group-anonymous-2").addClass("btn-primary");
                }

                NotyNotification(r.msg);

            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupInfoUpdate() {
    gname = $("#group-name").val();
    gdescription = groupDescriptionMDE.value();
    if (gname == "" || gdescription == "") {
        NotyNotification('Group name and description must be filled', type = 'warning');
        return;
    }
    $.ajax({
        url: '/api/group/manage',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupId: groupId,
            name: gname,
            description: gdescription,
            operation: "updateInfo",
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < bookList.length; i++) {
                    if (bookList[i].bookId == bookId) {
                        bookList[i].name = gname;
                        bookName = gname;

                        $(".book-name").html(bookName);
                        btns = '<button type="button" class="btn btn-outline-secondary" onclick="UpdateQuestionList()" id="refresh-btn"><i class="fa fa-sync"></i></button>';
                        $(".title").html(bookName + '&nbsp;&nbsp;' + btns);
                        $("title").html(bookName + " | My Memo");
                        $("title").html(bookName + " | My Memo");
                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();

                        localStorage.setItem("groupId", "-1");
                        break;
                    }
                }
                $("#modal").modal('hide');
                NotyNotification(r.msg);

            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupCodeUpdate(operation) {
    $.ajax({
        url: '/api/group/code/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupId: groupId,
            operation: operation,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < bookList.length; i++) {
                    if (bookList[i].bookId == bookId) {
                        bookList[i].groupCode = r.groupCode;
                        groupCode = r.groupCode;

                        $("#groupCode").html(groupCode);

                        break;
                    }
                }
                NotyNotification(r.msg);

            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function GroupDismissShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-times"></i> Dismiss Group</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to dismiss the group? The group book sync will stop and it will be deleted
                        permanently.</p>
                    <p>All members will quit automatically and they will not be able to see each other's progress.
                    </p>
                    <p>This operation cannot be undone.</p>
                    <p>*If you just want to make your group private or revoke the code, there are options just above
                        the
                        dismiss button.</p>
                    <br>
                    <p>Type the name of the group <b>` + bookName + `</b> to continue:</p>
                    <form>
                        <div class="input-group mb-3 center">
                            <input type="text" class="form-control" id="group-delete" aria-describedby="basic-addon1">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="GroupDismiss()">Dismiss</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $("#group-delete").keypress(function (e) {
        if (e.which == 13 || e.which == 13 && e.ctrlKey) {
            GroupDismiss();
        }
    });
}

function GroupDismiss() {
    if ($("#group-delete").val() != bookName) {
        NotyNotification('Type the name of the group correctly to continue!', type = 'warning');
        return;
    }
    $.ajax({
        url: '/api/group',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            groupId: groupId,
            operation: "dismiss",
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < bookList.length; i++) {
                    if (bookList[i].bookId == bookId) {
                        bookList[i].groupId = -1;
                        bookList[i].groupCode = "";
                        bookList[i].isGroupOwner = false;
                        groupId = -1;
                        groupCode = "";
                        isGroupOwner = false;

                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").hide();
                        $(".only-group-inexist").show();
                        $(".only-group-owner").hide();

                        break;
                    }
                }
                NotyNotification(r.msg);
                $("#modal").modal("hide");
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function SelectAll() {
    $("#questionList tbody tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && selected.indexOf(wid) == -1 && !$(this).hasClass("table-active")) { // check for NaN
            selected.push(wid);
        }

        $(this).addClass("table-active");
    });
}

function DeselectAll() {
    $("#questionList tbody tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && $(this).hasClass("table-active")) { // check for NaN
            idx = selected.indexOf(wid);
            if (idx > -1) {
                selected.splice(idx, 1);
            }
        }

        $(this).removeClass("table-active");
    });
}

function UpdateBookContentDisplay() {
    $(".book-list-content div").remove();
    if (bookList.length == 1) {
        $(".book-list-content").append("<div><p>My Book</p></div>");
    } else {
        $(".book-list-content").append("<div><p>My Books</p></div>");
    }
    for (var i = 0; i < bookList.length; i++) {
        book = bookList[i];
        wcnt = "";
        if (book.bookId == 0) {
            wcnt = book.total + ' questions';
        } else {
            wcnt = book.progress + ' memorized / ' + book.total + ' questions';
        }
        bname = book.name;
        if (book.groupId != -1) {
            bname = "[Group] " + bname;
        }

        $(".book-list-content").append('<div class="rect" style="padding:1em" onclick="OpenBook(' + book.bookId + ')">\
        <p class="rect-title">' + bname + '</p>\
        <p class="rect-content">&nbsp;&nbsp;' + wcnt + '</p>\
        </div>');
    }
}

function SelectBookContent(bookId) {
    localStorage.setItem("memo-book-id", bookId);
    UpdateBookContentDisplay();
}

function SelectBook(bookId) {
    localStorage.setItem("memo-book-id", bookId);
    UpdateBookContentDisplay();

    btns = '<button type="button" class="btn btn-outline-secondary" onclick="UpdateQuestionList()" id="refresh-btn"><i class="fa fa-sync"></i></button>';
    $(".title").html(bookName + '&nbsp;&nbsp;' + btns);
    $("title").html(bookName + " | My Memo");
}

function UpdateBookContentList() {
    $("#refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');
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
            bookList = r;
            UpdateBookContentDisplay();
            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        }
    });
}

function CreateBook(element) {
    bookName = $(element).val();

    if (bookName == "") {
        NotyNotification('Please enter the name of the book!', type = 'warning');
        return;
    }

    $.ajax({
        url: '/api/book/create',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            name: bookName,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                UpdateBookContentList();
                UpdateBookContentDisplay();
                NotyNotification('Success! Book created!');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BookChart() {
    $.ajax({
        url: '/api/book/chart',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
                aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modalLabel"><i class="fa fa-chart-bar"></i> Book Statistics</h5>
                            <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                                onclick="$('#modal').modal('hide')">
                                <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div id="charts" style="border-radius:0.5em">
                                <div class="chart" id="chart1"></div>
                                <div class="chart" id="chart2"></div>
                                <div class="chart" id="chart3" style="width:49%;display:inline-block;"></div>
                                <div class="chart" id="chart4" style="width:49%;display:inline-block;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`);
            x = ['x'];
            Memorized = ['Memorized'];
            Forgotten = ['Forgotten'];
            for (var i = r.challenge_history.length - 1; i >= 0; i--) {
                Memorized.push(r.challenge_history[i].memorized);
                Forgotten.push(r.challenge_history[i].forgotten);
                var date = new Date(Date.now() - 86400 * 3 * i * 1000);
                x.push((date.getMonth() + 1) + "-" + date.getDate());
            }
            chart1 = c3.generate({
                bindto: "#chart1",
                data: {
                    x: 'x',
                    columns: [
                        ['x'],
                        ['Memorized'],
                        ['Forgotten']
                    ],
                    groups: [
                        ['Memorized', 'Forgotten']
                    ],
                    colors: {
                        Memorized: '#55ff55',
                        Forgotten: '#ff5555'
                    },
                    types: {
                        Memorized: 'bar',
                        Forgotten: 'bar'
                    }
                },
                bar: {
                    width: {
                        ratio: 0.8
                    }
                },
                axis: {
                    x: {
                        type: 'category',
                        tick: {
                            rotate: -45,
                            multiline: false
                        },
                        height: 50
                    },
                    y: {
                        label: {
                            text: '3-Day Challenge Record',
                            position: 'outer-middle'
                        }
                    }
                },
                zoom: {
                    enabled: true
                }
            });
            setTimeout(function () {
                chart1.load({
                    columns: [x, Memorized, Forgotten]
                });
                setTimeout(function () {
                    chart1.flush();
                }, 500);
            }, 500);

            Total = ['Total'];
            for (var i = r.total_memorized_history.length - 1; i >= 0; i--) {
                Total.push(r.total_memorized_history[i].total);
            }
            chart2 = c3.generate({
                bindto: "#chart2",
                data: {
                    x: 'x',
                    columns: [
                        ['x'],
                        ['Total']
                    ],
                    colors: {
                        Total: '#5555ff',
                    },
                    types: {
                        Total: 'area',
                    }
                },
                axis: {
                    x: {
                        type: 'category',
                        tick: {
                            rotate: -45,
                            multiline: false
                        },
                        height: 50
                    },
                    y: {
                        label: {
                            text: '3-Day Total Memorized',
                            position: 'outer-middle'
                        }
                    }
                },
                zoom: {
                    enabled: true
                }
            });
            setTimeout(function () {
                chart2.load({
                    columns: [x, Total]
                });
                setTimeout(chart2.flush, 500);
            }, 1000);

            chart3 = c3.generate({
                bindto: "#chart3",
                data: {
                    columns: [
                        ['Memorized'],
                        ['Not Memorized']
                    ],
                    type: 'pie',
                    colors: {
                        'Memorized': '#55ff55',
                        'Not Memorized': '#ff5555',
                    },
                    onclick: function (d, i) {
                        console.log("onclick", d, i);
                    },
                    onmouseover: function (d, i) {
                        console.log("onmouseover", d, i);
                    },
                    onmouseout: function (d, i) {
                        console.log("onmouseout", d, i);
                    }
                }
            });
            setTimeout(function () {
                chart3.load({
                    columns: [
                        ['Memorized', r.total_memorized / r.total],
                        ['Not Memorized', (r.total - r.total_memorized) / r.total]
                    ]
                });
                setTimeout(chart3.flush, 500);
            }, 1500);

            chart4 = c3.generate({
                bindto: "#chart4",
                data: {
                    columns: [
                        ['Default'],
                        ['Tagged'],
                        ['Deleted']
                    ],
                    type: 'pie',
                    colors: {
                        Default: '#5555ff',
                        Tagged: 'yellow',
                        Deleted: 'gray',
                    },
                    onclick: function (d, i) {
                        console.log("onclick", d, i);
                    },
                    onmouseover: function (d, i) {
                        console.log("onmouseover", d, i);
                    },
                    onmouseout: function (d, i) {
                        console.log("onmouseout", d, i);
                    }
                }
            });
            setTimeout(function () {
                chart4.load({
                    columns: [
                        ['Default', (r.total - r.tag_cnt - r.del_cnt) / r.total],
                        ['Tagged', r.tag_cnt / r.total],
                        ['Deleted', r.del_cnt / r.total],
                    ]
                });
                setTimeout(chart4.flush, 500);
            }, 2000);

            $("text").css("font-family", "Comic Sans MS");
            if (localStorage.getItem("settings-theme") == "dark") {
                setInterval(function () {
                    $("text").css("fill", "#ffffff");
                    $(".c3-tooltip tr").css("color", "black")
                }, 50);
            }

            $("#modal").modal("show");
            $('#modal').on('hidden.bs.modal', function () {
                $("#modal").remove();
            });
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function BackToList() {
    $(".book-data-div").hide();
    $(".book-list-content-div").fadeIn();
    UpdateBookContentDisplay();

    window.history.pushState("My Memo", "My Memo", "/book");
    $(".title").html(`Book&nbsp;&nbsp;<button type="button" id="refresh-btn" class="btn btn-outline-secondary"
    onclick="UpdateBookContentList()"><i class="fa fa-sync"></i></button>`);
}