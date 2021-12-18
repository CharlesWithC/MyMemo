// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

class MemoClass {
    constructor() {
        this.questionId = 0;
        this.question = "";
        this.answer = "";
        this.questionStatus = 0;
        this.challengeStatus = 0;

        this.bookId = 0;
        this.bookName = "";

        this.fullQuestionList = [];
        this.questionListMap = new Map();
        this.bookList = [];
        this.selectedQuestionList = [];

        this.started = false;
        this.displayingAnswer = false;

        this.speaker = window.speechSynthesis;
    }
}

apdelay = [99999, 8, 5, 3];
class SettingsClass {
    constructor() {
        this.random = 0;
        this.swap = 0;
        this.showStatus = 1;
        this.mode = 0;

        this.autoPlay = 0;
        this.apinterval = -1;

        this.firstuse = 1;
    }
}

var ccCorrect = -1;
var goal = 0;
var chtoday = 0;
memo = new MemoClass();
memo.questionId = parseInt(lsGetItem("memo-question-id", 0));
memo.bookId = parseInt(lsGetItem("memo-book-id", 0));
memo.fullQuestionList = JSON.parse(ssGetItem("question-list", JSON.stringify([])));
memo.bookList = JSON.parse(ssGetItem("book-list", JSON.stringify([])));

settings = new SettingsClass();
settings.random = parseInt(lsGetItem("settings-random", 0));
settings.swap = parseInt(lsGetItem("settings-swap", 0));
settings.showStatus = parseInt(lsGetItem("settings-show-status", 1));
settings.mode = parseInt(lsGetItem("settings-mode", 0));
settings.autoPlay = parseInt(lsGetItem("settings-auto-play", 0));
settings.apinterval = -1;
settings.firstuse = parseInt(lsGetItem("first-use", 1));

var ccCorrectAudio = new Audio('/audio/correct.mp3');
var ccWrongAudio = new Audio('/audio/wrong.mp3');

function MapQuestionList() {
    memo.questionListMap = new Map();
    for (var i = 0; i < memo.fullQuestionList.length; i++) {
        memo.questionListMap.set(memo.fullQuestionList[i].questionId, {
            "question": memo.fullQuestionList[i].question,
            "answer": memo.fullQuestionList[i].answer,
            "status": memo.fullQuestionList[i].status
        });
    }
}

MapQuestionList();

function UpdateSelectedQuestionList() {
    for (var i = 0; i < memo.bookList.length; i++) {
        if (memo.bookList[i].bookId == memo.bookId) {
            memo.bookName = memo.bookList[i].name;
            $("#book-name").html(memo.bookName);
            memo.selectedQuestionList = [];
            for (this.j = 0; j < memo.bookList[i].questions.length; j++) {
                questionId = memo.bookList[i].questions[j];
                questionData = memo.questionListMap.get(questionId);
                memo.selectedQuestionList.push({
                    "questionId": questionId,
                    "question": questionData.question,
                    "answer": questionData.answer,
                    "status": questionData.status
                });
            }
        }
    }
}

function UpdateBookDisplay() {
    $(".book").remove();
    for (var i = 0; i < memo.bookList.length; i++) {
        book = memo.bookList[i];
        wcnt = "";
        if (book.bookId == 0) {
            wcnt = book.questions.length + ' questions';
        } else {
            wcnt = book.progress + ' memorized / ' + book.questions.length + ' questions';
        }
        btn = "";
        if (book.bookId != memo.bookId) {
            btn = '<button type="button" class="btn btn-primary " onclick="SelectBook(' + book.bookId + ')">Select</button>';
        } else {
            btn = '<button type="button" class="btn btn-secondary">Selected</button>'
        }
        bname = book.name;
        if (book.groupId != -1) {
            bname = "[Group] " + bname;
        }

        $("#book-list").append('<div class="book">\
        <p>' + bname + '</p>\
        <p>' + wcnt + '</p>\
        <button type="button" class="btn btn-primary " onclick="OpenBook(' + book.bookId + ')">Open</button>\
        ' + btn + '\
        <hr>\
        </div>');
    }
}

function UpdateBookList() {
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
            memo.bookList = r;
            try{sessionStorage.setItem("book-list", JSON.stringify(memo.bookList));}catch{console.warning("Cannot store book list to Session Storage, aborted!");}
            UpdateSelectedQuestionList();
            UpdateBookDisplay();
        }
    });
}

function PageInit() {
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        $("#home").css("line-height","85%");
    } else {
        $("#home").css("line-height","65%");
    }
    l = ["Switch", "Practice", "Challenge", "Offline"];
    $("#mode").html(l[settings.mode]);
    if (memo.fullQuestionList.length != 0) {
        UpdateSelectedQuestionList();
        $("#book-name").html(memo.bookName);
    }

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
            memo.fullQuestionList = r;
            try {
                sessionStorage.setItem("question-list", JSON.stringify(memo.fullQuestionList));
            } catch {
                console.warning("Session storage cannot store question-list, aborted!");
            }
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
                    memo.bookList = r;
                    try{sessionStorage.setItem("book-list", JSON.stringify(memo.bookList));}catch{console.warning("Cannot store book list to Session Storage, aborted!");}
                    UpdateSelectedQuestionList();
                    $("#book-name").html(memo.bookName);
                }
            });
        }
    });

    if (lsGetItem("userId", -1) != -1) {
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
                localStorage.setItem("username", r.username);

                goal = r.goal;
                chtoday = r.chtoday;
                checkin_today = r.checkin_today;
                checkin_continuous = r.checkin_continuous;

                $("#navusername").html(r.username);

                $("#goal-progress").css("width", Math.min(chtoday / goal * 100, 100) + "%");
                $("#today-goal").html(chtoday + " / " + goal);

                if (checkin_today || chtoday < goal) {
                    $("#checkin-btn").attr("disabled", "disabled");
                    if (checkin_today) {
                        $("#checkin-btn").html('<i class="fa fa-check-square"></i>');
                    }
                } else {
                    $("#checkin-btn").removeAttr("disabled");
                }
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    $(".user").remove();
                    $(".login").show();
                    $(".title").hide();
                    $("#signout-btn").hide();
                }
            }
        });
    }
}

function DisplayRandomQuestion() {
    if (!$("#start-from").is(":focus") && !memo.started && memo.selectedQuestionList.length != 0) {
        index = parseInt(Math.random() * memo.selectedQuestionList.length);
        memo.questionId = memo.selectedQuestionList[index].questionId;
        memo.question = memo.selectedQuestionList[index].question;
        memo.answer = memo.selectedQuestionList[index].answer;
        memo.questionStatus = memo.selectedQuestionList[index].status;

        $("#start-from").val(memo.question);
    }
}
setInterval(DisplayRandomQuestion, 3000);

function ShowQuestion() {
    if (settings.firstuse) {
        NotyNotification('Hint: Click question or double click answer to let your device speak it!', type = 'info', timeout = 10000);
        localStorage.setItem("first-use", 0);
        settings.firstuse = false;
    }
    if (settings.mode != 2) { // spj
        if (settings.swap == 0) {
            $("#question").val(memo.question);
            $("#answer").val("");
        } else if (settings.swap == 1) {
            $("#question").val("");
            $("#answer").val(memo.answer);
        } else if (settings.swap == 2 && settings.mode != 1) {
            $("#question").val(memo.question);
            $("#answer").val(memo.answer);
        }
    }
    if (settings.autoPlay != 0) {
        $(".ap-btn").show();
    }
    $(".memo-tag").html("Tag <i class='fa fa-star'></i>");
    $(".memo-delete").html("Delete <i class='fa fa-trash'></i>");
    if (memo.questionStatus == 2) {
        $(".memo-tag").html("Untag <i class='fa fa-star-o'></i>");
    } else if (memo.questionStatus == 3) {
        $(".memo-delete").html("Undelete <i class='fa fa-undo'></i>");
    }
    $("#home").hide();
    $(".title").show();
    $("#memo").fadeIn();
    $(".control").hide();
    if (settings.mode == 0) {
        $("#practice-control").show();
        $("#statistics-btn").show();
        $("#edit-btn").show();
    } else if (settings.mode == 1) {
        $("#challenge-yesno-control").show();
        $("#statistics-btn").hide();
        $("#edit-btn").hide();
    } else if (settings.mode == 2) {
        $("#challenge-choice-control").show();
        $("#statistics-btn").hide();
        $("#edit-btn").hide();
    } else if (settings.mode == 3) {
        $("#offline-control").show();
        $("#statistics-btn").hide();
        $("#edit-btn").hide();
    }

    memo.displayingAnswer = 0;
    memo.started = true;

    if (settings.apinterval != -1 && settings.mode != 1 && settings.mode != 2) {
        memo.speaker.cancel();
        msg = undefined;
        if (settings.swap != 1 || settings.swap == 1 && memo.displayingAnswer) {
            msg = new SpeechSynthesisUtterance($("#question").val());
        } else {
            msg = new SpeechSynthesisUtterance($("#answer").val());
        }
        memo.speaker.speak(msg);
    }
    if (settings.apinterval == -1 || settings.mode == 1) {
        $(".ap-btn").hide();
    } else {
        $(".ap-btn").show();
    }

    $("#start-btn").html("Go <i class='fa fa-play'></i>");
}

function DisplayAnswer() {
    if (memo.started) {
        if (settings.mode == 0 || settings.mode == 3) {
            if (settings.swap == 0) {
                if (!memo.displayingAnswer) $("#answer").val(memo.answer);
                else $("#answer").val("");
            } else if (settings.swap == 1) {
                if (!memo.displayingAnswer) $("#question").val(memo.question);
                else $("#question").val("");
            } else if (settings.swap == 2) {
                return;
            }
        }
        memo.displayingAnswer = 1 - memo.displayingAnswer;
    }
    if (!memo.started) {
        $("#book-div").fadeOut();
    }
}

function MemoMove(direction) {
    $("#statisticsQuestion").html("");
    $("#statisticsDetail").html("");
    if (settings.mode == 0) {
        moveType = 0;
        if (direction == "previous") {
            moveType = -1;
        } else if (direction == "next") {
            moveType = 1;
        }
        if (settings.random) {
            moveType = 0;
        }

        memo.displayingAnswer = 0;

        $.ajax({
            url: '/api/question/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                questionId: memo.questionId,
                status: settings.showStatus,
                moveType: moveType,
                bookId: memo.bookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;
                memo.questionId = r.questionId;
                ShowQuestion();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    SessionExpired();
                } else {
                    NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                }
            }
        });
    } else if (settings.mode == 3) {
        moveType = 0;
        if (direction == "previous") {
            moveType = -1;
        } else if (direction == "next") {
            moveType = 1;
        }
        if (settings.random) {
            moveType = 0;
        }

        memo.displayingAnswer = 0;

        requiredList = [];
        for (var i = 0; i < memo.selectedQuestionList.length; i++) {
            if (settings.showStatus == 1 && (memo.selectedQuestionList[i].status == 1 || memo.selectedQuestionList[i].status == 2)) {
                requiredList.push(memo.selectedQuestionList[i]);
            } else if (settings.showStatus == 2 && memo.selectedQuestionList[i].status == 2) {
                requiredList.push(memo.selectedQuestionList[i]);
            } else if (settings.showStatus == 3 && memo.selectedQuestionList[i].status == 3) {
                requiredList.push(memo.selectedQuestionList[i]);
            }
        }

        if (moveType == 0) {
            index = parseInt(Math.random() * requiredList.length);
            memo.questionId = requiredList[index].questionId;
            memo.question = requiredList[index].question;
            memo.answer = requiredList[index].answer;
            memo.questionStatus = requiredList[index].status;
        } else if (moveType == 1 || moveType == -1) {
            index = -1;
            for (var i = 0; i < requiredList.length; i++) {
                if (requiredList[i].questionId == memo.questionId) {
                    index = i;
                    break;
                }
            }
            if (index == -1) {
                memo.question = "";
                memo.answer = "Unknown error";
                ShowQuestion();
                return;
            }

            if (moveType == -1 && index > 0 || moveType == 1 && index < requiredList.length - 1) {
                index += moveType;
            } else if (moveType == -1 && index == 0) {
                index = requiredList.length - 1;
            } else if (moveType == 1 && index == requiredList.length - 1) {
                index = 0;
            }

            memo.questionId = requiredList[index].questionId;
            memo.question = requiredList[index].question;
            memo.answer = requiredList[index].answer;
            memo.questionStatus = requiredList[index].status;
        }

        setTimeout(ShowQuestion, 100);
    }
}

function AutoPlayer() {
    MemoMove("next");
}

function MemoStart() {
    $("#qa1").show();
    $("#qa2").hide();
    $("#statisticsQuestion").html("");
    $("#statisticsDetail").html("");
    if (settings.mode == 0) { // Switch mode
        startquestion = $("#start-from").val();
        if (startquestion == "") {
            DisplayRandomQuestion();
            startquestion = memo.question;
        }

        // User decided a question to start from
        // Get its question id
        $.ajax({
            url: '/api/question/id',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                question: startquestion,
                bookId: memo.bookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.questionId = r.questionId;

                // Question exist and get info of the question
                $.ajax({
                    url: '/api/question',
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        questionId: memo.questionId,
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        memo.questionId = r.questionId;
                        memo.question = r.question;
                        memo.answer = r.answer;
                        memo.questionStatus = r.status;

                        ShowQuestion();
                    },
                    error: function (r, textStatus, errorThrown) {
                        if (r.status == 401) {
                            SessionExpired();
                        } else {
                            NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                        }
                    }
                });
            },

            // Question doesn't exist then start from default
            error: function (r, textStatus, errorThrown) {
                if (r.status == 404) {
                    NotyNotification("Question to start from not found!", type = 'warning');
                    DisplayRandomQuestion();
                } else if (r.status == 401) {
                    SessionExpired();
                } else {
                    NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                }
            }
        });
    } else if (settings.mode == 1) { // Challenge mode
        $.ajax({
            url: '/api/question/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: memo.bookId,
                mixcnt: 0,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.questionId = r.questionId;
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;

                if (memo.questionId == -1) {
                    $("#challenge-yesno-control").hide();
                } else {
                    $("#challenge-yesno-control").show();
                }

                ShowQuestion();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    SessionExpired();
                } else {
                    NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                }
            }
        });
    } else if (settings.mode == 2) {
        $("#qa2").show();
        $("#qa1").hide();
        $(".challenge-choice-continue").hide();
        $.ajax({
            url: '/api/question/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: memo.bookId,
                mixcnt: 3,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.questionId = r.questionId;
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;

                choices = [];
                for (var i = 0; i < r.mix.length; i++) {
                    choices.push({
                        "question": r.mix[i].question,
                        "answer": r.mix[i].answer,
                        "correct": false
                    });
                }
                choices.push({
                    "question": memo.question,
                    "answer": memo.answer,
                    "correct": true
                });

                swap_to = parseInt(Math.random() * 1000 / 250);
                tmp = choices[swap_to];
                choices[swap_to] = choices[3];
                choices[3] = tmp;

                ccCorrect = swap_to;

                if (settings.swap == 0 || settings.swap == 2) {
                    $("#cc-question").val(memo.question);
                } else if (settings.swap == 1) {
                    $("#cc-question").val(memo.answer);
                }

                for (var i = 0; i < choices.length; i++) {
                    r = choices[i].answer;
                    if (settings.swap == 1) {
                        r = choices[i].question;
                    }
                    $("#choice-" + i).html(r);
                }

                ShowQuestion();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    SessionExpired();
                } else {
                    NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                }
            }
        });
    } else if (settings.mode == 3) { // Offline Mode
        if (memo.selectedQuestionList == []) {
            alert("Unable to start offline mode: No data in question list!");
            return;
        }

        if ($("#start-from").val() != "") {
            startquestion = $("#start-from").val();
            found = false;
            for (var i = 0; i < memo.selectedQuestionList.length; i++) {
                if (memo.selectedQuestionList[i].question == startquestion) {
                    memo.questionId = memo.selectedQuestionList[i].questionId;
                    memo.question = memo.selectedQuestionList[i].question;
                    memo.answer = memo.selectedQuestionList[i].answer;
                    memo.questionStatus = memo.selectedQuestionList[i].status;

                    found = true;
                }
            }
            if (!found) {
                $("#start-from").val("Not found!");
            }
        } else {
            index = parseInt(Math.random() * memo.selectedQuestionList.length);
            memo.questionId = memo.selectedQuestionList[index].questionId;
            memo.question = memo.selectedQuestionList[index].question;
            memo.answer = memo.selectedQuestionList[index].answer;
            memo.questionStatus = memo.selectedQuestionList[index].status;
        }

        ShowQuestion();
    }

    if (settings.mode != 1 && settings.mode != 2 && settings.autoPlay != 0) {
        settings.apinterval = setInterval(AutoPlayer, apdelay[settings.autoPlay] * 1000);
        $(".ap-btn").attr("onclick", "StopAutoPlayer()");
        $(".ap-btn").html('<i class="fa fa-pause-circle"></i> Pause');
        memo.speaker.cancel();
        msg = new SpeechSynthesisUtterance($("#question").val());
        memo.speaker.speak(msg);
    }
}

function MemoGo() {
    $("#start-btn").html("Go <i class='fa fa-spinner fa-spin'></i>");
    setTimeout(MemoStart, 50);
}

function MemoTag() {
    if (memo.questionStatus == 2) memo.questionStatus = 1;
    else if (memo.questionStatus == 1 || memo.questionStatus == 3) memo.questionStatus = 2;

    $.ajax({
        url: '/api/question/status/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify([memo.questionId]),
            status: memo.questionStatus,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (memo.questionStatus != 2) $(".memo-tag").html("Tag <i class='fa fa-star'></i>");
            else $(".memo-tag").html("Untag <i class='fa fa-star-o'></i>");
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

function MemoDelete() {
    if (memo.questionStatus == 3) memo.questionStatus = 1;
    else if (memo.questionStatus == 1 || memo.questionStatus == 2) memo.questionStatus = 3;

    $.ajax({
        url: '/api/question/status/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questions: JSON.stringify([memo.questionId]),
            status: memo.questionStatus,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (memo.questionStatus != 3) $(".memo-delete").html("Delete <i class='fa fa-trash'></i>");
            else $(".memo-delete").html("Undelete <i class='fa fa-undo'></i>");
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

function MemoChallenge(res) {
    if (memo.challengeStatus != 2 && res == "no") {
        memo.challengeStatus = 2;
        if (settings.swap == 0 || settings.swap == 2) {
            $("#answer").val(memo.answer);
        } else {
            $("#question").val(memo.question);
        }
        $("#challenge-msg").html("Try to memorize it!")
        $(".memo-challenge-yes").html("<i class='fa fa-arrow-circle-right'></i> Next");
        $(".memo-challenge-no").html("<i class='fa fa-arrow-circle-right'></i> Next");
        return;
    }

    if (memo.challengeStatus == 0 && res == "yes") {
        memo.challengeStatus = 1;
        if (settings.swap == 0 || settings.swap == 2) {
            $("#answer").val(memo.answer);
        } else {
            $("#question").val(memo.question);
        }
        $("#challenge-msg").html("Are you correct?");
    } else if (memo.challengeStatus == 1 && res == "yes") {
        $("#challenge-msg").html("Good job! <i class='fa fa-thumbs-up'></i>");

        $.ajax({
            url: '/api/question/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: memo.bookId,
                mixcnt: 0,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.questionId = r.questionId;
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;

                memo.challengeStatus = 0;
                $("#challenge-msg").html("Do you remember it?");
                ShowQuestion();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    SessionExpired();
                } else {
                    NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                }
            }
        });
    } else if (memo.challengeStatus == 2) {
        $(".memo-challenge-yes").html("Yes <i class='fa fa-check'></i>");
        $(".memo-challenge-no").html("No <i class='fa fa-times'></i>");
        $.ajax({
            url: '/api/question/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: memo.bookId,
                mixcnt: 0,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.questionId = r.questionId;
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;

                if (memo.questionId == -1) {
                    $("#challenge-control").hide();
                } else {
                    $("#challenge-control").show();
                }

                memo.challengeStatus = 0;
                $("#challenge-msg").html("Do you remember it?");
                ShowQuestion();
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

var ccAnswered = false;

function ChallengeChoice(choiceid) {
    $(".choice").css("background", "#ff5555");
    $("#div-choice-" + ccCorrect).css("background", "#55ff55");
    $("#choice-circle-" + choiceid).css("background", "#333333");

    if (choiceid == -1 || ccAnswered) {
        ccAnswered = false;
        $(".challenge-choice-continue").hide();
        $.ajax({
            url: '/api/question/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: memo.bookId,
                mixcnt: 3,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.questionId = r.questionId;
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;

                choices = [];
                for (var i = 0; i < r.mix.length; i++) {
                    choices.push({
                        "question": r.mix[i].question,
                        "answer": r.mix[i].answer,
                        "correct": false
                    });
                }
                choices.push({
                    "question": memo.question,
                    "answer": memo.answer,
                    "correct": true
                });

                swap_to = parseInt(Math.random() * 1000 / 250);
                tmp = choices[swap_to];
                choices[swap_to] = choices[3];
                choices[3] = tmp;

                ccCorrect = swap_to;

                if (settings.swap == 0 || settings.swap == 2) {
                    $("#cc-question").val(memo.question);
                } else if (settings.swap == 1) {
                    $("#cc-question").val(memo.answer);
                }

                for (var i = 0; i < choices.length; i++) {
                    r = choices[i].answer;
                    if (settings.swap == 1) {
                        r = choices[i].question;
                    }
                    $("#choice-" + i).html(r);
                }

                $(".choice").css("background", "transparent");
                $(".choice-circle").css("background", "#dddddd");

                ShowQuestion();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    SessionExpired();
                } else {
                    NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
                }
            }
        });
        return;
    }

    ccAnswered = true;

    if (choiceid == ccCorrect) {
        chtoday += 1;
        $("#goal-progress").css("width", Math.min(chtoday / goal * 100, 100) + "%");
        $("#today-goal").html(chtoday + " / " + goal);

        if (checkin_today || chtoday < goal) {
            $("#checkin-btn").attr("disabled", "disabled");
            if (checkin_today) {
                $("#checkin-btn").html('<i class="fa fa-check-square"></i>');
            }
        } else {
            $("#checkin-btn").removeAttr("disabled");
        }

        ccCorrectAudio.pause();
        ccCorrectAudio.currentTime = 0;
        ccCorrectAudio.play();
        $(".challenge-choice-continue").hide();
        $.ajax({
            url: '/api/question/challenge/update',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                questionId: memo.questionId,
                memorized: 1,
                getNext: 1,
                mixcnt: 3,
                bookId: memo.bookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                setTimeout(function () {
                    ccAnswered = false;
                    memo.questionId = r.questionId;
                    memo.question = r.question;
                    memo.answer = r.answer;
                    memo.questionStatus = r.status;

                    choices = [];
                    for (var i = 0; i < r.mix.length; i++) {
                        choices.push({
                            "question": r.mix[i].question,
                            "answer": r.mix[i].answer,
                            "correct": false
                        });
                    }
                    choices.push({
                        "question": memo.question,
                        "answer": memo.answer,
                        "correct": true
                    });

                    swap_to = parseInt(Math.random() * 1000 / 250);
                    tmp = choices[swap_to];
                    choices[swap_to] = choices[3];
                    choices[3] = tmp;

                    ccCorrect = swap_to;

                    if (settings.swap == 0 || settings.swap == 2) {
                        $("#cc-question").val(memo.question);
                    } else if (settings.swap == 1) {
                        $("#cc-question").val(memo.answer);
                    }

                    for (var i = 0; i < choices.length; i++) {
                        r = choices[i].answer;
                        if (settings.swap == 1) {
                            r = choices[i].question;
                        }
                        $("#choice-" + i).html(r);
                    }

                    $(".choice").css("background", "transparent");
                    $(".choice-circle").css("background", "#dddddd");
                    ShowQuestion();
                }, 500);
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
        ccWrongAudio.pause();
        ccWrongAudio.currentTime = 0;
        ccWrongAudio.play();
        $(".challenge-choice-continue").show();
        $.ajax({
            url: '/api/question/challenge/update',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                questionId: memo.questionId,
                memorized: 0,
                getNext: 0,
                mixcnt: 0,
                bookId: memo.bookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
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

function Statistics() {
    $.ajax({
        url: '/api/question/stat',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            questionId: memo.questionId,
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
                            <h5 class="modal-title" id="modalLabel">Statistics of ` + memo.question + `</h5>
                            <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                                onclick="$('#modal').modal('hide')">
                                <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p>` + statistics + `</p>
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
            if (r.status == 401) {
                SessionExpired();
            } else {
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
            }
        }
    });
}

function EditQuestionShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLabel">Edit Question</h5>
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
                    <button type="button" class="btn btn-primary" onclick="EditQuestion()">Edit</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#edit-question").val(memo.question);
    $("#edit-answer").val(memo.answer);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });

    $("#edit-question,#edit-answer").on('keypress', function (e) {
        if (e.which == 13 && e.ctrlKey) {
            EditQuestion();
        }
    });
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
            questionId: memo.questionId,
            question: question,
            answer: answer,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            memo.question = question;
            memo.answer = answer;

            if (settings.swap == 0 || settings.swap == 2 && settings.mode == 1) {
                $("#question").val(memo.question);
                $("#answer").val("");
            } else if (settings.swap == 1) {
                $("#question").val("");
                $("#answer").val(memo.answer);
            } else if (settings.swap == 2 && settings.mode != 1 && settings.mode != 2) {
                $("#question").val(memo.question);
                $("#answer").val(memo.answer);
            }

            if (r.success == true) {
                NotyNotification(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }

            $("#editQuestionModal").modal('hide');
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

function SpeakQuestion() {
    memo.speaker.cancel();
    msg = new SpeechSynthesisUtterance($("#question").val());
    memo.speaker.speak(msg);
}

function SpeakAnswer() {
    memo.speaker.cancel();
    msg = new SpeechSynthesisUtterance($("#answer").val());
    memo.speaker.speak(msg);
}

function StopAutoPlayer() {
    settings.apinterval = clearInterval(settings.apinterval); // this will make it undefined
    $(".ap-btn").attr("onclick", "ResumeAutoPlayer()");
    $(".ap-btn").html('<i class="fa fa-play-circle"></i> Resume');
}

function ResumeAutoPlayer() {
    settings.apinterval = setInterval(AutoPlayer, apdelay[settings.autoPlay] * 1000);
    $(".ap-btn").attr("onclick", "StopAutoPlayer()");
    $(".ap-btn").html('<i class="fa fa-pause-circle"></i> Pause');
}

function BackToHome() {
    memo.started = false;
    $(".title").hide();
    $("#memo").hide();
    $("#home").fadeIn();
    StopAutoPlayer();
}

function SelectBook(bookId) {
    memo.bookId = bookId;
    localStorage.setItem("memo-book-id", memo.bookId);
    UpdateSelectedQuestionList();
    UpdateBookDisplay();
}

function CheckIn() {
    $.ajax({
        url: "/api/user/checkin",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification(r.msg, type = 'success');
                $("#checkin-btn").html('<i class="fa fa-check-square"></i>');
                $("#checkin-btn").attr("disabled", "disabled");
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