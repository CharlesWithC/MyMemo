// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

class UserClass {
    constructor() {
        this.userId = -1;
        this.username = "";
        this.bio = "";
        this.email = "";
        this.invitationCode = "";
        this.inviter = -1;
        this.age = 0;
        this.isAdmin = false;
        this.goal = 0;
        this.chtoday = 0;
        this.checkin_today = 0;
        this.checkin_continuous = 0;
        this.sessions = [];
    }
}
user = new UserClass();

var curModalId = "";

function UpdateUserInfo() {
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
            user.userId = localStorage.getItem("userId");
            user.username = r.username;
            user.bio = r.bio;
            user.email = r.email;
            user.invitationCode = r.invitationCode;
            user.inviter = r.inviter;
            user.age = r.age;
            user.isAdmin = r.isAdmin;
            if (user.isAdmin) {
                localStorage.setItem("isAdmin", 1);
            } else {
                localStorage.removeItem("isAdmin");
            }

            user.goal = r.goal;
            user.chtoday = r.chtoday;
            user.checkin_today = r.checkin_today;
            user.checkin_continuous = r.checkin_continuous;

            localStorage.setItem("username", user.username);

            $("#signout-btn").show();
            l = user.username.indexOf('>', user.username.indexOf('>') + 1);
            r = user.username.indexOf('<', user.username.indexOf('<', user.username.indexOf('<') + 1) + 1);
            $("title").html(user.username.substr(l + 1, r - l - 1) + " - My Memo");

            $("#navusername").html(user.username);
            $("#username").html(user.username);
            $("#bio").html(marked.parse(user.bio));
            $("#userId").html(user.userId);
            $("#age").html(user.age);
            $("#email").html(user.email);
            $("#inviteCode").html(user.invitationCode);
            $("#inviteBy").html(user.inviter);

            $("#goal-progress").css("width", Math.min(user.chtoday / user.goal * 100, 100) + "%");
            $("#today-goal").html(user.chtoday + " / " + user.goal);
            $("#checkin-continuous").html(user.checkin_continuous);

            if (user.checkin_today || user.chtoday < user.goal) {
                $("#checkin-btn").attr("disabled", "disabled");
                if (user.checkin_today) {
                    $("#checkin-btn").html("Checked in");
                    $("#checkin-hint").html("You have already checked in today!");
                } else {
                    $("#checkin-hint").html("Accomplish today's goal to check in!");
                }
            } else {
                $("#checkin-btn").removeAttr("disabled");
                $("#checkin-hint").html("Goal accomplished! You can check in now!");
            }

            if (user.goal == 0) {
                $("#checkin-btn").attr("disabled", "disabled");
                $("#checkin-btn").html("Check in");
                $("#checkin-hint").html("Let's set a goal first!");
            }

            if (r.isAdmin) {
                $("#danger-zone").remove();
            }

            $.ajax({
                url: "/api/user/sessions",
                method: 'POST',
                async: true,
                dataType: "json",
                data: {
                    userId: localStorage.getItem("userId"),
                    token: localStorage.getItem("token")
                },
                success: function (r) {
                    sessions = r;
                    for (var i = 0; i < sessions.length; i++) {
                        system = "desktop";
                        if (sessions[i].userAgent.indexOf("Win") != -1) system = "windows";
                        if (sessions[i].userAgent.indexOf("Mac") != -1) system = "apple";
                        if (sessions[i].userAgent.indexOf("Linux") != -1) system = "linux";
                        if (sessions[i].userAgent.indexOf("Android") != -1) system = "android";
                        sysver = sessions[i].userAgent.substr(sessions[i].userAgent.indexOf("(") + 1, sessions[i].userAgent.indexOf(")") - sessions[i].userAgent.indexOf("(") - 1);
                        $("#sessions").append("<div class='rect' onclick='SessionDetail(" + i + ");'>\
                    <p class='rect-title'><i class='fa fa-brands fa-" + system + "'></i>&nbsp;&nbsp;" + sysver + "\
                    <p class='rect-content'>IP: " + sessions[i].ip + "</p>\
                    </div><br>")
                    }
                }
            });
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                if ((window.location).toString().indexOf("/login") == -1) {
                    window.location.href = "/user/login";
                }
                $("#signout-btn").hide();
            } else {
                AjaxErrorHandler(r, textStatus, errorThrown);
            }
        }
    });
}

function UpdateChart(tuid) {
    $.ajax({
        url: "/api/user/chart/" + tuid,
        method: 'GET',
        async: true,
        dataType: "json",
        success: function (r) {
            if (r.success == false) {
                return;
            }
            $(".chart").show();
            if (uid != -1 && uid != localStorage.getItem("userId")) {
                $("#charts").appendTo("#user-public");
            } else {
                $("#charts").appendTo("#private-chart");
            }
            $("#charts").show();

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
        },
        error: function (r, textStatus, errorThrown) {
            $(".chart").hide();
            $("#private-chart").hide();
        }
    });
}

function Login() {
    username = $("#input-username").val();
    password = $("#input-password").val();

    if (username == "" || password == "") {
        NotyNotification('Username and password must be filled', type = 'warning');
        return;
    }

    if (captchaToken == undefined) {
        ShowCaptcha("Login");
        return;
    }

    $.ajax({
        url: "/api/user/login",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            username: username,
            password: password,
            captchaToken: captchaToken,
            captchaAnswer: $("#captcha-answer").val()
        },
        success: function (r) {
            if (r.captcha == true) {
                NotyNotification(r.msg, "warning");
                RefreshCaptcha();
                return;
            }

            $(".captchaModal").modal("hide");

            if (r.success == true && r.active == true) {
                localStorage.setItem("userId", r.userId);
                localStorage.setItem("token", r.token);

                user.userId = r.userId;

                NotyNotification('You are now signed in!');

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
                        user.userId = localStorage.getItem("userId");
                        user.username = r.username;
                        user.bio = r.bio;
                        user.email = r.email;
                        user.invitationCode = r.invitationCode;
                        user.inviter = r.inviter;
                        user.age = r.age;
                        user.isAdmin = r.isAdmin;
                        if (user.isAdmin) {
                            localStorage.setItem("isAdmin", 1);
                        } else {
                            localStorage.removeItem("isAdmin");
                        }
                        l = user.username.indexOf('>', user.username.indexOf('>') + 1);
                        r = user.username.indexOf('<', user.username.indexOf('<', user.username.indexOf('<') + 1) + 1);
                        $("title").html(user.username.substr(l + 1, r - l - 1) + " - My Memo");

                        if (localStorage.getItem("first-use") != "0" || localStorage.getItem("sign-out") == "1") {
                            $.ajax({
                                url: '/api/user/settings',
                                method: 'POST',
                                async: false,
                                dataType: "json",
                                data: {
                                    operation: "download",
                                    userId: localStorage.getItem("userId"),
                                    token: localStorage.getItem("token")
                                },
                                success: function (r) {
                                    if (r.success) {
                                        localStorage.setItem("settings-random", r.swap);
                                        localStorage.setItem("settings-swap", r.swap);
                                        localStorage.setItem("settings-show-status", r.showStatus);
                                        localStorage.setItem("settings-mode", r.mode);
                                        localStorage.setItem("settings-auto-play", r.autoPlay);
                                        localStorage.setItem("settings-theme", r.theme);
                                    }
                                },
                                error: function (r, textStatus, errorThrown) {
                                    AjaxErrorHandler(r, textStatus, errorThrown);
                                }
                            });
                        }

                        $("#input-username").val("");
                        $("#input-password").val("");

                        window.location.href = "/user";
                    }
                });
            } else if (r.success == true && r.active == false) {
                localStorage.setItem("puserId", r.puserId);
                localStorage.setItem("ptoken", r.ptoken);

                window.location.href = "/user/confirm";
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function Register() {
    username = $("#register-username").val();
    password = $("#register-password").val();
    email = $("#register-email").val();
    invitationCode = $("#register-inviteCode").val();

    if (username == "" || password == "" || email == "") {
        NotyNotification('Username, password and email must be filled', type = 'warning');
        return;
    }

    if (captchaToken == undefined) {
        ShowCaptcha("Register");
        return;
    }

    $.ajax({
        url: "/api/user/register",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            username: username,
            password: password,
            email: email,
            invitationCode: invitationCode,
            captchaToken: captchaToken,
            captchaAnswer: $("#captcha-answer").val()
        },
        success: function (r) {
            if (r.captcha == true) {
                NotyNotification(r.msg, "warning");
                RefreshCaptcha();
                return;
            }

            $(".captchaModal").modal("hide");

            if (r.success == true) {
                NotyNotification(r.msg, type = 'success', timeout = 15000);
                $(".register").hide();
                $(".login").fadeIn();
                $("#register-password").val("");
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function UpdateProfileShow() {
    curModalId = GenModal(`<i class="fa fa-edit"></i> Update Profile`,
        `<div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Username</span>
            <input type="text" class="form-control" id="update-username" aria-describedby="basic-addon1">
        </div>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Email</span>
            <input type="text" class="form-control" id="update-email" aria-describedby="basic-addon1">
        </div>
        <div class="form-group">
            <label for="update-bio" class="col-form-label">Bio:</label>
            <script>var biomde = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
            <textarea class="form-control" id="update-bio"></textarea>
        </div>`,
        `<button type="button" class="btn btn-primary" onclick="UpdateUserProfile()">Update</button>`);
    BeautifyMarkdownEditor();
    OnSubmit("#update-username,#update-email,#update-bio", UpdateUserProfile, true);
    l = user.username.indexOf('>', user.username.indexOf('>') + 1);
    r = user.username.indexOf('<', user.username.indexOf('<', user.username.indexOf('<') + 1) + 1);
    $("#update-username").val(user.username.substr(l + 1, r - l - 1));
    $("#update-email").val(user.email);
    $('#' + curModalId).on('shown.bs.modal', function () {
        biomde.value(user.bio);
    });
}

function UpdateUserProfile() {
    username = $("#update-username").val();
    email = $("#update-email").val();
    bio = biomde.value();

    if (username == "" || email == "") {
        NotyNotification('Username and email must be filled', type = 'warning');
        return;
    }

    $.ajax({
        url: "/api/user/updateInfo",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            username: username,
            email: email,
            bio: bio,
            captchaToken: captchaToken,
            captchaAnswer: $("#captcha-answer").val(),
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.captcha == true) {
                if ($(".captchaModal").length == 0) {
                    ShowCaptcha("UpdateUserProfile");
                } else {
                    NotyNotification(r.msg, "warning");
                    RefreshCaptcha();
                }
                return;
            }

            if (r.success == true) {
                $(".captchaModal").modal("hide");
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
                        user.username = r.username;
                        user.email = r.email;
                        user.bio = r.bio;
                        $("#navusername").html(user.username);
                        $("#username").html(user.username);
                        $("#bio").html(marked.parse(user.bio));
                        $("#email").html(user.email);
                    }
                });
                $("#" + curModalId).modal("hide");

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

function ChangePasswordShow() {
    curModalId = GenModal(`<i class="fa fa-edit"></i> Change Password`,
        `<div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Current Password</span>
            <input type="password" class="form-control" id="oldpwd" aria-describedby="basic-addon1">
        </div>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">New Password</span>
            <input type="password" class="form-control" id="newpwd" aria-describedby="basic-addon1">
        </div>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Repeat new Password</span>
            <input type="password" class="form-control" id="cfmpwd" aria-describedby="basic-addon1">
        </div>`,
        `<button type="button" class="btn btn-primary" onclick="ChangePassword()">Change</button>`);
    OnSubmit("#oldpwd,#newpwd,#cfmpwd",ChangePassword);
}

function ChangePassword() {
    oldpwd = $("#oldpwd").val();
    newpwd = $("#newpwd").val();
    cfmpwd = $("#cfmpwd").val();

    if (oldpwd == "" || newpwd == "" || cfmpwd == "") {
        NotyNotification('Passwords must be filled', type = 'warning');
        return;
    }

    $.ajax({
        url: "/api/user/changepassword",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            oldpwd: oldpwd,
            newpwd: newpwd,
            cfmpwd: cfmpwd,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                $("#oldpwd").val("");
                $("#newpwd").val("");
                $("#cfmpwd").val("");

                NotyNotification('Password has been changed! You have to log in again!', type = 'warning');

                $("#" + curModalId).modal("hide");

                localStorage.removeItem("userid");
                localStorage.removeItem("username");
                localStorage.removeItem("token");

                setTimeout(function () {
                    window.location.href = "/user/login";
                }, 1000);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function DeleteAccountShow() {
    userId = localStorage.getItem("userId");
    curModalId = GenModal(`<span style='color:red'><i class="fa fa-trash"></i> Delete Account</span>`,
        `<p>Are you sure to delete your account?</p>
        <p>By continuing, your account will be disabled and it will be deleted after 14 days.</p>
        <p>You can recover it by logging in at any time during that period.</p>
        <p>After 14 days it will be deleted permanently and cannot be recovered.</p>
        <br>
        <p>Deleting your account will make you unable to login permanently but all your other data will
            be preserved.</p>
        <p>You can delete most of the data manually such as questions and books.</p>
        <p>If you want a deep data wipe, you can contact administrator and provide your User ID: ` + userId + `.</p>
        <p>Administrators will be able to wipe your data completely after your account is deleted.</p>
        <br>
        <p>Type your "I acknowledge what I'm doing" and your password to continue:</p>
        <div class="input-group mb-3">
            <input type="text" class="form-control" id="acknowledge-confirm"
                aria-describedby="basic-addon1">
        </div>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Password</span>
            <input type="password" class="form-control" id="delete-password"
                aria-describedby="basic-addon1">
        </div>
        <p id="delete-msg"></p>`,
        `<button type="button" class="btn btn-primary" onclick="DeleteAccount()">Delete</button>`);
    OnSubmit("#acknowledge-confirm,#delete-password", DeleteAccount, true);
}

function DeleteAccount() {
    ack = $("#acknowledge-confirm").val();
    password = $("#delete-password").val();

    if (ack != "I acknowledge what I'm doing") {
        NotyNotification("Type \"I acknowledge what I'm doing\" in the first input box to continue!", type = 'warning');
        return;
    }
    if (password == "") {
        NotyNotification("Please enter your password!", type = 'warning');
        return;
    }

    $.ajax({
        url: "/api/user/requestDelete",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            password: password,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification(r.msg, type = 'success', timeout = 10000);
                $("#delete-msg").html(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
                $("#delete-msg").html(r.msg);
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function RestartServer() {
    if (!user.isAdmin) {
        return;
    }

    $.ajax({
        url: "/api/admin/restart",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == false) {
                NotyNotification(r.msg, type = 'error');
            } else {
                NotyNotification('Server is being restarted!', type = 'success', timeout = 3000);
            }
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                NotyNotification('Access control by NGINX: You have to enter that password to authorize!', type = 'warning', timeout = 10000);
            } else {
                AjaxErrorHandler(r, textStatus, errorThrown);
            }
        }
    });
}

function CheckIn() {
    if (user.chtoday < user.goal) {
        NotyNotification("Accomplish today's goal before checking in!", type = 'warning');
        return;
    }
    if (user.checkin_today) {
        NotyNotification("You have already checked in today!", type = 'warning');
        return;
    }

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

                user.checkin_today = true;
                user.checkin_continuous += 1;

                if (user.checkin_today || user.chtoday < user.goal) {
                    $("#checkin-btn").attr("disabled", "disabled");
                    if (user.checkin_today) {
                        $("#checkin-btn").html("Checked in");
                        $("#checkin-hint").html("You have already checked in today!");
                    }
                } else {
                    $("#checkin-btn").removeAttr("disabled");
                    $("#checkin-hint").html("Goal accomplished! You can check in now!")
                }
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function UpdateGoal() {
    if ($("#new-goal").val() == undefined || $("#new-goal").val() == "" || $("#new-goal").val() == null) {
        NotyNotification("Please enter your new goal!", type = 'warning');
        return;
    }
    goal = parseInt($("#new-goal").val());
    if (goal == user.goal) {
        NotyNotification("New goal cannot be the same as the old one!", type = 'warning');
        return;
    }

    $.ajax({
        url: "/api/user/updateGoal",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            goal: goal,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification(r.msg, type = 'success');
                user.goal = goal;
                $("#goal-progress").css("width", Math.min(user.chtoday / user.goal * 100, 100) + "%");
                $("#today-goal").html(user.chtoday + " / " + user.goal);
                $("#checkin-continuous").html(user.checkin_continuous);
                if (user.checkin_today || user.chtoday < user.goal) {
                    $("#checkin-btn").attr("disabled", "disabled");
                    if (user.checkin_today) {
                        $("#checkin-hint").html("You have already checked in today!");
                    } else {
                        $("#checkin-hint").html("Accomplish today's goal to check in!");
                    }
                } else {
                    $("#checkin-btn").removeAttr("disabled");
                    $("#checkin-hint").html("Goal accomplished! You can check in now!")
                }
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function SessionDetail(i) {
    system = "desktop";
    if (sessions[i].userAgent.indexOf("Win") != -1) system = "windows";
    if (sessions[i].userAgent.indexOf("Mac") != -1) system = "apple";
    if (sessions[i].userAgent.indexOf("Linux") != -1) system = "linux";
    if (sessions[i].userAgent.indexOf("Android") != -1) system = "android";
    sysver = sessions[i].userAgent.substr(sessions[i].userAgent.indexOf("(") + 1, sessions[i].userAgent.indexOf(")") - sessions[i].userAgent.indexOf("(") - 1);
    loginTime = new Date(sessions[i].loginTime * 1000).toLocaleString();
    expireTime = new Date(sessions[i].expireTime * 1000).toLocaleString();
    body = "<p>IP: " + sessions[i].ip + "</p>\
    <p>User Agent: " + sessions[i].userAgent + "</p></p>\
    <p>Login time: " + loginTime + "</p>\
    <p>Expire time: " + expireTime + "</p>";
    GenModal(`<i class='fa fa-brands fa-` + system + `'></i>&nbsp;&nbsp;` + sysver, body);
}

$(document).ready(function () {
    uid = getUrlParameter("userId");
    if (uid != -1 && uid != localStorage.getItem("userId")) {
        $.ajax({
            url: "/api/user/publicInfo/" + uid,
            method: 'GET',
            async: true,
            dataType: "json",
            success: function (r) {
                if (r.success == true || r.success == undefined) {
                    if (r.username == "@deleted") {
                        NotyNotification("That's a deleted user!", type = 'error');
                        setTimeout(function () {
                            window.location.href = "/user";
                        }, 1000);
                        return;
                    } else {
                        user.username = r.username;
                        user.bio = r.bio;
                        user.age = r.age;
                        user.isAdmin = r.isAdmin;

                        $(".user-public").show();
                        $(".user").remove();
                        $("#signout-btn").show();
                        l = user.username.indexOf('>', user.username.indexOf('>') + 1);
                        r = user.username.indexOf('<', user.username.indexOf('<', user.username.indexOf('<') + 1) + 1);
                        $("title").html(user.username.substr(l + 1, r - l - 1) + " - My Memo");

                        $("#username-public").html(user.username);
                        $("#bio-public").html(marked.parse(user.bio));
                        $("#userId-public").html(uid);
                        $("#age-public").html(user.age);

                        UpdateChart(uid);
                    }
                } else {
                    NotyNotification(r.msg, type = 'error');
                    setTimeout(function () {
                        window.location.href = "/user";
                    }, 1000);
                }
            },
            error: function (r, textStatus, errorThrown) {
                AjaxErrorHandler(r, textStatus, errorThrown);
            }
        });
    } else {
        if ((uid == -1 || uid == localStorage.getItem("userId")) && localStorage.getItem("userId") != null) {
            $("#signout-btn").hide();
            UpdateUserInfo();
            UpdateChart(localStorage.getItem("userId"));
        }

        if (localStorage.getItem("userId") == null && uid == -1) {
            $("#signout-btn").hide();
            if ((window.location).toString().indexOf("/login") == -1) {
                window.location.href = "/user/login";
            }
        }
    }
});

function ForgotPasswordShow() {
    curModalId = GenModal(`<i class='fa fa-sync'></i> Reset Password`,
        `<p>Please enter your email below and an email containing password reset link will be sent to you.</p>
        <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Email</span>
            <input type="text" class="form-control" id="reset-email" aria-describedby="basic-addon1">
        </div>
        <p id="msg"></p>`,
        `<button type="button" class="btn btn-primary" onclick="ForgotPassword()">Reset</button>`);
    OnSubmit("#reset-email", ForgotPassword);
}

function ForgotPassword() {
    $.ajax({
        url: '/api/user/requestResetPassword',
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            email: $("#reset-email").val()
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification(r.msg);
                $("#msg").html(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}