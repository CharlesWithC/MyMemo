// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var bookId = -1;
var bookName = "";
var groupId = -1;
var groupCode = "";
var groupName = "";
var groupDescription = "";
var isGroupOwner = false;
var isGroupEditor = false;
var discoveryId = -1;
var groupDiscoveryId = -1;
var bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
setInterval(function () {
    bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
}, 5000); // this will be updated by general.js
var selected = [];

var curModalId = "";

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
    if (groupId == -1 || groupId != -1 && isGroupOwner) {
        btns += '<button type="button" class="btn btn-primary btn-sm" onclick="EditQuestionShow(' + questionId + ')"><i class="fa fa-edit"></i></button>';
        if ($("#removeFromDB").is(":checked") || bookId == 0) {
            btns += '<button type="button" class="btn btn-danger btn-sm remove-question-btn" onclick="RemoveFromBook(' + questionId + ')"><i class="fa fa-trash"></i></button>';
        } else {
            btns += '<button type="button" class="btn btn-warning btn-sm remove-question-btn" onclick="RemoveFromBook(' + questionId + ')"><i class="fa fa-trash"></i></button>';
        }
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

function BackToList() {
    $(".book-data-div").hide();
    $(".book-list-content-div").fadeIn();
    window.history.pushState("My Memo", "My Memo", "/book");
    $(".title").html(`Book&nbsp;&nbsp;<button type="button" id="refresh-btn" class="btn btn-outline-secondary"
    onclick="UpdateBookContentList()"><i class="fa fa-sync"></i></button>`);
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
            localStorage.setItem("book-list", JSON.stringify(bookList));
            UpdateBookContentDisplay();
            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        }
    });
}

function UpdateTable() {
    $("tbody tr").remove();
    statusIntToStr = ["", "Default", "Tagged", "Deleted"];
    for (var i = 0; i < data.length; i++) {
        AppendTableData("questionList", [
            marked.parse(data[i].question),
            marked.parse(data[i].answer),
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
    PaginateTable("questionList", page, total, "BookPage");
    SetTableInfo("questionList", content);
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
                PaginateTable("questionList", 1, 1, "BookPage");
                SetTableInfo("questionList", "Forbidden");
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
    selected = [];
    search = $("#search-content").val();
    orderBy = "none";
    SortTable(orderBy);
    UpdateQuestionList();
}

function OpenBook(bid = null) {
    $("tbody tr").remove();
    if (bid != null) {
        bookId = bid;
    }

    search = "";
    selected = [];

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

    window.history.pushState("My Memo", "My Memo", "/book/" + bookId);

    found = false;

    for (var i = 0; i < bookList.length; i++) {
        if (bookList[i].bookId == bookId) {
            found = true;
            $(".book-list-content-div").hide();
            $(".book-data-div").fadeIn();

            $(".group").show();

            totalQ = bookList[i].total;
            bookName = bookList[i].name;
            $(".title").html(bookName);
            $("title").html(bookName + " - My Memo");
            groupId = bookList[i].groupId;
            groupCode = bookList[i].groupCode;
            isGroupOwner = bookList[i].isGroupOwner;
            isGroupEditor = bookList[i].isGroupEditor;
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
            $("#groupCode").html(groupCode + " " + GenCPBtn(groupCode));
            $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode.substr(1)));
            if(groupCode == "@pvtgroup" || groupCode == "") $(".only-group-public").hide();
            else $(".only-group-public").show();
            discoveryId = bookList[i].discoveryId;
            if (discoveryId == -1) {
                $(".not-published-to-discovery").show();
                $(".published-to-discovery").hide();
            } else if (discoveryId != -1) {
                $(".not-published-to-discovery").hide();
                $(".published-to-discovery").show();
                $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery/" + discoveryId + "'");
            }
            if (groupId != -1) {
                groupDiscoveryId = bookList[i].groupDiscoveryId;
                if (groupDiscoveryId == -1 && groupCode != "") {
                    $(".group-not-published-to-discovery").show();
                    $(".group-published-to-discovery").hide();
                } else if (groupDiscoveryId != -1) {
                    $(".group-not-published-to-discovery").hide();
                    $(".group-published-to-discovery").show();
                    $("#group-go-to-discovery-btn").attr("onclick", "window.location.href='/discovery/" + groupDiscoveryId + "'");
                }
                $.ajax({
                    url: "/api/group/info",
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        groupId: groupId,
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        groupName = r.name;
                        groupDescription = r.description;
                    }
                });
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
    InitTable("questionList", [10, 25, 50, 100], 10, UpdatePageLimit, Search);
    InitSorting("questionList", ["question", "answer", "status"], ["asc", undefined, undefined], "BookListSort");
    bookId = window.location.href.split("/").pop();
    if (!$.isNumeric(bookId)) bookId = -1;
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
            localStorage.setItem("book-list", JSON.stringify(bookList));
            if (bookId != -1)
                OpenBook();
            else
                $(".book-list-content-div").show();
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
            statistics = TimestampToLocale(r.msg.replaceAll("\n", "<br>"));

            GenModal("<i class='fa fa-chart-bar'></i> Statistics", "<p>" + statistics + "</p>");
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

    curModalId = GenModal("<i class='fa fa-edit'></i> Edit",
        `<div class="form-group">
            <label for="edit-question" class="col-form-label">Question:</label>
            <textarea class="form-control" id="edit-question"></textarea>
        </div>
        <div class="form-group">
            <label for="edit-answer" class="col-form-label">Answer:</label>
            <textarea class="form-control" id="edit-answer" style="height:10em"></textarea>
        </div>`,
        `<button id="edit-question-btn" type="button" class="btn btn-primary" onclick="EditQuestion()">Edit</button>`);
    $("#edit-question").val(question);
    $("#edit-answer").val(answer);
    OnSubmit("#edit-question,#edit-answer", EditQuestion, true);
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
            question = r.question;
            answer = r.answer;
            for (var i = 0; i < data.length; i++)
                if (data[i].questionId == editQuestionId) {
                    data[i].question = question;
                    data[i].answer = answer;
                    break;
                }
            UpdateTable();

            if (r.success == true) NotyNotification(r.msg);
            else NotyNotification(r.msg, type = 'error');
            $("#" + curModalId).modal('hide');
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
            NotyNotification("Question status updated!");
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
                NotyNotification('Added ' + selected.length + ' question(s)!');

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
    GenModal("<i class='fa fa-plus'></i> Add",
        `<div class="form-group">
            <label for="add-question" class="col-form-label">Question:</label>
            <textarea class="form-control" id="add-question"></textarea>
        </div>
        <div class="form-group">
            <label for="add-answer" class="col-form-label">Answer:</label>
            <textarea class="form-control" id="add-answer" style="height:10em"></textarea>
        </div>`,
        `<button id="add-question-btn" type="button" class="btn btn-primary" onclick="AddQuestion()">Add</button>`);
    OnSubmit("#add-question,#add-answer", AddQuestion, true);
}

function AddQuestion() {
    question = $("#add-question").val();
    answer = $("#add-answer").val();
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
                NotyNotification('Added a new question!');
                $("#add-question").val("");
                $("#add-answer").val("");
                $("#add-question").focus();

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
    if (wid == -1) questions = selected;
    else questions = [wid];
    if (questions.length == 0) {
        NotyNotification("Make sure you selected at least one question!", type = 'warning');
        return;
    }
    if ($("#removeFromDB").is(":checked") || bookId == 0) {
        RemoveQuestionShow(wid);
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
                NotyNotification('Removed ' + questions.length + ' question(s) from this book!');

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


function RemoveQuestionShow(wid) {
    curModalId = GenModal("<span style='color:red'><i class='fa fa-trash'></i> Remove</span>",
        `<p>Are you sure to remove all select questions from <b>database</b>? This will remove them from <b>all books</b>.</p>
        <p>This operation cannot be undone.</p>`,
        `<button type="button" class="btn btn-danger" onclick="RemoveQuestion(` + wid + `)">Remove</button>`);
}

function RemoveQuestion(wid) {
    questions = [];
    if (wid == -1) questions = selected;
    else questions = [wid];
    if (questions.length == 0) {
        NotyNotification("Make sure you selected at least one question!", type = 'warning');
        return;
    }
    $.ajax({
        url: '/api/question/delete',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify(questions),
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Removed ' + questions.length + ' question(s) from database!');

                $("#" + curModalId).modal('hide');
                localStorage.setItem("memo-book-id", "0");

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
                NotyNotification('Book cloned!');
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
    curModalId = GenModal("<i class='fa fa-edit'></i> Rename Book",
        `<div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Name</span>
            <input type="text" class="form-control" id="book-rename" aria-describedby="basic-addon1">
        </div>`,
        `<button type="button" class="btn btn-primary" onclick="BookRename()">Rename</button>`);
    $("#book-rename").val(bookName);
    OnSubmit("#book-rename", BookRename);
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
                $(".title").html(bookName);
                $("title").html(bookName + " - My Memo");
                $("title").html(bookName + " - My Memo");
                NotyNotification('Book renamed!');
                $("#" + curModalId).modal("hide");
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
    curModalId = GenModal("<span style='color:red'><i class='fa fa-trash'></i> Delete Book</span>",
        `<p>Are you sure to delete this book? The questions will be preserved in the question database but they will no longer belong to this book.</p>
        <p>This operation cannot be undone.</p>
        <br>
        <p>Type the name of the book <b>` + bookName + `</b> to continue:</p>
        <div class="input-group mb-3">
            <input type="text" class="form-control" id="book-delete" aria-describedby="basic-addon1">
        </div>`,
        `<button type="button" class="btn btn-danger" onclick="BookDelete()">Delete</button>`);
    OnSubmit("#book-delete", BookDelete);
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
                NotyNotification('Book deleted!');
                $('#' + curModalId).on('hide.bs.modal', function () {
                    BackToList();
                });
                setTimeout(function () {
                    $("#" + curModalId).modal("hide");
                    BackToList();
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
    curModalId = GenModal("<i class='fa fa-paper-plane'></i> Publish To Discovery",
        `<p>You are about to publish the book to Discovery.</p>
        <p>This will make it able to be found by any people.</p>
        <p>All your updates made within this book will be synced to Discovery. (But people already
            imported it will not get the sync, use Group function to do that)</p>
        <br>
        <p>Please enter title and description below. Make them beautiful and others may get engaged.</p>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Title</span>
            <input type="text" class="form-control" id="discovery-title" aria-describedby="basic-addon1">
        </div>
        <div class="form-group">
            <label for="discovery-description" class="col-form-label">Description:</label>
            <script>var descriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
            <textarea class="form-control" id="discovery-description" style="height:10em"></textarea>
        </div>`,
        `<button id="publish-to-discovery-btn" type="button" class="btn btn-primary" onclick="PublishToDiscovery()">Publish</button>`);
    BeautifyMarkdownEditor();
    OnSubmit("#discovery-title,#discovery-description", PublishToDiscovery, true);
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
                $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery/" + discoveryId + "'");

                NotyNotification(r.msg);

                $('#' + curModalId).modal('hide');
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
    curModalId = GenModal(`<span style="color:red"><i class="fa fa-trash"></i> Unpublish From Discovery</span>`,
        `<p>Are you sure to unpublish the book from Discovery?</p>
        <p>You will lose all the views and likes of your post.</p>
        <p>This operation cannot be undone.</p>`,
        `<button type="button" class="btn btn-danger" onclick="UnpublishDiscovery()">Unpublish</button>`);
}

function GroupPublishToDiscoveryShow() {
    curModalId = GenModal(`<i class="fa fa-paper-plane"></i> Publish To Discovery`,
        `<p>You are about to publish the group to Discovery.</p>
        <p>This will make it able to be found by any people.</p>
        <p>Any people will be able to find it and join your group.</p>
        <p>You can make your group a private group if you want to temporarily make it invisible on
            Discovery.</p>
        <br>
        <p>Please enter title and description below. Make them beautiful and others may get engaged.</p>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Title</span>
            <input type="text" class="form-control" id="group-discovery-title" aria-describedby="basic-addon1">
        </div>
        <div class="form-group">
            <label for="group-discovery-description" class="col-form-label">Description:</label>
            <script>var descriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
            <textarea class="form-control" id="group-discovery-description" style="height:10em"></textarea>
        </div>`,
        `<button id="publish-to-discovery-btn" type="button" class="btn btn-primary" onclick="GroupPublishToDiscovery()">Publish</button>`);
    BeautifyMarkdownEditor();
    OnSubmit("#group-discovery-title,#group-discovery-description", GroupPublishToDiscovery, true);
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
                $("#group-go-to-discovery-btn").attr("onclick", "window.location.href='/discovery/" + discoveryId + "'");

                NotyNotification(r.msg, type = 'success', timeout = 30000);

                $('#' + curModalId).modal('hide');
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
    curModalId = GenModal(`<span style='color:red'><i class="fa fa-trash"></i> Unpublish From Discovery</span>`,
        `<p>Are you sure to unpublish the group from Discovery?</p>
        <p>You will lose all the views and likes of your post.</p>
        <p>This operation cannot be undone.</p>`,
        `<button type="button" class="btn btn-danger" onclick="GroupUnpublishDiscovery()">Unpublish</button>`);
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
                $('#' + curModalId).modal('hide');
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
                $('#' + curModalId).modal('hide');
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
    curModalId = GenModal(`<i class='fa fa-user-group'></i> Create Group`,
        `<p>Your group need a name and a description so others can know about it.</p>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Name</span>
            <input type="text" class="form-control" id="group-name" aria-describedby="basic-addon1">
        </div>
        <div class="form-group">
            <label for="group-description" class="col-form-label">Description:</label>
            <script>var groupDescriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
            <textarea class="form-control" id="group-description" style="height:10em"></textarea>
        </div>`,
        `<button id="create-group-btn" type="button" class="btn btn-primary" onclick="CreateGroup()">Create</button>`);
    BeautifyMarkdownEditor();
    OnSubmit("#group-name,#group-description", CreateGroup, true);
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

                        $("#groupCode").html(groupCode + " " + GenCPBtn(groupCode));
                        $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode.substr(1)));
                        if(groupCode == "@pvtgroup" || groupCode == "") $(".only-group-public").hide();
                        else $(".only-group-public").show();
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();
                        $(".group-not-published-to-discovery").show();

                        break;
                    }
                }
                NotyNotification(r.msg, type = 'info', timeout = 30000);
                $("#" + curModalId).modal("hide");
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
    window.location.href = "/group/" + groupId;
}

function QuitGroupShow() {
    curModalId = GenModal(`<span style="color:yellow"><i class="fa fa-arrow-right-from-bracket"></i> Quit Group</span>`,
        `<p>Are you sure to quit the group? Your progress will no longer be shared with other members and the data sync will stop.</p>
        <p>You will not be able to join the group again unless you have the invite code.</p>`,
        `<button type="button" class="btn btn-warning" onclick="QuitGroup()">Quit</button>`);
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

                        $("#groupCode").html(groupCode + " " + GenCPBtn(groupCode));
                        $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode.substr(1)));
                        if(groupCode == "@pvtgroup" || groupCode == "") $(".only-group-public").hide();
                        else $(".only-group-public").show();
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();

                        localStorage.setItem("groupId", "-1");
                        break;
                    }
                }
                $("#" + curModalId).modal('hide');
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
    curModalId = GenModal(`<i class='fa fa-edit'></i> Update Group Information`,
        `<div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Name</span>
            <input type="text" class="form-control" id="group-name" aria-describedby="basic-addon1">
        </div>
        <div class="form-group">
            <label for="group-description" class="col-form-label">Description:</label>
            <script>var groupDescriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
            <textarea class="form-control" id="group-description" style="height:10em"></textarea>
        </div>`,
        `<button id="create-group-btn" type="button" class="btn btn-primary" onclick="GroupInfoUpdate()">Update</button>`);
    $("#group-name").val(groupName);
    $('#' + curModalId).on('shown.bs.modal', function () {
        groupDescriptionMDE.value(groupDescription);
    });
    BeautifyMarkdownEditor();
    OnSubmit("#group-name,#group-description", GroupInfoUpdate, true);
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
                        $(".title").html(bookName);
                        $("title").html(bookName + " - My Memo");
                        $("title").html(bookName + " - My Memo");
                        $("#groupCode").html(groupCode + " " + GenCPBtn(groupCode));
                        $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode.substr(1)));
                        if(groupCode == "@pvtgroup" || groupCode == "") $(".only-group-public").hide();
                        else $(".only-group-public").show();
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();

                        localStorage.setItem("groupId", "-1");
                        break;
                    }
                }
                $("#" + curModalId).modal('hide');
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

                        $("#groupCode").html(groupCode + " " + GenCPBtn(groupCode));
                        $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode.substr(1)));
                        if(groupCode == "@pvtgroup" || groupCode == "") $(".only-group-public").hide();
                        else $(".only-group-public").show();

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
    curModalId = GenModal(`<span style="color:red"><i class="fa fa-users-slash"></i> Dismiss Group</span>`,
        `<p>Are you sure to dismiss the group? The group data sync will stop and it will be deleted permanently.</p>
        <p>All members will quit automatically and they will not be able to see each other's progress.</p>
        <p>This operation cannot be undone.</p>
        <p>*If you just want to make your group private or revoke the code, there are options just above the dismiss button.</p>
        <br>
        <p>Type the name of the group <b>` + bookName + `</b> to continue:</p>
        <div class="input-group mb-3">
            <input type="text" class="form-control" id="group-delete" aria-describedby="basic-addon1">
        </div>`,
        `<button type="button" class="btn btn-danger" onclick="GroupDismiss()">Dismiss</button>`);
    OnSubmit("#group-delete", GroupDismiss);
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

                        $("#groupCode").html(groupCode + " " + GenCPBtn(groupCode));
                        $("#groupLink").html(GenCPBtn("http://" + window.location.hostname + "/group/join/" + groupCode.substr(1)));
                        if(groupCode == "@pvtgroup" || groupCode == "") $(".only-group-public").hide();
                        else $(".only-group-public").show();
                        $(".only-group-exist").hide();
                        $(".only-group-inexist").show();
                        $(".only-group-owner").hide();

                        break;
                    }
                }
                NotyNotification(r.msg);
                $("#" + curModalId).modal("hide");
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

    $(".title").html(bookName);
    $("title").html(bookName + " - My Memo");
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
            localStorage.setItem("book-list", JSON.stringify(bookList));
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
                NotyNotification('Book created!');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function ImportShare() {
    shareCode = $("#page-import-share").val();
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
            } else {
                window.location.href = "/share/import/" + shareCode;
            }
        }
    });
}

function JoinGroup() {
    groupCode = $("#page-join-group").val();
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
            } else {
                window.location.href = "/group/join/" + groupCode;
            }
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
            GenModal(`<i class="fa fa-chart-bar"></i> Book Statistics`,
                `<div id="charts" style="border-radius:0.5em">
                    <div class="chart" id="chart1"></div>
                    <div class="chart" id="chart2"></div>
                    <div class="chart" id="chart3" style="width:49%;display:inline-block;"></div>
                    <div class="chart" id="chart4" style="width:49%;display:inline-block;"></div>
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
            BeautifyC3Chart();
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}