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

function BackToHome() {
    window.location.href = '/';
}

function GoToUser() {
    window.location.href = "/user"
}

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

        $(".user").show();
        $(".title").show();
        $("#signout-btn").show();

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
    error: function (r) {
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
        new Noty({
            theme: 'mint',
            text: 'Both fields must be filled!',
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: "/api/user/login",
        method: 'POST',
        async: false,
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

                new Noty({
                    theme: 'mint',
                    text: 'Success! You have now logged in!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

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
                    }
                });
                $("#input-username").val("");
                $("#input-password").val("");

                window.location.reload();
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
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
        new Noty({
            theme: 'mint',
            text: 'All fields must be filled!',
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: "/api/user/register",
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            username: username,
            password: password,
            email: email,
            invitationCode: invitationCode
        },
        success: function (r) {
            if (r.success == true) {
                new Noty({
                    theme: 'mint',
                    text: 'Success! You are now registered!',
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
                $(".register").hide();
                $(".login").show();
                $(".title").hide();
                $("#register-password").val("");
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
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

    $(".user").hide();
    $(".login").show();
    $(".title").hide();

    $("#navusername").html("Sign in");

    new Noty({
        theme: 'mint',
        text: 'Success! You are now signed out!',
        type: 'success',
        layout: 'bottomRight',
        timeout: 3000
    }).show();
}

function UpdateProfileShow() {
    $("#updateProfileModal").modal("toggle");
    $("#update-username").val(user.username);
    $("#update-email").val(user.email);
}

function UpdateUserProfile() {
    username = $("#update-username").val();
    email = $("#update-email").val();

    if (username == "" || email == "") {
        new Noty({
            theme: 'mint',
            text: 'Both fields must be filled!',
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: "/api/user/updateInfo",
        method: 'POST',
        async: false,
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
                $("#updateProfileModal").modal("toggle");

                new Noty({
                    theme: 'mint',
                    text: r.msg,
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
        }
    });
}

function ChangePassword() {
    oldpwd = $("#oldpwd").val();
    newpwd = $("#newpwd").val();
    cfmpwd = $("#cfmpwd").val();

    if (oldpwd == "" || newpwd == "" || cfmpwd == "") {
        new Noty({
            theme: 'mint',
            text: 'All fields must be filled!',
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: "/api/user/changepassword",
        method: 'POST',
        async: false,
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

                new Noty({
                    theme: 'mint',
                    text: "Success! password has been changed! You have to log in again!",
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();

                $("#changepasswordModal").modal("toggle");

                localStorage.removeItem("userid");
                localStorage.removeItem("username");
                localStorage.removeItem("token");

                $(".user").hide();
                $(".login").show();
                $(".title").hide();
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
            }
        }
    });
}


function ChangePasswordShow() {
    $("#changepasswordModal").modal("toggle");
}

function DeleteAccount() {
    ack = $("#acknowledge-confirm").val();
    password = $("#delete-password").val();

    if (ack != "I acknowledge what I'm doing") {
        new Noty({
            theme: 'mint',
            text: "Type \"I acknowledge what I'm doing\" in the first input box to continue!",
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }
    if (password == "") {
        new Noty({
            theme: 'mint',
            text: "Enter your password!",
            type: 'warning',
            layout: 'bottomRight',
            timeout: 3000
        }).show();
        return;
    }

    $.ajax({
        url: "/api/user/delete",
        method: 'POST',
        async: false,
        dataType: "json",
        data: {
            password: password,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                $("#delete-password").val("");

                new Noty({
                    theme: 'mint',
                    text: "Account deactivated!! It will be deleted after 14 days!",
                    type: 'warning',
                    layout: 'bottomRight',
                    timeout: 10000
                }).show();

                $("#deleteAccountModal").modal("toggle");

                localStorage.removeItem("userid");
                localStorage.removeItem("username");
                localStorage.removeItem("token");

                $(".user").hide();
                $(".login").show();
                $(".title").hide();
            } else {
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
            }
        }
    });
}

function DeleteAccountShow() {
    $("#deleteAccountModal").modal("toggle");
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
                new Noty({
                    theme: 'mint',
                    text: r.msg,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
            } else {
                new Noty({
                    theme: 'mint',
                    text: "Server is being restarted!",
                    type: 'success',
                    layout: 'bottomRight',
                    timeout: 3000
                }).show();
            }
        },
        error: function (r, textStatus, errorThrown) {
            if (r.status == 401) {
                new Noty({
                    theme: 'mint',
                    text: 'Access control by NGINX: You have to enter that password to authorize!',
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 10000
                }).show();
                
            } else {
                new Noty({
                    theme: 'mint',
                    text: "Error: " + r.status + " " + errorThrown,
                    type: 'error',
                    layout: 'bottomRight',
                    timeout: 10000
                }).show();
            }
        }
    });
}