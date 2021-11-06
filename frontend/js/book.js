// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

function lsGetItem(lsItemName, defaultValue = 0) {
    if (localStorage.getItem(lsItemName) == null || localStorage.getItem(lsItemName) == "undefined") {
        localStorage.setItem(lsItemName, defaultValue);
        return defaultValue;
    } else {
        return localStorage.getItem(lsItemName);
    }
}

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

function GoToUser() {
    window.location.href = "/user"
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
    return -1;
};

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
                error: function (r) {
                    if (r.status == 401 && show401) {
                        $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
                        SessionExpired();
                    }
                }
            });
        },
        error: function (r) {
            if (r.status == 401 && show401) {
                $("#refresh-btn").html('<i class="fa fa-refresh"></i>');
                SessionExpired();
            }
        }
    });
}

function SelectQuestions() {
    found = false;
    for (var i = 0; i < bookList.length; i++) {
        if (bookList[i].bookId == bookId) {
            found = true;
            $(".book-list-div").hide();
            $(".book-data-div").show();

            bookName = bookList[i].name;
            $(".title").html(bookName + '&nbsp;&nbsp;<button type="button" class="btn btn-outline-secondary" onclick="RefreshQuestionList(show401=true)" id="refresh-btn"><i class="fa fa-refresh"></i></button>');
            $("title").html("My Memo - " + bookName);
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
        $(".book-list-div").show();
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
        table.row.add([
            [selectedQuestionList[i].question],
            [selectedQuestionList[i].answer],
            [l[selectedQuestionList[i].status]]
        ]).node().id = selectedQuestionList[i].questionId;
    }
    table.draw();

    if (localStorage.getItem("settings-theme") == "dark") {
        $("#questionList tr").attr("style", "background-color:#333333");
    }
}

function PageInit() {
    if (bookId == -1) {
        bookId = getUrlParameter("bookId");
    }

    table = $("#questionList").DataTable();
    table.clear();
    table.row.add([
        [""],
        ["Loading <i class='fa fa-spinner fa-spin'></i>"],
        [""],
    ]);
    table.draw();
    if (localStorage.getItem("settings-theme") == "dark") {
        $("#questionList tr").attr("style", "background-color:#333333");
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
            error: function (r) {
                $("#navusername").html("Sign in");
                localStorage.setItem("username", "");
            }
        });
    }

    // Use existing questions
    if (questionList.length != 0) {
        MapQuestionList();
        SelectQuestions();
        UpdateTable();
    }

    RefreshQuestionList();
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
    $("#editQuestionModal").modal('toggle');
    $("#edit-question-btn").html("Edit");
    $("#edit-question-btn").attr("onclick", "EditQuestion()");
}

function EditQuestionFromBtn() {
    if (selected.length != 1) {
        new Noty({
            theme: 'mint',
            text: 'Make sure you selected one question!',
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
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

            new Noty({
                theme: 'mint',
                text: 'Success! Question edited!',
                type: 'success',
                layout: 'bottomRight',
                timeout: 3000
            }).show();

            $("#editQuestionModal").modal('toggle');
            UpdateTable();
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
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
                        console.log(selectedQuestionList[i].questionId);
                        selectedQuestionList[i].status = updateTo;
                        break;
                    }
                }
            }

            new Noty({
                theme: 'mint',
                text: 'Success! Question status updated!',
                type: 'success',
                layout: 'bottomRight',
                timeout: 3000
            }).show();

            UpdateTable();
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function ShowQuestionDatabase() {
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
            [l[questionList[i].status]]
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
    }
}

function ShowManage() {
    $("#addExistingQuestion").hide();
    $(".manage").show();
    UpdateTable();
}

function AddExistingQuestion() {
    $.ajax({
        url: '/api/book/addQuestion',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            questions: JSON.stringify(selected),
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Added ' + selected.length + ' question(s)!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                UpdateBookList(false);
                MapQuestionList();
                SelectQuestions();
                UpdateTable();
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

function AddQuestionShow() {
    $("#edit-question").val("");
    $("#edit-answer").val("");
    $("#editQuestionModalLabel").html("Add a new question to " + bookName);
    $("#editQuestionModal").modal('toggle');
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
                new Noty({
                    theme: 'mint',
                    text: 'Success! Added a new question!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                $("#editQuestionModal").modal('toggle');

                RefreshQuestionList();
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

function RemoveFromBook() {
    $.ajax({
        url: '/api/book/deleteQuestion',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            questions: JSON.stringify(selected),
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Removed ' + selected.length + ' question(s) from this book!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                UpdateBookList(false);
                MapQuestionList();
                SelectQuestions();
                UpdateTable();
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

function RemoveQuestionShow() {
    $("#deleteQuestionModal").modal("toggle");
}

function RemoveQuestion() {
    $.ajax({
        url: '/api/question/delete',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            questions: JSON.stringify(selected),
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Removed ' + selected.length + ' question(s) from database!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                $("#deleteQuestionModal").modal('toggle');

                RefreshQuestionList();
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

function BookClone() {
    $.ajax({
        url: '/api/book/clone',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            fromBook: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Cloned this book!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
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

function BookRenameShow() {
    $("#renameModal").modal("toggle");
    $("#book-rename").val(bookName);
}

function BookRename() {
    newName = $("#book-rename").val();
    if (newName == "") {
        new Noty({
            theme: 'mint',
            text: "Enter new name!",
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: '/api/book/rename',
        method: 'POST',
        async: false,
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
                $("title").html("My Memo - " + bookName);
                new Noty({
                    theme: 'mint',
                    text: "Success! Book renamed!",
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
                $("#renameModal").modal("toggle");
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

function BookDeleteShow() {
    $("#deleteWBModal").modal("toggle");
    $(".book-name").html(bookName);
}

function BookDelete() {
    if ($("#book-delete").val() != bookName) {
        new Noty({
            theme: 'mint',
            text: "Type the name of the book correctly to continue!",
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }
    $.ajax({
        url: '/api/book/delete',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            bookId: bookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: "Success! Book deleted!",
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
                setTimeout(BackToHome, 3000);
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

function BookShare() {
    if (bookShareCode == "") {
        $.ajax({
            url: '/api/book/share',
            method: 'POST',
            async: false,
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
                    new Noty({
                        theme: 'mint',
                        text: r.msg,
                        type: 'success',
                        layout: 'bottomRight',
                        timeout: 30000
                    }).show();
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
    } else {
        $.ajax({
            url: '/api/book/share',
            method: 'POST',
            async: false,
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
                    new Noty({
                        theme: 'mint',
                        text: r.msg,
                        type: 'success',
                        layout: 'bottomRight',
                        timeout: 3000
                    }).show();
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

function PublishToDiscoveryShow() {
    $('#publishToDiscoveryModal').modal('toggle');
}

function PublishToDiscovery() {
    title = $("#discovery-title").val();
    description = $("#discovery-description").val();

    $.ajax({
        url: '/api/discovery/book/publish',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            bookId: bookId,
            title: title,
            description: description,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                discoveryId = r.discoveryId;
                $(".not-published-to-discovery").hide();
                $(".published-to-discovery").show();
                $("#go-to-discovery-btn").attr("onclick", "window.location.href='/discovery?discoveryId=" + discoveryId + "'");
                
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
                
                $('#publishToDiscoveryModal').modal('toggle');
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

function UnpublishDiscoveryShow(){
    $('#unpublishDiscoveryModal').modal('toggle');
}

function UnpublishDiscovery(){
    $.ajax({
        url: '/api/discovery/book/unpublish',
        method: 'POST',
        async: false,
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
                
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
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

function CreateGroupShow() {
    $("#create-group-btn").attr("onclick", "CreateGroup()");
    $("#create-group-btn").html("Create");
    $("#createGroupModalLabel").html("Create Group");
    $("#createGroupModal").modal("toggle");
}

function CreateGroup() {
    gname = $("#group-name").val();
    gdescription = $("#group-description").val();
    if (gname == "" || gdescription == "") {
        new Noty({
            theme: 'mint',
            text: 'Both fields must be filled!',
            type: 'warning',
            layout: 'topLeft',
            timeout: 3000
        }).show();
        return;
    }
    $.ajax({
        url: '/api/group',
        method: 'POST',
        async: false,
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
                $("#createGroupModal").modal("toggle");
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
                $("#bookShareCode").html(r.shareCode);
                $("#shareop").html("Unshare");
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

function GroupMember() {
    window.location.href = "/group?groupId=" + groupId;
}

function QuitGroupShow() {
    $("#quitGroupModal").modal('toggle');
}

function QuitGroup() {
    $.ajax({
        url: '/api/group/quit',
        method: 'POST',
        async: false,
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
                $("#quitGroupModal").modal('toggle');
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
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

function GroupInfoUpdateShow() {
    $("#create-group-btn").attr("onclick", "GroupInfoUpdate()");
    $("#create-group-btn").html("Update");
    $("#createGroupModalLabel").html("Update Group Information");
    $("#createGroupModal").modal("toggle");
}

function GroupInfoUpdate() {
    gname = $("#group-name").val();
    gdescription = $("#group-description").val();
    if (gname == "" || gdescription == "") {
        new Noty({
            theme: 'mint',
            text: 'Both fields must be filled!',
            type: 'warning',
            layout: 'topLeft',
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
                        $("title").html("My Memo - " + bookName);
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
                $("#createGroupModal").modal('toggle');
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();

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

function GroupCodeUpdate(operation) {
    $.ajax({
        url: '/api/group/code/update',
        method: 'POST',
        async: false,
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
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();

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

function GroupDismissShow() {
    $("#dismissGroupModal").modal("toggle");
    $(".book-name").html(bookName);
}

function GroupDismiss() {
    if ($("#group-delete").val() != bookName) {
        new Noty({
            theme: 'mint',
            text: "Type the name of the group correctly to continue!",
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }
    $.ajax({
        url: '/api/group',
        method: 'POST',
        async: false,
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
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 30000
                }).show();
                $("#dismissGroupModal").modal("toggle");
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

function UpdateBookDisplay() {
    $(".book").remove();
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
            btn = '<button type="button" class="btn btn-primary " onclick="SelectBook(' + book.bookId + ')">Select</button>';
        } else {
            btn = '<button type="button" class="btn btn-secondary">Selected</button>'
        }
        bname = book.name;
        if (book.groupId != -1) {
            bname = "[Group] " + bname;
        }

        $(".book-list").append('<div class="book">\
        <p>' + bname + '</p>\
        <p>' + wcnt + '</p>\
        <button type="button" class="btn btn-primary " onclick="OpenBook(' + book.bookId + ')">Open</button>\
        ' + btn + '\
        <hr>\
        </div>');
    }
}

function OpenBook(bookId) {
    window.location.href = '/book?bookId=' + bookId;
}

function SelectBook(bookId) {
    localStorage.setItem("memo-book-id", bookId);
    UpdateBookDisplay();
}

function UpdateBookList(doasync = true) {
    $.ajax({
        url: "/api/book",
        method: 'POST',
        async: doasync,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            bookList = r;
            localStorage.setItem("book-list", JSON.stringify(bookList));
        }
    });
}

function CreateBook() {
    bookName = $("#create-book-name").val();

    if (bookName == "") {
        new Noty({
            theme: 'mint',
            text: 'Enter a book name!',
            type: 'warning',
            layout: 'topLeft',
            timeout: 3000
        }).show();
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
                UpdateBookList(false);
                UpdateBookDisplay();
                new Noty({
                    theme: 'mint',
                    text: 'Success!',
                    type: 'success',
                    layout: 'topLeft',
                    timeout: 3000
                }).show();
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'topLeft',
                    timeout: 3000
                }).show();
            }
        },
        error: function (r) {
            if (r.status == 401) {
                alert("Login session expired! Please login again!");
                localStorage.removeItem("userId");
                localStorage.removeItem("token");
                window.location.href = "/user";
            }
        }
    });
}

function SignOut() {
    $.ajax({
        url: "/api/user/logout",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        }
    });
    localStorage.removeItem("userid");
    localStorage.removeItem("username");
    localStorage.removeItem("token");
    localStorage.removeItem("memo-question-id");
    localStorage.removeItem("memo-book-id");
    localStorage.removeItem("book-list");
    localStorage.removeItem("question-list");

    $("#navusername").html("Sign in");

    new Noty({
        theme: 'mint',
        text: 'Success! You are now signed out!',
        type: 'success',
        layout: 'bottomRight',
        timeout: 3000
    }).show();
}