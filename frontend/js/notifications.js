var page = 1;

function PageInit() {
    $.ajax({
        url: '/api/user/events',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token"),
            page: 1
        },
        success: function (r) {
            notifications = r.notifications;
            for (var i = 0; i < notifications.length; i++) {
                var time = new Date(parseInt(notifications[i].timestamp) * 1000);
                $("#content").append("<div id=" + ((page - 1) * 20 + i) + " class='notification subcontainer sub-div' style='padding:0.8em 0.2em 0.2em 0.8em'>\
                <p style='font-size:1.2em'>" + notifications[i].msg + "</p>\
                <p style='font-size:0.8em;color:#888888'>" + time.toLocaleString() + "</p>\
                </div>");
            }
            if (r.nextpage != -1) $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn' onclick='ShowMore()'>Show More</a>");
            else $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn'>The End</a>");
            page = r.nextpage;
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

function ShowMore() {
    if (page == -1) {
        return;
    }
    $(".more-btn").html("Loading... <i class='fa fa-spinner fa-spin'></i>")
    $.ajax({
        url: '/api/user/events',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token"),
            page: page
        },
        success: function (r) {
            notifications = r.notifications;
            for (var i = 0; i < notifications.length; i++) {
                var time = new Date(parseInt(notifications[i].timestamp) * 1000);
                $("#content").append("<div id=" + ((page - 1) * 20 + i) + " class='notification subcontainer sub-div' style='padding:0.8em 0.2em 0.2em 0.8em'>\
                <p style='font-size:1.2em'>" + notifications[i].msg + "</p>\
                <p style='font-size:0.8em;color:#888888'>" + time.toLocaleString() + "</p>\
                </div>");
            }
            $(".more-btn").remove();
            if (r.nextpage != -1) $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn' onclick='ShowMore()'>Show More</a>");
            else $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn'>The End</a>");
            page = r.nextpage;
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