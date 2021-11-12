// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

class UserClass {
    constructor() {
        this.userId = -1;
        this.username = "";
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
        $("title").html(user.username + " | My Memo");

        $("#navusername").html(user.username);
        $("#username").html(user.username);
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
        $(".user").hide();
        $(".login").show();
        $(".title").hide();
        $("#signout-btn").hide();
    }
});

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
                        $("title").html(user.username + " | My Memo");
                    }
                });
                $("#input-username").val("");
                $("#input-password").val("");

                window.location.reload();
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
    $("#update-username").val(user.username);
    $("#update-email").val(user.email);
}

function UpdateUserProfile() {
    username = $("#update-username").val();
    email = $("#update-email").val();

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
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                user.username = username;
                user.email = email;

                $("#navusername").html(user.username);
                $("#username").html(user.username);
                $("#email").html(user.email);
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
                NotyNotification('Server is being restarted!', timeout = 3000);
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