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

var wordBookId = -1;
var wordBookName = "";
var wordBookShareCode = "";
var groupId = -1;
var groupCode = "";
var isGroupOwner = false;
var wordList = JSON.parse(lsGetItem("word-list", JSON.stringify([])));
var wordBookList = JSON.parse(lsGetItem("word-book-list", JSON.stringify([])));
var selectedWordList = [];
var wordListMap = new Map();
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
    return false;
};

function MapWordList() {
    wordListMap = new Map();
    for (var i = 0; i < wordList.length; i++) {
        wordListMap.set(wordList[i].wordId, {
            "word": wordList[i].word,
            "translation": wordList[i].translation,
            "status": wordList[i].status
        });
    }
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
            wordList = r;
            localStorage.setItem("wordList", JSON.stringify(wordList));
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
            wordBookList = r;
            localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
        }
    });
}

function SelectWords() {
    for (var i = 0; i < wordBookList.length; i++) {
        if (wordBookList[i].wordBookId == wordBookId) {
            wordBookName = wordBookList[i].name;
            $(".title").html(wordBookName);
            $("title").html("Word Memo - " + wordBookName);
            wordBookShareCode = wordBookList[i].shareCode;
            if (wordBookShareCode == "") {
                $("#wordBookShareCode").html("(Private)");
            } else {
                $("#wordBookShareCode").html(wordBookShareCode);
            }
            if (wordBookShareCode == "") {
                $("#shareop").html("Share");
                $(".only-shared").hide();
            } else {
                $("#shareop").html("Unshare");
                $(".only-shared").show();
            }
            groupId = wordBookList[i].groupId;
            groupCode = wordBookList[i].groupCode;
            $("#groupCode").html(groupCode);
            isGroupOwner = wordBookList[i].isGroupOwner;
            $(".group").show();
            if (groupId == -1) {
                $(".only-group-exist").hide();
                $(".only-group-inexist").show();
                $(".only-group-owner").hide();
            } else {
                $(".only-group-exist").show();
                $(".only-group-inexist").hide();
                $(".only-group-owner").hide();
            }
            if (isGroupOwner) {
                $(".only-group-owner").show();
            }
            if (wordBookId == 0) {
                $(".not-for-all-words").hide();
            } else {
                $(".not-for-all-words").show();
            }
            selectedWordList = [];
            for (this.j = 0; j < wordBookList[i].words.length; j++) {
                wordId = wordBookList[i].words[j];
                wordData = wordListMap.get(wordId);
                selectedWordList.push({
                    "wordId": wordId,
                    "word": wordData.word,
                    "translation": wordData.translation,
                    "status": wordData.status
                });
            }
        }
    }
}

function UpdateTable() {
    selected = [];

    table = $("#wordList").DataTable();
    table.clear();

    l = ["", "Default", "Tagged", "Deleted"];

    for (var i = 0; i < selectedWordList.length; i++) {
        table.row.add([
            [selectedWordList[i].word],
            [selectedWordList[i].translation],
            [l[selectedWordList[i].status]]
        ]).node().id = selectedWordList[i].wordId;
    }

    table.draw();
}

function PageInit() {
    if (wordBookId == -1) {
        wordBookId = getUrlParameter("wordBookId");
    }

    table = $("#wordList").DataTable();
    table.clear();
    table.row.add([
        [""],
        ["Loading <i class='fa fa-spinner fa-spin'></i>"],
        [""],
    ]);
    table.draw();
    table.clear();

    if (wordBookId == 0) {
        $(".not-for-all-words").hide();
    } else {
        $(".not-for-all-words").show();
    }
    $(".group").hide();

    // Use existing words
    if (wordList.length != 0) {
        MapWordList();
        SelectWords();
        UpdateTable();
    }

    // Update list
    $.ajax({
        url: "/api/wordBook/wordList",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            wordList = r;
            localStorage.setItem("word-list", JSON.stringify(wordList));
            MapWordList();
            $.ajax({
                url: "/api/wordBook",
                method: 'POST',
                async: true,
                dataType: "json",
                data: {
                    userId: localStorage.getItem("userId"),
                    token: localStorage.getItem("token")
                },
                success: function (r) {
                    wordBookList = r;
                    localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
                    MapWordList();
                    SelectWords();
                    UpdateTable();
                }
            });
        }
    });
}

var editWordId = -1;

function EditWordShow(wid) {
    editWordId = wid;
    word = "";
    translation = "";
    for (var i = 0; i < selectedWordList.length; i++) {
        if (selectedWordList[i].wordId == wid) {
            word = selectedWordList[i].word;
            translation = selectedWordList[i].translation;
            break;
        }
    }
    $("#editWordModalLabel").html("Edit Word");
    $("#edit-word").val(word);
    $("#edit-translation").val(translation);
    $("#editWordModal").modal('toggle');
    $("#edit-word-btn").html("Edit");
    $("#edit-word-btn").attr("onclick", "EditWord()");
}

function EditWordFromBtn() {
    if (selected.length != 1) {
        new Noty({
            theme: 'mint',
            text: 'Make sure you selected one word!',
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    EditWordShow(selected[0]);
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
            wordId: editWordId,
            word: word,
            translation: translation,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            for (var i = 0; i < selectedWordList.length; i++) {
                if (selectedWordList[i].wordId == wid) {
                    selectedWordList[i].word = word;
                    selectedWordList[i].translation = translation;
                    break;
                }
            }

            new Noty({
                theme: 'mint',
                text: 'Success! Word edited!',
                type: 'success',
                layout: 'bottomRight',
                timeout: 3000
            }).show();

            $("#editWordModal").modal('toggle');
            UpdateTable();
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function WordBookUpdateStatus(updateTo) {
    $.ajax({
        url: '/api/word/status/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            words: JSON.stringify(selected),
            status: updateTo,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            for (var i = 0; i < selectedWordList.length; i++) {
                for (var j = 0; j < selected.length; j++) {
                    if (selectedWordList[i].wordId == selected[j]) {
                        console.log(selectedWordList[i].wordId);
                        selectedWordList[i].status = updateTo;
                        break;
                    }
                }
            }

            new Noty({
                theme: 'mint',
                text: 'Success! Word status updated!',
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

function ShowWordDatabase() {
    $(".manage").hide();
    $("#addExistingWord").show();
    $(".word-book-name").html(wordBookName);
    selected = [];

    table = $("#wordList").DataTable();
    table.clear();
    for (var i = 0; i < wordList.length; i++) {
        table.row.add([
            [wordList[i].word],
            [wordList[i].translation],
            [l[wordList[i].status]]
        ]).node().id = wordList[i].wordId;
    }
    table.draw();
}

function ShowManage() {
    $("#addExistingWord").hide();
    $(".manage").show();
    UpdateTable();
}

function AddExistingWord() {
    $.ajax({
        url: '/api/wordBook/addWord',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            words: JSON.stringify(selected),
            wordBookId: wordBookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Added ' + selected.length + ' word(s)!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                UpdateWordBookList(false);
                MapWordList();
                SelectWords();
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

function AddWordShow() {
    $("#edit-word").val("");
    $("#edit-translation").val("");
    $("#editWordModalLabel").html("Add a new word to " + wordBookName);
    $("#editWordModal").modal('toggle');
    $("#edit-word-btn").html("Add");
    $("#edit-word-btn").attr("onclick", "AddWord()");
}

function AddWord() {
    word = $("#edit-word").val();
    translation = $("#edit-translation").val();
    $.ajax({
        url: '/api/word/add',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            word: word,
            translation: translation,
            addToWordBook: wordBookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Added a new word!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                $("#editWordModal").modal('toggle');

                UpdateWordList(false);
                UpdateWordBookList(false);
                MapWordList();
                SelectWords();
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

function RemoveFromWordBook() {
    $.ajax({
        url: '/api/wordBook/deleteWord',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            words: JSON.stringify(selected),
            wordBookId: wordBookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Removed ' + selected.length + ' word(s) from this word book!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                UpdateWordBookList(false);
                MapWordList();
                SelectWords();
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

function RemoveWordShow() {
    $("#deleteWordModal").modal("toggle");
}

function RemoveWord() {
    $.ajax({
        url: '/api/word/delete',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            words: JSON.stringify(selected),
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Removed ' + selected.length + ' word(s) from database!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                $("#deleteWordModal").modal('toggle');

                UpdateWordList(false);
                UpdateWordBookList(false);
                MapWordList();
                SelectWords();
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

function WordBookClone() {
    $.ajax({
        url: '/api/wordBook/clone',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            fromWordBook: wordBookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! Cloned this word book!',
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

function WordBookRenameShow() {
    $("#renameModal").modal("toggle");
    $("#word-book-rename").val(wordBookName);
}

function WordBookRename() {
    newName = $("#word-book-rename").val();
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
        url: '/api/wordBook/rename',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            wordBookId: wordBookId,
            name: newName,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                wordBookName = newName;
                $(".word-book-name").html(wordBookName);
                $(".title").html(wordBookName);
                $("title").html("Word Memo - " + wordBookName);
                new Noty({
                    theme: 'mint',
                    text: "Success! Word book renamed!",
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

function WordBookDeleteShow() {
    $("#deleteWBModal").modal("toggle");
    $(".word-book-name").html(wordBookName);
}

function WordBookDelete() {
    if ($("#word-book-delete").val() != wordBookName) {
        new Noty({
            theme: 'mint',
            text: "Type the name of the word book correctly to continue!",
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }
    $.ajax({
        url: '/api/wordBook/delete',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            wordBookId: wordBookId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: "Success! Word book deleted!",
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

function WordBookShare() {
    if (wordBookShareCode == "") {
        $.ajax({
            url: '/api/wordBook/share',
            method: 'POST',
            async: false,
            dataType: "json",
            data: {
                wordBookId: wordBookId,
                operation: "share",
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success == true) {
                    for (var i = 0; i < wordBookList.length; i++) {
                        if (wordBookList[i].wordBookId == wordBookId) {
                            wordBookList[i].shareCode = r.shareCode;
                            wordBookShareCode = r.shareCode;
                            localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
                    $("#wordBookShareCode").html(r.shareCode);
                    $("#shareop").html("Unshare");
                    $(".only-shared").show();
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
            url: '/api/wordBook/share',
            method: 'POST',
            async: false,
            dataType: "json",
            data: {
                wordBookId: wordBookId,
                operation: "unshare",
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success == true) {
                    for (var i = 0; i < wordBookList.length; i++) {
                        if (wordBookList[i].wordBookId == wordBookId) {
                            wordBookList[i].shareCode = "";
                            wordBookShareCode = "";
                            localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
                    $("#wordBookShareCode").html("(Private)");
                    $("#shareop").html("Share");
                    $(".only-shared").hide();
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
            wordBookId: wordBookId,
            name: gname,
            description: gdescription,
            operation: "create",
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                for (var i = 0; i < wordBookList.length; i++) {
                    if (wordBookList[i].wordBookId == wordBookId) {
                        wordBookList[i].groupId = r.groupId;
                        wordBookList[i].groupCode = r.groupCode;
                        wordBookList[i].isGroupOwner = r.isGroupOwner;
                        groupId = r.groupId;
                        groupCode = r.groupCode;
                        isGroupOwner = r.isGroupOwner;

                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();

                        localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
                $("#wordBookShareCode").html(r.shareCode);
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
                for (var i = 0; i < wordBookList.length; i++) {
                    if (wordBookList[i].wordBookId == wordBookId) {
                        wordBookList[i].groupId = -1;
                        wordBookList[i].groupCode = "";
                        wordBookList[i].isGroupOwner = false;
                        groupId = -1;
                        groupCode = "";
                        isGroupOwner = false;

                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();

                        localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
                for (var i = 0; i < wordBookList.length; i++) {
                    if (wordBookList[i].wordBookId == wordBookId) {
                        wordBookList[i].name = gname;
                        wordBookName = gname;

                        $(".word-book-name").html(wordBookName);
                        $(".title").html(wordBookName);
                        $("title").html("Word Memo - " + wordBookName);
                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").show();
                        $(".only-group-inexist").hide();
                        $(".only-group-owner").show();

                        localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
                for (var i = 0; i < wordBookList.length; i++) {
                    if (wordBookList[i].wordBookId == wordBookId) {
                        wordBookList[i].groupCode = r.groupCode;
                        groupCode = r.groupCode;

                        $("#groupCode").html(groupCode);

                        localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
    $(".word-book-name").html(wordBookName);
}

function GroupDismiss() {
    if ($("#group-delete").val() != wordBookName) {
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
                for (var i = 0; i < wordBookList.length; i++) {
                    if (wordBookList[i].wordBookId == wordBookId) {
                        wordBookList[i].groupId = -1;
                        wordBookList[i].groupCode = "";
                        wordBookList[i].isGroupOwner = false;
                        groupId = -1;
                        groupCode = "";
                        isGroupOwner = false;

                        $("#groupCode").html(groupCode);
                        $(".only-group-exist").hide();
                        $(".only-group-inexist").show();
                        $(".only-group-owner").hide();

                        localStorage.setItem("word-book-list", JSON.stringify(wordBookList));
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
    $("#wordList tr").each(function () {
        wid = parseInt($(this).attr("id"));
        if (wid == wid && !$(this).hasClass("selected")) { // check for NaN
            selected.push(wid);
        }

        $(this).addClass("selected");
    });
}

function deselectAll() {
    $("#wordList tr").each(function () {
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
    for (var i = 0; i < wordBookList.length; i++) {
        wordBook = wordBookList[i];
        wcnt = "";
        if (wordBook.wordBookId == 0) {
            wcnt = wordBook.words.length + ' words';
        } else {
            wcnt = wordBook.progress + ' memorized / ' + wordBook.words.length + ' words';
        }
        btn = "";
        if (wordBook.wordBookId != wordBookId) {
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

function HideWordBookList() {
    $("#wordbook").animate({
        left: "-60%"
    }, {
        queue: false,
        duration: 500
    });
    $("#window").hide();
    $(".manage").fadeIn();
    $("table").attr("style", "opacity:1");
}

function ShowWordBook() {
    $("#wordbook").animate({
        left: '0'
    }, {
        queue: false,
        duration: 500
    });
    UpdateWordBookDisplay();
    $("#window").show();
    $(".manage").fadeOut();
    $("table").attr("style", "opacity:0.5");
}

function OpenWordBook(wordBookId) {
    window.location.href = '/wordbook?wordBookId=' + wordBookId;
}

function SelectWordBook(wb) {
    wordBookId = wb;
    localStorage.setItem("memo-word-book-id", wordBookId);
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