// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

class MemoClass {
    constructor() {
        this.questionId = 0;
        this.question = "";
        this.answer = "";
        this.questionStatus = 0;
        this.practiceStatus = 0;
        this.challengeToken = 0;
        this.chocies = 0;

        this.bookId = 0;
        this.bookName = "";
        this.bookList = [];

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

var goal = 0;
var chtoday = 0;
memo = new MemoClass();
memo.questionId = parseInt(lsGetItem("memo-question-id", 0));
memo.bookId = parseInt(lsGetItem("memo-book-id", 0));
memo.bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
memo.bookName = lsGetItem("memo-book-name", "");
function UpdateBookName(){
    memo.bookList = JSON.parse(lsGetItem("book-list", JSON.stringify([])));
    if(memo.bookList == []){
        memo.bookId = 0;
        memo.bookName = "All questions";
        $("#book-name").html(memo.bookName);
        return;
    }
    found = false;
    for (var i = 0; i < memo.bookList.length; i++) {
        if (memo.bookList[i].bookId == memo.bookId) {
            memo.bookName = memo.bookList[i].name;
            $("#book-name").html(memo.bookName);
            localStorage.setItem("memo-book-name", memo.bookName);
            found = true;
        }
    }
    if (!found) {
        memo.bookId = 0;
        localStorage.setItem("memo-book-id", 0);
        memo.bookName = memo.bookList[0].name;
        $("#book-name").html(memo.bookName);
        localStorage.setItem("memo-book-name", memo.bookName);
    }
}
UpdateBookName();
setInterval(function () {
    UpdateBookName();
}, 5000); // this will be updated by general.js

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

function PageInit() {
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        $("#home").css("line-height", "85%");
    } else {
        $("#home").css("line-height", "65%");
    }
    l = ["Switch", "Practice", "Challenge", "Offline"];
    $("#mode").html(l[settings.mode]);
    $("#book-name").html(memo.bookName);

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
        $("#switch-control").show();
        $("#statistics-btn").show();
        $("#edit-btn").show();
    } else if (settings.mode == 1) {
        $("#practice-control").show();
        $("#statistics-btn").hide();
        $("#edit-btn").hide();
    } else if (settings.mode == 2) {
        $("#challenge-control").show();
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
    if (settings.apinterval == -1 || settings.mode >= 1) {
        $(".ap-btn").hide();
    } else {
        $(".ap-btn").show();
    }

    $("#start-btn").html("Go <i class='fa fa-play'></i>");
}

function DisplayAnswer() {
    if (memo.started) {
        if (settings.mode == 0) {
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
    if (settings.mode == 0 || settings.mode == 1) {
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
                if (!r.success) {
                    NotyNotification(r.msg, 'warning', 5000);
                    return;
                }
                memo.question = r.question;
                memo.answer = r.answer;
                memo.questionStatus = r.status;
                memo.questionId = r.questionId;
                ShowQuestion();
                if (settings.mode == 1) {
                    memo.practiceStatus = 0;
                    $("#practice-msg").html("Do you remember it?");
                }
            },
            error: function (r, textStatus, errorThrown) {
                AjaxErrorHandler(r, textStatus, errorThrown);
            }
        });
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
                        $("#start-btn").html("Go <i class='fa fa-play'></i>");
                        if (!r.success) {
                            NotyNotification(r.msg, 'warning', 5000);
                            return;
                        }
                        memo.questionId = r.questionId;
                        memo.question = r.question;
                        memo.answer = r.answer;
                        memo.questionStatus = r.status;

                        ShowQuestion();
                    },
                    error: function (r, textStatus, errorThrown) {
                        AjaxErrorHandler(r, textStatus, errorThrown);
                    }
                });
            },

            // Question doesn't exist then start from default
            error: function (r, textStatus, errorThrown) {
                if (r.status == 404) {
                    NotyNotification("Question to start from not found!", type = 'warning');
                    DisplayRandomQuestion();
                } else {
                    AjaxErrorHandler(r, textStatus, errorThrown);
                }
            }
        });
    } else if (settings.mode == 1) { // Practice mode
        startquestion = $("#start-from").val();

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
                        $("#start-btn").html("Go <i class='fa fa-play'></i>");
                        if (!r.success) {
                            NotyNotification(r.msg, 'warning', 5000);
                            return;
                        }
                        memo.questionId = r.questionId;
                        memo.question = r.question;
                        memo.answer = r.answer;
                        memo.questionStatus = r.status;

                        if (memo.questionId == -1) {
                            $("#practice-control").hide();
                        } else {
                            $("#practice-control").show();
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
            },

            // Question doesn't exist then start from default
            error: function (r, textStatus, errorThrown) {
                if (r.status == 404) {
                    NotyNotification("Question to start from not found!", type = 'warning');
                    DisplayRandomQuestion();
                } else {
                    AjaxErrorHandler(r, textStatus, errorThrown);
                }
            }
        });
    } else if (settings.mode == 2) { // Challenge mode
        $("#qa2").show();
        $("#qa1").hide();
        $.ajax({
            url: '/api/question/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                bookId: memo.bookId,
                swapqa: settings.swap,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                $("#start-btn").html("Go <i class='fa fa-play'></i>");
                if (!r.success) {
                    NotyNotification(r.msg, 'warning', 5000);
                    return;
                }
                ccAnswered = false;
                $("#challenge-msg").html("Select your answer <i class='fa fa-arrow-up'></i>");
                $(".choice").css("background", "transparent");
                $(".choice-circle").css("background", "#dddddd");

                memo.questionId = -1;
                memo.question = r.question;
                memo.answer = "";
                memo.questionStatus = r.status;
                memo.choices = r.choices;
                $("#cc-question").val(memo.question);
                for (var i = 0; i < memo.choices.length; i++)
                    $("#choice-" + i).html(memo.choices[i]);
                memo.challengeToken = r.challengeToken;
                ShowQuestion();
            },
            error: function (r, textStatus, errorThrown) {
                AjaxErrorHandler(r, textStatus, errorThrown);
            }
        });
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
            AjaxErrorHandler(r, textStatus, errorThrown);
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
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function MemoPractice(res) {
    if (memo.practiceStatus != 2 && res == "no") {
        memo.practiceStatus = 2;
        if (settings.swap == 0 || settings.swap == 2) {
            $("#answer").val(memo.answer);
        } else {
            $("#question").val(memo.question);
        }
        $("#practice-msg").html("Try to memorize it!")
        $(".memo-practice-yes").html("<i class='fa fa-arrow-circle-right'></i> Next");
        $(".memo-practice-no").html("<i class='fa fa-arrow-circle-right'></i> Next");
        return;
    }

    if (memo.practiceStatus == 0 && res == "yes") {
        memo.practiceStatus = 1;
        if (settings.swap == 0 || settings.swap == 2) {
            $("#answer").val(memo.answer);
        } else {
            $("#question").val(memo.question);
        }
        $("#practice-msg").html("Are you correct?");
    } else if (memo.practiceStatus == 1 && res == "yes") {
        $("#practice-msg").html("Good job! <i class='fa fa-thumbs-up'></i>");
        MemoMove("next");
    } else if (memo.practiceStatus == 2) {
        $(".memo-practice-yes").html("Yes <i class='fa fa-check'></i>");
        $(".memo-practice-no").html("No <i class='fa fa-times'></i>");
        MemoMove("next");
    }
}

var ccAnswered = false;

function ChallengeChoice(choiceid) {
    if (ccAnswered) {
        ccAnswered = false;
        $("#cc-question").val(memo.question);
        for (var i = 0; i < memo.choices.length; i++)
            $("#choice-" + i).html(memo.choices[i]);
        $("#challenge-msg").html("Select your answer <i class='fa fa-arrow-up'></i>");
        ShowQuestion();
        $(".choice").css("background", "transparent");
        $(".choice-circle").css("background", "#dddddd");
        return;
    }

    $("#choice-circle-" + choiceid).css("background", "#333333");
    if (localStorage.getItem("settings-theme") == "dark") {
        $("#choice-circle-" + choiceid).css("background", "#888888");
    }
    choiceid += 1;

    $("#challenge-msg").html("Checking your answer... <i class='fa fa-spinner fa-spin'></i>");
    ccAnswered = true;
    $.ajax({
        url: '/api/question/challenge/check',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            challengeToken: memo.challengeToken,
            answer: choiceid,
            getNext: 1,
            bookId: memo.bookId,
            swapqa: settings.swap,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            $(".choice").css("background", "#ff5555");
            $("#div-choice-" + (r.correct - 1)).css("background", "#55ff55");

            if (r.result == true) {
                $("#challenge-msg").html("Answer correct <i class='fa fa-check'></i>");
                if (r.expired == true) {
                    $("#challenge-msg").html("Answer is correct but challenge has expired!");
                    NotyNotification("Challenge expired!", 'warning');
                }

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

                setTimeout(function () {
                    ccAnswered = false;
                    memo.questionId = -1;
                    memo.question = r.question;
                    memo.answer = "";
                    memo.questionStatus = r.status;
                    memo.choices = r.choices;
                    $("#cc-question").val(memo.question);
                    for (var i = 0; i < memo.choices.length; i++)
                        $("#choice-" + i).html(memo.choices[i]);
                    memo.challengeToken = r.challengeToken;
                    $("#challenge-msg").html("Select your answer <i class='fa fa-arrow-up'></i>");
                    ShowQuestion();
                    $(".choice").css("background", "transparent");
                    $(".choice-circle").css("background", "#dddddd");
                }, 500)
            } else {
                $("#challenge-msg").html("Wrong answer <i class='fa fa-times'></i>");
                if (r.expired == true) {
                    NotyNotification("Challenge expired!", 'warning');
                    $("#challenge-msg").html("Answer is wrong and challenge has expired!");
                }
                ccWrongAudio.pause();
                ccWrongAudio.currentTime = 0;
                ccWrongAudio.play();
                memo.questionId = -1;
                memo.question = r.question;
                memo.answer = "";
                memo.questionStatus = r.status;
                memo.choices = r.choices;
                memo.challengeToken = r.challengeToken;
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
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
            AjaxErrorHandler(r, textStatus, errorThrown);
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

    $("#edit-question,#edit-answer").keypress(function (e) {
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
            AjaxErrorHandler(r, textStatus, errorThrown);
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
    for (var i = 0; i < memo.bookList.length; i++) {
        if (memo.bookList[i].bookId == memo.bookId) {
            memo.bookName = memo.bookList[i].name;
            $("#book-name").html(memo.bookName);
            localStorage.setItem("memo-book-name", memo.bookName);
        }
    }
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
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}