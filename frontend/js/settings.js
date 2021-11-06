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

function BackToHome() {
    window.location.href = '/';
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

function UpdateSettingsButtons() {
    mode = lsGetItem("settings-mode", 0);
    $(".mode-btn").removeClass("btn-primary btn-secondary");
    $(".mode-btn").addClass("btn-secondary");
    if (mode == 0) {
        $("#mode-practice-btn").removeClass("btn-secondary");
        $("#mode-practice-btn").addClass("btn-primary");
    } else if (mode == 1) {
        $("#mode-challenge-btn").removeClass("btn-secondary");
        $("#mode-challenge-btn").addClass("btn-primary");
    } else if (mode == 2) {
        $("#mode-offline-btn").removeClass("btn-secondary");
        $("#mode-offline-btn").addClass("btn-primary");
    }

    random = lsGetItem("settings-random", 0);
    $(".order-btn").removeClass("btn-primary btn-secondary");
    $(".order-btn").addClass("btn-secondary");
    if (random == 0) {
        $("#order-sequence-btn").removeClass("btn-secondary");
        $("#order-sequence-btn").addClass("btn-primary");
    } else if (random == 1) {
        $("#order-random-btn").removeClass("btn-secondary");
        $("#order-random-btn").addClass("btn-primary");
    }

    swap = lsGetItem("settings-swap", 0);
    $(".swap-btn").removeClass("btn-primary btn-secondary");
    $(".swap-btn").addClass("btn-secondary");
    if (swap == 0) {
        $("#swap-question-btn").removeClass("btn-secondary");
        $("#swap-question-btn").addClass("btn-primary");
    } else if (swap == 1) {
        $("#swap-answer-btn").removeClass("btn-secondary");
        $("#swap-answer-btn").addClass("btn-primary");
    } else if (swap == 2) {
        $("#swap-both-btn").removeClass("btn-secondary");
        $("#swap-both-btn").addClass("btn-primary");
    }

    range = lsGetItem("settings-show-status", 0);
    $(".range-btn").removeClass("btn-primary btn-secondary");
    $(".range-btn").addClass("btn-secondary");
    if (range == 1) {
        $("#range-all-btn").removeClass("btn-secondary");
        $("#range-all-btn").addClass("btn-primary");
    } else if (range == 2) {
        $("#range-tagged-btn").removeClass("btn-secondary");
        $("#range-tagged-btn").addClass("btn-primary");
    } else if (range == 3) {
        $("#range-deleted-btn").removeClass("btn-secondary");
        $("#range-deleted-btn").addClass("btn-primary");
    }

    ap = lsGetItem("settings-auto-play", 0);
    $(".ap-btn").removeClass("btn-primary btn-secondary");
    $(".ap-btn").addClass("btn-secondary");
    if (ap == 0) {
        $("#ap-none-btn").removeClass("btn-secondary");
        $("#ap-none-btn").addClass("btn-primary");
    } else if (ap == 1) {
        $("#ap-slow-btn").removeClass("btn-secondary");
        $("#ap-slow-btn").addClass("btn-primary");
    } else if (ap == 2) {
        $("#ap-medium-btn").removeClass("btn-secondary");
        $("#ap-medium-btn").addClass("btn-primary");
    } else if (ap == 3) {
        $("#ap-fast-btn").removeClass("btn-secondary");
        $("#ap-fast-btn").addClass("btn-primary");
    }

    theme = lsGetItem("settings-theme", "light");
    $(".theme-btn").removeClass("btn-primary btn-secondary");
    $(".theme-btn").addClass("btn-secondary");
    if (theme == "light") {
        $("#theme-light-btn").removeClass("btn-secondary");
        $("#theme-light-btn").addClass("btn-primary");
    } else if (theme == "dark") {
        $("#theme-dark-btn").removeClass("btn-secondary");
        $("#theme-dark-btn").addClass("btn-primary");
    }

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
}

function UpdateMode(mode) {
    localStorage.setItem("settings-mode", mode);
    UpdateSettingsButtons();
}

function UpdateOrder(random) {
    localStorage.setItem("settings-random", random);
    UpdateSettingsButtons();
}

function UpdateSwap(swap) {
    localStorage.setItem("settings-swap", swap);
    UpdateSettingsButtons();
}

function UpdateRange(range) {
    localStorage.setItem("settings-show-status", range);
    UpdateSettingsButtons();
}

function UpdateAutoplay(speed) {
    localStorage.setItem("settings-auto-play", speed);
    UpdateSettingsButtons();
}

function UpdateTheme(theme) {
    localStorage.setItem("settings-theme", theme);
    UpdateSettingsButtons();

    if (theme == "dark") {
        $("body").attr("style", "transition:background-color 0.5s ease;color:#ffffff;background-color:#333333");
    } else {
        $("body").attr("style", "transition:background-color 0.5s ease;color:#000000;background-color:#ffffff");
    }
}

function ClearDeletedQuestion() {
    $.ajax({
        url: '/api/question/clearDeleted',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            new Noty({
                theme: 'mint',
                text: 'Cleared all questions that are marked deleted!',
                type: 'success',
                layout: 'bottomRight',
                timeout: 3000
            }).show();
            $('#clearDeletedModal').modal('toggle');
        },
        error: function (r) {
            if (r.status == 401) {
                SessionExpired();
            }
        }
    });
}

function Import() {
    window.location.href = '/data/import'
}

function Export() {
    window.location.href = '/data/export'
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