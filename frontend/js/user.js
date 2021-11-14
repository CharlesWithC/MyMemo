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
        this.cnt = 0;
        this.tagcnt = 0;
        this.delcnt = 0;
        this.chcnt = 0;
        this.inviter = -1;
        this.age = 0;
        this.isAdmin = false;
    }
}
user = new UserClass();

uid = getUrlParameter("userId");
if (uid != -1 && uid != localStorage.getItem("userId")) {
    $.ajax({
        url: "/api/user/publicInfo/" + uid,
        method: 'GET',
        async: true,
        dataType: "json",
        success: function (r) {
            user.username = r.username;
            user.bio = r.bio;
            user.cnt = r.cnt;
            user.tagcnt = r.tagcnt;
            user.delcnt = r.delcnt;
            user.chcnt = r.chcnt;
            user.age = r.age;
            user.isAdmin = r.isAdmin;

            $(".user-public").show();
            $(".user").hide();
            $(".title").show();
            $("#signout-btn").show();
            l = user.username.indexOf('>');
            r = user.username.indexOf('<', 1);
            $("title").html(user.username.substr(l + 1, r - l - 2) + " | My Memo");

            $("#username-public").html(user.username);
            $("#bio-public").html(user.bio);
            $("#userId-public").html(uid);
            $("#age-public").html(user.age);
            $("#cnt-public").html(user.cnt);
            $("#tagged-public").html(user.tagcnt);
            $("#deleted-public").html(user.delcnt);
            $("#chcnt-public").html(user.chcnt);
        }
    });
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
        user.username = r.username;
        $("#navusername").html(user.username);
    }
});

if (uid == -1 || uid == localStorage.getItem("userId")) {
    $("#signout-btn").hide();
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
            user.cnt = r.cnt;
            user.tagcnt = r.tagcnt;
            user.delcnt = r.delcnt;
            user.chcnt = r.chcnt;
            user.inviter = r.inviter;
            user.age = r.age;
            user.isAdmin = r.isAdmin;
            if (user.isAdmin) {
                localStorage.setItem("isAdmin", 1);
            } else {
                localStorage.removeItem("isAdmin");
            }

            $(".user").show();
            $(".title").show();
            $("#signout-btn").show();
            l = user.username.indexOf('>');
            r = user.username.indexOf('<', 1);
            $("title").html(user.username.substr(l + 1, r - l - 2) + " | My Memo");

            $("#navusername").html(user.username);
            $("#username").html(user.username);
            $("#bio").html(user.bio);
            $("#userId").html(user.userId);
            $("#age").html(user.age);
            $("#email").html(user.email);
            $("#inviteCode").html(user.invitationCode);
            $("#inviteBy").html(user.inviter);
            $("#cnt").html(user.cnt);
            $("#tagged").html(user.tagcnt);
            $("#deleted").html(user.delcnt);
            $("#chcnt").html(user.chcnt);

            if (user.isAdmin) {
                $(".only-admin").show();
            } else {
                $(".only-admin").hide();
            }
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                $(".user").hide();
                $(".login").show();
                $(".title").hide();
                $("#signout-btn").hide();
            }
        }
    });

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
                loginTime = new Date(sessions[i].loginTime * 1000).toString();
                expireTime = new Date(sessions[i].expireTime * 1000).toString();
                $("#sessions").append("<div class='session'>\
                    <p class='session-title'><i class='fa fa-" + system + "'></i>&nbsp;&nbsp;" + sysver + "\
                    <p class='session-content'>IP: " + sessions[i].ip + "</p>\
                    <p class='session-content'>User Agent: " + sessions[i].userAgent + "</p></p>\
                    <p class='session-content'>Login time: " + loginTime + "</p>\
                    <p class='session-content'>Expire time: " + expireTime + "</p>\
                    </div><br>")
            }
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                $(".user").hide();
                $(".login").show();
                $(".title").hide();
                $("#signout-btn").hide();
            }
        }
    });
}


function Login() {
    username = $("#input-username").val();
    password = $("#input-password").val();

    if (username == "" || password == "") {
        NotyNotification('Both fields must be filled', type = 'warning');
        return;
    }

    $.ajax({
        url: "/api/user/login",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            username: username,
            password: password
        },
        success: function (r) {
            if (r.success == true) {
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
                        user.cnt = r.cnt;
                        user.tagcnt = r.tagcnt;
                        user.delcnt = r.delcnt;
                        user.chcnt = r.chcnt;
                        user.inviter = r.inviter;
                        user.age = r.age;
                        user.isAdmin = r.isAdmin;
                        if (user.isAdmin) {
                            localStorage.setItem("isAdmin", 1);
                        } else {
                            localStorage.removeItem("isAdmin");
                        }
                        l = user.username.indexOf('>');
                        r = user.username.indexOf('<', 1);
                        $("title").html(user.username.substr(l + 1, r - l - 2) + " | My Memo");

                        if (localStorage.getItem("first-use") != "0") {
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
                                    if (r.status == 401) {
                                        SessionExpired();
                                    }
                                }
                            });
                        }

                        $("#input-username").val("");
                        $("#input-password").val("");

                        window.location.reload();
                    }
                });
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        }
    });
}

function Register() {
    username = $("#register-username").val();
    password = $("#register-password").val();
    email = $("#register-email").val();
    invitationCode = $("#register-inviteCode").val();

    if (username == "" || password == "" || email == "" || invitationCode == "") {
        NotyNotification('All fields must be filled', type = 'warning');
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
            invitationCode: invitationCode
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification('Success! You are now registered!');
                $(".register").hide();
                $(".login").show();
                $(".title").hide();
                $("#register-password").val("");
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        }
    });
}

function UpdateProfileShow() {
    $("#updateProfileModal").modal("show");
    l = user.username.indexOf('>');
    r = user.username.indexOf('<', 1);
    $("#update-username").val(user.username.substr(l + 1, r - l - 2));
    $("#update-email").val(user.email);
    $("#update-bio").val(user.bio);
}

function UpdateUserProfile() {
    username = $("#update-username").val();
    email = $("#update-email").val();
    bio = $("#update-bio").val();

    if (username == "" || email == "") {
        NotyNotification('Both fields must be filled', type = 'warning');
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
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
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
                        user.email = r.email
                        user.bio = r.bio
                        $("#navusername").html(user.username);
                        $("#username").html(user.username);
                        $("#bio").html(user.bio);
                        $("#email").html(user.email);
                    }
                });
                $("#updateProfileModal").modal("hide");

                NotyNotification(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        }
    });
}

function ChangePassword() {
    oldpwd = $("#oldpwd").val();
    newpwd = $("#newpwd").val();
    cfmpwd = $("#cfmpwd").val();

    if (oldpwd == "" || newpwd == "" || cfmpwd == "") {
        NotyNotification('All fields must be filled', type = 'warning');
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

                $("#changepasswordModal").modal("hide");

                localStorage.removeItem("userid");
                localStorage.removeItem("username");
                localStorage.removeItem("token");

                $(".user").hide();
                $(".login").show();
                $(".title").hide();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        }
    });
}


function ChangePasswordShow() {
    $("#changepasswordModal").modal("show");
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
        url: "/api/user/delete",
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
                $("#delete-password").val("");

                NotyNotification("Account deactivated! It will be deleted after 14 days!", type = 'warning', timeout = 10000);

                $("#deleteAccountModal").modal("hide");

                localStorage.removeItem("userid");
                localStorage.removeItem("username");
                localStorage.removeItem("token");

                $(".user").hide();
                $(".login").show();
                $(".title").hide();
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        }
    });
}

function DeleteAccountShow() {
    $("#deleteAccountModal").modal("show");
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
                NotyNotification("Error: " + r.status + " " + errorThrown, type = 'error');
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
    localStorage.removeItem("userId");
    localStorage.removeItem("username");
    localStorage.removeItem("token");
    localStorage.removeItem("memo-question-id");
    localStorage.removeItem("memo-book-id");
    localStorage.removeItem("book-list");
    localStorage.removeItem("question-list");

    $("#navusername").html("Sign in");

    $(".user").hide();
    $(".login").show();
    $(".title").hide();

    NotyNotification('You are now signed out!');
}