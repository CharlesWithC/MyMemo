// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

function UpdateSettingsButtons() {
    mode = lsGetItem("settings-mode", 0);
    $(".mode-btn").removeClass("btn-primary btn-secondary");
    $(".mode-btn").addClass("btn-secondary");
    if (mode == 0) {
        $("#mode-switch-btn").removeClass("btn-secondary");
        $("#mode-switch-btn").addClass("btn-primary");
    } else if (mode == 1) {
        $("#mode-practice-btn").removeClass("btn-secondary");
        $("#mode-practice-btn").addClass("btn-primary");
    } else if (mode == 2) {
        $("#mode-challenge-btn").removeClass("btn-secondary");
        $("#mode-challenge-btn").addClass("btn-primary");
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

    range = lsGetItem("settings-show-status", 1);
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
                $("#navusername").html("<a href='/user/login'>Sign in</a>&nbsp;&nbsp;  ");
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
            NotyNotification('Success! All questions marked deleted are removed from database!');
            $('#modal').modal('hide');
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

function SettingsSync(operation) {
    if (operation == "upload") {
        $.ajax({
            url: '/api/user/settings',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                operation: "upload",
                random: localStorage.getItem("settings-random"),
                swap: localStorage.getItem("settings-swap"),
                showStatus: localStorage.getItem("settings-show-status"),
                mode: localStorage.getItem("settings-mode"),
                autoPlay: localStorage.getItem("settings-auto-play"),
                theme: localStorage.getItem("settings-theme"),
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success) {
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
    } else if (operation == "download") {
        $.ajax({
            url: '/api/user/settings',
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                operation: "download",
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                if (r.success) {
                    NotyNotification(r.msg);
                    localStorage.setItem("settings-random", r.swap);
                    localStorage.setItem("settings-swap", r.swap);
                    localStorage.setItem("settings-show-status", r.showStatus);
                    localStorage.setItem("settings-mode", r.mode);
                    localStorage.setItem("settings-auto-play", r.autoPlay);
                    localStorage.setItem("settings-theme", r.theme);
                    UpdateTheme(r.theme);
                    UpdateSettingsButtons();
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

function ClearDeletedQuestionsShow(){
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" style="color:red"><i class="fa fa-trash"></i> Clear Deleted Questions</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Are you sure to clear all deleted questions? This will remove all the questions that are marked
                        as
                        deleted.</p>
                    <p>This operation cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Cancel</button>
                    <button type="button" class="btn btn-danger" data-dismiss="modal"
                        onclick="ClearDeletedQuestion()">Remove</button>
                </div>
            </div>
        </div>
    </div>`);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
}