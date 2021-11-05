// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

function lsGetItem(lsItemName, defaultValue = 0) {
    if (localStorage.getItem(lsItemName) == null) {
        localStorage.setItem(lsItemName, defaultValue);
        return defaultValue;
    } else {
        return localStorage.getItem(lsItemName);
    }
}

class MemoClass {
    constructor() {
        this.wordId = 0;
        this.word = "";
        this.translation = "";
        this.wordStatus = 0;
        this.challengeStatus = 0;

        this.wordBookId = 0;
        this.wordBookName = "";

        this.fullWordList = [];
        this.wordListMap = null;
        this.wordBookList = [];
        this.selectedWordList = [];

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

memo = new MemoClass();
memo.wordId = parseInt(lsGetItem("memo-word-id", 0));
memo.wordBookId = parseInt(lsGetItem("memo-word-book-id", 0));
memo.fullWordList = JSON.parse(lsGetItem("word-list", JSON.stringify([])));
memo.wordBookList = JSON.parse(lsGetItem("word-book-list", JSON.stringify([])));

settings = new SettingsClass();
settings.random = parseInt(lsGetItem("settings-random", 0));
settings.swap = parseInt(lsGetItem("settings-swap", 0));
settings.showStatus = parseInt(lsGetItem("settings-show-status", 1));
settings.mode = parseInt(lsGetItem("settings-mode", 0));
settings.autoPlay = parseInt(lsGetItem("settings-auto-play", 0));
settings.apinterval = -1;
settings.firstuse = parseInt(lsGetItem("first-use", 1));



function MapWordList() {
    memo.wordListMap = new Map();
    for (var i = 0; i < memo.wordList.length; i++) {
        memo.wordListMap.set(memo.wordList[i].wordId, {
            "word": memo.wordList[i].word,
            "translation": memo.wordList[i].translation,
            "status": memo.wordList[i].status
        });
    }
}

function UpdateSelectedWordList() {
    for (var i = 0; i < memo.wordBookList.length; i++) {
        if (memo.wordBookList[i].wordBookId == memo.wordBookId) {
            memo.wordBookName = memo.wordBookList[i].name;
            $("#word-book").html(memo.wordBookName);
            memo.selectedWordList = [];
            for (this.j = 0; j < memo.wordBookList[i].words.length; j++) {
                wordId = memo.wordBookList[i].words[j];
                wordData = memo.wordListMap.get(wordId);
                memo.selectedWordList.push({
                    "wordId": wordId,
                    "word": wordData.word,
                    "translation": wordData.translation,
                    "status": wordData.status
                });
            }
        }
    }
}

function GoToUser() {
    window.location.href = "/user"
}

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

function UpdateWordList(doasync = true) {
    $.ajax({
        url: "/api/wordBook/wordList",
        method: 'POST',
        async: doasync,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            memo.wordList = r;
            localStorage.setItem("word-list", JSON.stringify(memo.wordList));
            MapWordList();
        }
    });
}

function UpdateWordBookList(doasync = true) {
    $.ajax({
        url: "/api/wordBook",
        method: 'POST',
        async: doasync,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            memo.wordBookList = r;
            localStorage.setItem("word-book-list", JSON.stringify(memo.wordBookList));
            UpdateSelectedWordList();
        }
    });
}

function UpdateHomePage() {
    l = ["Practice", "Challenge", "Offline"];
    $("#mode").html(l[settings.mode]);

    if (localStorage.getItem("username") != null) {
        $("#username").html(localStorage.getItem("username"));
    }
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
            $("#username").html(r.username);
            localStorage.setItem("username", r.username);
        }
    });

    UpdateWordList(doasync = false);
    UpdateWordBookList(doasync = false);

    $("#word-book").html(memo.wordBookName);
}

function DisplayRandomWord() {
    if (!$("#start-from").is(":focus") && !memo.started && memo.selectedWordList.length != 0) {
        index = parseInt(Math.random() * memo.selectedWordList.length);
        memo.wordId = memo.selectedWordList[index].wordId;
        memo.word = memo.selectedWordList[index].word;
        memo.translation = memo.selectedWordList[index].translation;
        memo.wordStatus = memo.selectedWordList[index].status;

        $("#start-from").val(memo.word);
    }
}
setInterval(DisplayRandomWord, 3000);

function ShowWord() {
    if (settings.firstuse) {
        new Noty({
            theme: 'mint',
            text: 'Hint: You can click the word to hear its sound',
            type: 'info',
            layout: 'bottomRight',
            timeout: 10000
        }).show();
        localStorage.setItem("first-use", 0);
        settings.firstuse = false;
    }
    if (settings.swap == 0 || settings.swap == 2 && settings.mode == 1) {
        $("#word").val(memo.word);
        $("#translation").val("");
    } else if (settings.swap == 1) {
        $("#word").val("");
        $("#translation").val(memo.translation);
    } else if (settings.swap == 2 && settings.mode != 1) {
        $("#word").val(memo.word);
        $("#translation").val(memo.translation);
    }
    if (settings.autoPlay != 0) {
        $(".ap-btn").show();
    }
    $(".memo-tag").html("Tag <i class='fa fa-star'></i>");
    $(".memo-delete").html("Delete <i class='fa fa-trash'></i>");
    if (memo.wordStatus == 2) {
        $(".memo-tag").html("Untag <i class='fa fa-star-o'></i>");
    } else if (memo.wordStatus == 3) {
        $(".memo-delete").html("Undelete <i class='fa fa-undo'></i>");
    }
    $("#home").hide();
    $("#memo").show();
    $(".control").hide();
    if (settings.mode == 0) {
        $("#practice-control").show();
        $("#statistics-btn").show();
        $("#edit-btn").show();
    } else if (settings.mode == 1) {
        $("#challenge-control").show();
        $("#statistics-btn").show();
        $("#edit-btn").hide();
    } else if (settings.mode == 2) {
        $("#offline-control").show();
        $("#statistics-btn").hide();
        $("#edit-btn").hide();
    }

    memo.displayingAnswer = 0;
    memo.started = true;

    if (settings.apinterval != -1 && settings.mode != 1) {
        memo.speaker.cancel();
        msg = undefined;
        if (settings.swap != 1 || settings.swap == 1 && memo.displayingAnswer) {
            msg = new SpeechSynthesisUtterance($("#word").val());
        } else {
            msg = new SpeechSynthesisUtterance($("#translation").val());
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
    if (memo.started && settings.mode != 1) {
        if (settings.swap == 0) {
            if (!memo.displayingAnswer) $("#translation").val(memo.translation);
            else $("#translation").val("");
        } else if (settings.swap == 1) {
            if (!memo.displayingAnswer) $("#word").val(memo.word);
            else $("#word").val("");
        }
        memo.displayingAnswer = 1 - memo.displayingAnswer;
    }
    if (!memo.started) {
        $("#wordbook").animate({
            left: "-60%"
        }, {
            queue: false,
            duration: 500
        });
    }
}

function MemoMove(direction) {
    $("#statisticsWord").html("");
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
            url: '/api/word/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                wordId: memo.wordId,
                status: settings.showStatus,
                moveType: moveType,
                wordBookId: memo.wordBookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.word = r.word;
                memo.translation = r.translation;
                memo.wordStatus = r.status;
                memo.wordId = r.wordId;
                ShowWord();
            },
            error: function (r, textStatus, errorThrown) {
                if (r.status == 401) {
                    SessionExpired();
                } else {
                    memo.word = r.status + " " + errorThrown;
                    memo.translation = "Maybe change the settings?\nOr check your connection?";
                    ShowWord();
                }
            }
        });
    } else if (settings.mode == 2) {
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
        for (var i = 0; i < memo.selectedWordList.length; i++) {
            if (settings.showStatus == 1 && (memo.selectedWordList[i].status == 1 || memo.selectedWordList[i].status == 2)) {
                requiredList.push(memo.selectedWordList[i]);
            } else if (settings.showStatus == 2 && memo.selectedWordList[i].status == 2) {
                requiredList.push(memo.selectedWordList[i]);
            } else if (settings.showStatus == 3 && memo.selectedWordList[i].status == 3) {
                requiredList.push(memo.selectedWordList[i]);
            }
        }

        if (moveType == 0) {
            index = parseInt(Math.random() * requiredList.length);
            memo.wordId = requiredList[index].wordId;
            memo.word = requiredList[index].word;
            memo.translation = requiredList[index].translation;
            memo.wordStatus = requiredList[index].status;
        } else if (moveType == 1 || moveType == -1) {
            index = -1;
            for (var i = 0; i < requiredList.length; i++) {
                if (requiredList[i].wordId == memo.wordId) {
                    index = i;
                    break;
                }
            }
            if (index == -1) {
                memo.word = "";
                memo.translation = "Unknown error";
                ShowWord();
                return;
            }

            if (moveType == -1 && index > 0 || moveType == 1 && index < requiredList.length - 1) {
                index += moveType;
            } else if (moveType == -1 && index == 0) {
                index = requiredList.length - 1;
            } else if (moveType == 1 && index == requiredList.length - 1) {
                index = 0;
            }

            memo.wordId = requiredList[index].wordId;
            memo.word = requiredList[index].word;
            memo.translation = requiredList[index].translation;
            memo.wordStatus = requiredList[index].status;
        }

        ShowWord();
    }
}

function AutoPlayer() {
    MemoMove("next");
}

function MemoStart() {
    $("#statisticsWord").html("");
    $("#statisticsDetail").html("");
    if (settings.mode == 0) { // Practice mode
        startword = $("#start-from").val();
        if (startword == "") {
            DisplayRandomWord();
            startword = memo.word;
        }

        // User decided a word to start from
        // Get its word id
        $.ajax({
            url: '/api/word/id',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                word: startword,
                wordBookId: memo.wordBookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.wordId = r.wordId;

                // Word exist and get info of the word
                $.ajax({
                    url: '/api/word',
                    method: 'POST',
                    async: true,
                    dataType: "json",
                    data: {
                        wordId: memo.wordId,
                        userId: localStorage.getItem("userId"),
                        token: localStorage.getItem("token")
                    },
                    success: function (r) {
                        memo.wordId = r.wordId;
                        memo.word = r.word;
                        memo.translation = r.translation;
                        memo.wordStatus = r.status;

                        ShowWord();
                    },
                    error: function (r, textStatus, errorThrown) {
                        if (r.status == 401) {
                            SessionExpired();
                        } else {
                            memo.word = r.status + " " + errorThrown;
                            memo.translation = "Maybe change the settings?\nOr check your connection?";

                            ShowWord();
                        }
                    }
                });
            },

            // Word doesn't exist then start from default
            error: function (r, textStatus, errorThrown) {
                if (r.status == 404) {
                    $("#start-from").val("Not found!");
                    DisplayRandomWord();
                } else if (r.status == 401) {
                    SessionExpired();
                } else {
                    memo.word = r.status + " " + errorThrown;
                    memo.translation = "Maybe change the settings?\nOr check your connection?";

                    ShowWord();
                }
            }
        });
    } else if (settings.mode == 1) { // Challenge mode
        $.ajax({
            url: '/api/word/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                wordBookId: memo.wordBookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.wordId = r.wordId;
                memo.word = r.word;
                memo.translation = r.translation;
                memo.wordStatus = r.status;
                
                if(memo.wordId == -1){
                    $("#challenge-control").hide();
                } else {
                    $("#challenge-control").show();
                }

                ShowWord();
            },
            error: function (r) {
                if (r.status == 401) {
                    SessionExpired();
                }
            }
        });
    } else if (settings.mode == 2) { // Offline Mode
        if (memo.selectedWordList == []) {
            alert("Unable to start offline mode: No data in word list!");
            return;
        }

        if ($("#start-from").val() != "") {
            startword = $("#start-from").val();
            found = false;
            for (var i = 0; i < memo.selectedWordList.length; i++) {
                if (memo.selectedWordList[i].word == startword) {
                    memo.wordId = memo.selectedWordList[i].wordId;
                    memo.word = memo.selectedWordList[i].word;
                    memo.translation = memo.selectedWordList[i].translation;
                    memo.wordStatus = memo.selectedWordList[i].status;

                    found = true;
                }
            }
            if (!found) {
                $("#start-from").val("Not found!");
            }
        } else {
            index = parseInt(Math.random() * memo.selectedWordList.length);
            memo.wordId = memo.selectedWordList[index].wordId;
            memo.word = memo.selectedWordList[index].word;
            memo.translation = memo.selectedWordList[index].translation;
            memo.wordStatus = memo.selectedWordList[index].status;
        }

        ShowWord();
    }

    if (settings.mode != 1 && settings.autoPlay != 0) {
        settings.apinterval = setInterval(AutoPlayer, apdelay[settings.autoPlay] * 1000);
        $(".ap-btn").attr("onclick", "StopAutoPlayer()");
        $(".ap-btn").html('<i class="fa fa-pause-circle"></i> Pause');
        memo.speaker.cancel();
        msg = new SpeechSynthesisUtterance($("#word").val());
        memo.speaker.speak(msg);
    }
}

function MemoGo() {
    $("#start-btn").html("Go <i class='fa fa-spinner fa-spin'></i>");
    setTimeout(MemoStart, 50);
}

function MemoTag() {
    if (memo.wordStatus == 2) memo.wordStatus = 1;
    else if (memo.wordStatus == 1 || memo.wordStatus == 3) memo.wordStatus = 2;

    $.ajax({
        url: '/api/word/status/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            words: JSON.stringify([memo.wordId]),
            status: memo.wordStatus,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (memo.wordStatus != 2) $(".memo-tag").html("Tag <i class='fa fa-star'></i>");
            else $(".memo-tag").html("Untag <i class='fa fa-star-o'></i>");
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function MemoDelete() {
    if (memo.wordStatus == 3) memo.wordStatus = 1;
    else if (memo.wordStatus == 1 || memo.wordStatus == 2) memo.wordStatus = 3;

    $.ajax({
        url: '/api/word/status/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            words: JSON.stringify([memo.wordId]),
            status: memo.wordStatus,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (memo.wordStatus != 3) $(".memo-delete").html("Delete <i class='fa fa-trash'></i>");
            else $(".memo-delete").html("Undelete <i class='fa fa-undo'></i>");
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function MemoChallenge(res) {
    if (memo.challengeStatus != 2 && res == "no") {
        memo.challengeStatus = 2;
        $("#translation").val(memo.translation);
        $("#challenge-msg").html("Try to memorize it!")
        $(".memo-challenge-yes").html("<i class='fa fa-arrow-circle-right'></i> Next");
        $(".memo-challenge-no").html("<i class='fa fa-arrow-circle-right'></i> Next");
        $.ajax({
            url: '/api/word/challenge/update',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                wordId: memo.wordId,
                memorized: 0,
                getNext: 0,
                wordBookId: memo.wordBookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
        });
        return;
    }

    if (memo.challengeStatus == 0 && res == "yes") {
        memo.challengeStatus = 1;
        $("#translation").val(memo.translation);
        $("#challenge-msg").html("Are you correct?");
    } else if (memo.challengeStatus == 1 && res == "yes") {
        $("#challenge-msg").html("Good job! <i class='fa fa-thumbs-up'></i>");

        $.ajax({
            url: '/api/word/challenge/update',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                wordId: memo.wordId,
                memorized: 1,
                getNext: 1,
                wordBookId: memo.wordBookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.wordId = r.wordId;
                memo.word = r.word;
                memo.translation = r.translation;
                memo.wordStatus = r.status;

                memo.challengeStatus = 0;
                $("#challenge-msg").html("Do you remember it?");
                ShowWord();
            },
            error: function (r) {
                if (r.status == 401) {
                    SessionExpired();
                }
            }
        });
    } else if (memo.challengeStatus == 2) {
        $(".memo-challenge-yes").html("Yes <i class='fa fa-check'></i>");
        $(".memo-challenge-no").html("No <i class='fa fa-times'></i>");
        $.ajax({
            url: '/api/word/challenge/next',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                wordBookId: memo.wordBookId,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                memo.wordId = r.wordId;
                memo.word = r.word;
                memo.translation = r.translation;
                memo.wordStatus = r.status;

                if(memo.wordId == -1){
                    $("#challenge-control").hide();
                } else {
                    $("#challenge-control").show();
                }

                memo.challengeStatus = 0;
                $("#challenge-msg").html("Do you remember it?");
                ShowWord();
            },
            error: function (r) {
                if (r.status == 401) {
                    SessionExpired();
                }
            }
        });
    }
}

function Statistics() {
    if ($("#statisticsWord").text() == memo.word) {
        $('#statisticsModal').modal('toggle')
        return;
    }
    $.ajax({
        url: '/api/word/stat',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            wordId: memo.wordId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            statistics = r.msg.replaceAll("\n", "<br>");

            $("#statisticsWord").html(memo.word);
            $("#statisticsDetail").html(statistics);

            $('#statisticsModal').modal('toggle')
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function EditWordShow() {
    $("#edit-word").val(memo.word);
    $("#edit-translation").val(memo.translation);
    $("#editWordModal").modal('toggle');
}

function EditWord() {
    word = $("#edit-word").val();
    translation = $("#edit-translation").val();
    $.ajax({
        url: '/api/word/edit',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            wordId: memo.wordId,
            word: word,
            translation: translation,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            memo.word = word;
            memo.translation = translation;

            if (settings.swap == 0 || settings.swap == 2 && settings.mode == 1) {
                $("#word").val(memo.word);
                $("#translation").val("");
            } else if (settings.swap == 1) {
                $("#word").val("");
                $("#translation").val(memo.translation);
            } else if (settings.swap == 2 && settings.mode != 1) {
                $("#word").val(memo.word);
                $("#translation").val(memo.translation);
            }

            new Noty({
                theme: 'mint',
                text: 'Success! Word edited!',
                type: 'success',
                layout: 'bottomRight',
                timeout: 3000
            }).show();

            $("#editWordModal").modal('toggle');
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function SpeakWord() {
    if (settings.swap != 1 || settings.swap == 1 && memo.displayingAnswer) {
        memo.speaker.cancel();
        msg = new SpeechSynthesisUtterance($("#word").val());
        memo.speaker.speak(msg);
    }
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
    $("#memo").hide();
    $("#home").show();
    StopAutoPlayer();
}

function Settings() {
    window.location.href = '/settings';
    StopAutoPlayer();
}

function UpdateWordBookDisplay() {
    $(".wordbook").remove();
    $("#wordbook-list").append('<div class="wordbook">\
        <p>Create Word Book: </p>\
        <div class="input-group mb-3 w-75">\
            <span class="input-group-text" id="basic-addon1">Name</span>\
            <input type="text" class="form-control" id="create-word-book-name" aria-describedby="basic-addon1">\
            <div class="input-group-append">\
                <button class="btn btn-outline-primary" type="button" onclick="CreateWordBook()">Create</button>\
            </div>\
        </div>\
        </div>');
    for (var i = 0; i < memo.wordBookList.length; i++) {
        wordBook = memo.wordBookList[i];
        wcnt = "";
        if (wordBook.wordBookId == 0) {
            wcnt = wordBook.words.length + ' words';
        } else {
            wcnt = wordBook.progress + ' memorized / ' + wordBook.words.length + ' words';
        }
        btn = "";
        if (wordBook.wordBookId != memo.wordBookId) {
            btn = '<button type="button" class="btn btn-primary " onclick="SelectWordBook(' + wordBook.wordBookId + ')">Select</button>';
        } else {
            btn = '<button type="button" class="btn btn-secondary">Selected</button>'
        }

        $("#wordbook-list").append('<div class="wordbook">\
        <p>' + wordBook.name + '</p>\
        <p>' + wcnt + '</p>\
        <button type="button" class="btn btn-primary " onclick="OpenWordBook(' + wordBook.wordBookId + ')">Open</button>\
        ' + btn + '\
        <hr>\
        </div>');
    }
}

function ShowWordBook() {
    $("#wordbook").animate({
        left: '0'
    }, {
        queue: false,
        duration: 500
    });
    UpdateWordBookDisplay();
}

function OpenWordBook(wordBookId) {
    window.location.href = '/wordbook?wordBookId=' + wordBookId;
}

function SelectWordBook(wordBookId) {
    memo.wordBookId = wordBookId;
    localStorage.setItem("memo-word-book-id", memo.wordBookId);
    UpdateSelectedWordList();
    UpdateWordBookDisplay();
}

function CreateWordBook() {
    wordBookName = $("#create-word-book-name").val();

    if (wordBookName == "") {
        new Noty({
            theme: 'mint',
            text: 'Enter a word book name!',
            type: 'warning',
            layout: 'topLeft',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: '/api/wordBook/create',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            name: wordBookName,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                UpdateWordBookList(false);
                UpdateWordBookDisplay();
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

function BackToHome() {
    window.location.href = '/';
}