// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var bookId = -1;
var bookName = "";
var bookShareCode = "";
var groupId = -1;
var groupCode = "";
var isGroupOwner = false;
var isGroupEditor = false;
var discoveryId = -1;
var questionList = JSON.parse(lsGetItem("question-list", JSON.stringify([])));
var bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
var selectedQuestionList = [];
var questionListMap = new Map();
var selected = [];

function MapQuestionList() {
    questionListMap = new Map();
    for (var i = 0; i < questionList.length; i++) {
        questionListMap.set(questionList[i].questionId, {
            "question": questionList[i].question,
            "answer": questionList[i].answer,
            "status": questionList[i].status
        });
    }
}

function RefreshQuestionList(show401 = false) {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');
    // Update list
    $.ajax({
        url: "/api/book/questionList",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            questionList = r;
            localStorage.setItem("question-list", JSON.stringify(questionList));
            MapQuestionList();
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
                    MapQuestionList();
                    SelectQuestions();
                    UpdateTable();
                    $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
                },
                error: function (r, textStatus, errorThrown) {
                    if (r.status == 401 && show401) {
                        $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
                        SessionExpired();
                    } else {
                        NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                    }
                }
            });
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401 && show401) {
                $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
        }
    });
}

function SelectQuestions() {
    found = false;
    for (var i = 0; i < bookList.length; i++) {
        if (bookList[i].bookId == bookId) {
            found = true;
            $(".book-list-content-div").hide();
            $(".book-data-div").show();

            bookName = bookList[i].name;
            $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="RefreshQuestionList(show401=true)" id="refresh-btn"><i class="fa fa-refresh"></i></button>');
            $("title").html(bookName + " | My Memo");
            bookShareCode = bookList[i].shareCode;
            if (bookShareCode == "") {
                $("#bookShareCode").html("(Private)");
            } else {
                $("#bookShareCode").html(bookShareCode);
            }
            if (bookShareCode == "") {
                $("#shareop").html("Share");
                $(".only-shared").hide();
            } else {
                $("#shareop").html("Unshare");
                $(".only-shared").show();
            }
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
            if (discoveryId == -1 && bookShareCode != "") {
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

            selectedQuestionList = [];
            for (this.j = 0; j < bookList[i].questions.length; j++) {
                questionId = bookList[i].questions[j];
                questionData = questionListMap.get(questionId);
                selectedQuestionList.push({
                    "questionId": questionId,
                    "question": questionData.question,
                    "answer": questionData.answer,
                    "status": questionData.status
                });
            }
        }
    }
    if (!found) {
        $(".book-list-content-div").show();
        $(".book-data-div").hide();
        UpdateBookDisplay();
    }
}

function UpdateTable() {
    selected = [];

    table = $("#questionList").DataTable();
    table.clear();

    l = ["", "Default", "Tagged", "Deleted"];

    for (var i = 0; i < selectedQuestionList.length; i++) {
        btns = '';
        btns += '<button type="button" class="btn btn-primary btn-sm only-group-editor-if-group-exist" onclick="EditQuestionShow(' + selectedQuestionList[i].questionId + ')">Edit</button>';
        if (bookId != 0) {
            btns += '<button type="button" class="btn btn-warning btn-sm only-group-editor-if-group-exist" onclick="RemoveFromBook(' + selectedQuestionList[i].questionId + ')">Remove</button>';
        }
        table.row.add([
            [selectedQuestionList[i].question],
            [selectedQuestionList[i].answer],
            [l[selectedQuestionList[i].status]],
            [btns]
        ]).node().id = selectedQuestionList[i].questionId;
    }
    table.draw();

    if (localStorage.getItem("settings-theme") == "dark") {
        $("#questionList tr").attr("style", "background-color:#333333");
    } else {
        $("#questionList tr").attr("style", "background-color:#ffffff");
    }
}

function UpdateQuestionList() {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');
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
            UpdateBookDisplay();
            MapQuestionList();
            SelectQuestions();
            UpdateTable();
            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
        }
    });
}

function PageInit() {
    if (bookId == -1) {
        bookId = getUrlParameter("bookId");
    }
    if (bookId == -1) {
        UpdateBookContentList();
    } else {
        RefreshQuestionList();
    }

    table = $("#questionList").DataTable();
    table.clear();
    table.row.add([
        [""],
        ["Loading <i class='fa fa-spinner fa-spin'></i>"],
        [""],
        [""]
    ]);
    table.draw();
    if (localStorage.getItem("settings-theme") == "dark") {
        $("#questionList tr").attr("style", "background-color:#333333");
    } else {
        $("#questionList tr").attr("style", "background-color:#ffffff");
    }
    table.clear();

    if (bookId == 0) {
        $(".not-for-all-questions").hide();
    } else {
        $(".not-for-all-questions").show();
    }
    $(".group").hide();

    // Update username
    if (localStorage.getItem("username") != null && localStorage.getItem("username") != "") {
        username = localStorage.getItem("username");
        $("#navusername").html(username);
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

    // Use existing questions
    if (questionList.length != 0 && bookId != -1) {
        MapQuestionList();
        SelectQuestions();
        UpdateTable();
    }
}

var editQuestionId = -1;

function EditQuestionShow(wid) {
    editQuestionId = wid;
    question = "";
    answer = "";
    for (var i = 0; i < selectedQuestionList.length; i++) {
        if (selectedQuestionList[i].questionId == wid) {
            question = selectedQuestionList[i].question;
            answer = selectedQuestionList[i].answer;
            break;
        }
    }
    $("#editQuestionModalLabel").html("Edit Question");
    $("#edit-question").val(question);
    $("#edit-answer").val(answer);
    $("#editQuestionModal").modal('show');
    $("#edit-question-btn").html("Edit");
    $("#edit-question-btn").attr("onclick", "EditQuestion()");
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
            for (var i = 0; i < selectedQuestionList.length; i++) {
                if (selectedQuestionList[i].questionId == wid) {
                    selectedQuestionList[i].question = question;
                    selectedQuestionList[i].answer = answer;
                    break;
                }
            }

            NotyNotification("Success! Question edited!");

            $("#editQuestionModal").modal('hide');
            UpdateTable();
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
            for (var i = 0; i < selectedQuestionList.length; i++) {
                for (var j = 0; j < selected.length; j++) {
                    if (selectedQuestionList[i].questionId == selected[j]) {
                        selectedQuestionList[i].status = updateTo;
                        break;
                    }
                }
            }

            NotyNotification("Success! Question status updated!");

            UpdateTable();
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

function ShowQuestionDatabase() {
    $('#questionList').DataTable().column(3).visible(false);
    $(".manage").hide();
    $("#addExistingQuestion").show();
    $(".book-name").html(bookName);
    selected = [];

    table = $("#questionList").DataTable();
    table.clear();
    for (var i = 0; i < questionList.length; i++) {
        table.row.add([
            [questionList[i].question],
            [questionList[i].answer],
            [l[questionList[i].status]],
            ['<button type="button" class="btn btn-primary btn-sm only-group-editor-if-group-exist" onclick="EditQuestionShow(' + questionList[i].questionId + ')">Edit</button>\
            <button type="button" class="btn btn-danger btn-sm only-group-editor-if-group-exist" onclick="RemoveFromBook(' + questionList[i].questionId + ')">Delete</button>']
        ]).node().id = questionList[i].questionId;
    }
    table.draw();
    for (var i = 0; i < questionList.length; i++) {
        if (questionList[i].status == "Tagged") {
            $("#" + questionList[i].questionId).attr("style", "color: red");
        } else if (questionList[i].status == "Deleted") {
            if (localStorage.getItem("settings-theme") == "dark") {
                $("#" + questionList[i].questionId).attr("style", "color: lightgray");
            } else {
                $("#" + questionList[i].questionId).attr("style", "color: gray");
            }
        }
    }
    if (localStorage.getItem("settings-theme") == "dark") {
        $("#questionList tr").attr("style", "background-color:#333333");
    } else {
        $("#questionList tr").attr("style", "background-color:#ffffff");
    }
}

function ShowManage() {
    $('#questionList').DataTable().column(3).visible(true);
    $("#addExistingQuestion").hide();
    $(".manage").show();
    UpdateTable();
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

                UpdateQuestionList();
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

function AddQuestionShow() {
    $("#edit-question").val("");
    $("#edit-answer").val("");
    $("#editQuestionModalLabel").html("Add a new question to " + bookName);
    $("#editQuestionModal").modal('show');
    $("#edit-question-btn").html("Add");
    $("#edit-question-btn").attr("onclick", "AddQuestion()");
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

                RefreshQuestionList();
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

function RemoveFromBook(wid = -1) {
    questions = [];
    if (wid == -1) {
        questions = selected;
    } else {
        questions = [wid];
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
            if (r.status == 401) {
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
        }
    });
}

function RemoveQuestionShow() {
    $("#deleteQuestionModal").modal("show");
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

                $("#deleteQuestionModal").modal('hide');

                RefreshQuestionList();
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
            if (r.status == 401) {
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
        }
    });
}

function BookRenameShow() {
    $("#renameModal").modal("show");
    $("#book-rename").val(bookName);
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
                $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="RefreshQuestionList(show401=true)" id="refresh-btn"><i class="fa fa-refresh"></i></button>');
                $("title").html(bookName + " | My Memo");
                NotyNotification('Success! Book renamed!');
                $("#renameModal").modal("hide");
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

function BookDeleteShow() {
    $("#deleteWBModal").modal("show");
    $(".book-name").html(bookName);
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
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! Book deleted!');
                setTimeout(function () {
                    window.location.href = '/book';
                }, 3000);
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

function BookShare() {
    if (bookShareCode == "") {
        $.ajax({
            url: '/api/book/share',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: bookId,
                operation: "share",
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success == true) {
                    for (var i = 0; i < bookList.length; i++) {
                        if (bookList[i].bookId == bookId) {
                            bookList[i].shareCode = r.shareCode;
                            bookShareCode = r.shareCode;
                            localStorage.setItem("book-list", JSON.stringify(bookList));
                            break;
                        }
                    }
                    NotyNotification(r.msg, type = 'info',  timeout = 30000);
                    $("#bookShareCode").html(r.shareCode);
                    $("#shareop").html("Unshare");
                    $(".only-shared").show();
                    discoveryId = bookList[i].discoveryId;
                    if (discoveryId == -1 && bookShareCode != "") {
                        $(".not-published-to-discovery").show();
                        $(".published-to-discovery").hide();
                    } else if (discoveryId != -1) {
                        $(".not-published-to-discovery").hide();
                        $(".published-to-discovery").show();
                        $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + discoveryId + "'");
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
    } else {
        $.ajax({
            url: '/api/book/share',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: bookId,
                operation: "unshare",
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success == true) {
                    for (var i = 0; i < bookList.length; i++) {
                        if (bookList[i].bookId == bookId) {
                            bookList[i].shareCode = "";
                            bookShareCode = "";
                            localStorage.setItem("book-list", JSON.stringify(bookList));
                            break;
                        }
                    }
                    NotyNotification(r.msg, type = 'success', timeout = 30000);
                    $("#bookShareCode").html("(Private)");
                    $("#shareop").html("Share");
                    $(".only-shared").hide();
                    discoveryId = bookList[i].discoveryId;
                    if (discoveryId == -1 && bookShareCode != "") {
                        $(".not-published-to-discovery").show();
                        $(".published-to-discovery").hide();
                    } else if (discoveryId != -1) {
                        $(".not-published-to-discovery").hide();
                        $(".published-to-discovery").show();
                        $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + discoveryId + "'");
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

function PublishToDiscoveryShow() {
    $('#publishToDiscoveryModal').modal('show');
}

function PublishToDiscovery() {
    title = $("#discovery-title").val();
    description = $("#discovery-description").val();

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

                $('#publishToDiscoveryModal').modal('hide');
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

function UnpublishDiscoveryShow() {
    $('#unpublishDiscoveryModal').modal('show');
}

function GroupPublishToDiscoveryShow() {
    $('#groupPublishToDiscoveryModal').modal('show');
}

function GroupPublishToDiscovery() {
    title = $("#group-discovery-title").val();
    description = $("#group-discovery-description").val();

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

                $('#groupPublishToDiscoveryModal').modal('hide');
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

function GroupUnpublishDiscoveryShow() {
    $('#groupUnpublishDiscoveryModal').modal('show');
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

function CreateGroupShow() {
    $("#create-group-btn").attr("onclick", "CreateGroup()");
    $("#create-group-btn").html("Create");
    $("#createGroupModalLabel").html("Create Group");
    $("#createGroupModal").modal("show");
}

function CreateGroup() {
    gname = $("#group-name").val();
    gdescription = $("#group-description").val();
    if (gname == "" || gdescription == "") {
        NotyNotification('Both fields must be filled', type = 'warning');
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

                        localStorage.setItem("book-list", JSON.stringify(bookList));
                        break;
                    }
                }
                NotyNotification(r.msg, type = 'info', timeout = 30000);
                $("#createGroupModal").modal("hide");
                $("#bookShareCode").html(r.shareCode);
                $("#shareop").html("Unshare");
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

function GroupMember() {
    window.location.href = "/group?groupId=" + groupId;
}

function QuitGroupShow() {
    $("#quitGroupModal").modal('show');
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

                        localStorage.setItem("book-list", JSON.stringify(bookList));
                        localStorage.setItem("groupId", "-1");
                        break;
                    }
                }
                $("#quitGroupModal").modal('hide');
                NotyNotification(r.msg);
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

function GroupInfoUpdateShow() {
    $("#create-group-btn").attr("onclick", "GroupInfoUpdate()");
    $("#create-group-btn").html("Update");
    $("#createGroupModalLabel").html("Update Group Information");
    $("#createGroupModal").modal("show");
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
                        localStorage.setItem("book-list", JSON.stringify(bookList));
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
            if (r.status == 401) {
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
        }
    });
}

function GroupInfoUpdate() {
    gname = $("#group-name").val();
    gdescription = $("#group-description").val();
    if (gname == "" || gdescription == "") {
        NotyNotification('Both fields must be filled', type = 'warning');
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
                        $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="RefreshQuestionList(show401=true)" id="refresh-btn"><i class="fa fa-refresh"></i></button>');
                        $("title").html(bookName + " | My Memo");
                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();
                        $(".only-group-owner-if-group-exist").show();
                        $(".only-group-editor-if-group-exist").show();

                        localStorage.setItem("book-list", JSON.stringify(bookList));
                        localStorage.setItem("groupId", "-1");
                        break;
                    }
                }
                $("#createGroupModal").modal('hide');
                NotyNotification(r.msg);

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

                        localStorage.setItem("book-list", JSON.stringify(bookList));
                        break;
                    }
                }
                NotyNotification(r.msg);

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

function GroupDismissShow() {
    $("#dismissGroupModal").modal("show");
    $(".book-name").html(bookName);
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

                        localStorage.setItem("book-list", JSON.stringify(bookList));
                        break;
                    }
                }
                NotyNotification(r.msg);
                $("#dismissGroupModal").modal("hide");
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

function selectAll() {
    $("#questionList tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && !$(this).hasClass("selected")) { // check for NaN
            selected.push(wid);
        }

        $(this).addClass("selected");
    });
}

function deselectAll() {
    $("#questionList tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && $(this).hasClass("selected")) { // check for NaN
            idx = selected.indexOf(wid);
            if (idx > -1) {
                selected.splice(idx, 1);
            }
        }

        $(this).removeClass("selected");
    });
}

function UpdateBookContentDisplay() {
    $(".book-content").remove();
    for (var i = 0; i < bookList.length; i++) {
        book = bookList[i];
        wcnt = "";
        if (book.bookId == 0) {
            wcnt = book.questions.length + ' questions';
        } else {
            wcnt = book.progress + ' memorized / ' + book.questions.length + ' questions';
        }
        btn = "";
        if (book.bookId != localStorage.getItem("memo-book-id")) {
            btn = '<button type="button" class="btn btn-primary " onclick="SelectBookContent(' + book.bookId + ')">Select</button>';
        } else {
            btn = '<button type="button" class="btn btn-secondary">Selected</button>'
        }
        bname = book.name;
        if (book.groupId != -1) {
            bname = "[Group] " + bname;
        }

        $(".book-list-content").append('<div class="book-content">\
        <p>' + bname + '</p>\
        <p>' + wcnt + '</p>\
        <button type="button" class="btn btn-primary " onclick="OpenBook(' + book.bookId + ')">Open</button>\
        ' + btn + '\
        <hr>\
        </div>');
    }
}

function SelectBookContent(bookId) {
    localStorage.setItem("memo-book-id", bookId);
    UpdateBookContentDisplay();
}

function SelectBook(bookId) {
    localStorage.setItem("memo-book-id", bookId);
    UpdateBookDisplay();
    UpdateBookContentDisplay();
}

function UpdateBookContentList() {
    $("#refresh-btn").html('<i class="fa fa-refresh fa-spin"></i>');
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
            $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
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
                UpdateBookList();
                UpdateBookDisplay();
                UpdateBookContentList();
                UpdateBookContentDisplay();
                NotyNotification('Success! Book created!');
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