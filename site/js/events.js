var page = 1;
var lstmd = "";

var isphone = false;
if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
    isphone = true;
}

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
            isfirst = true;
            notifications = r.notifications;
            for (var i = 0; i < notifications.length; i++) {
                var time = new Date(parseInt(notifications[i].timestamp) * 1000);
                if (time.toLocaleDateString() != lstmd) {
                    lstmd = time.toLocaleDateString();
                    if (isfirst) $("#content").append(`<h4>` + lstmd + `&nbsp;&nbsp;</h4>`), isfirst = false;
                    else $("#content").append(`<h4><br>` + lstmd + `&nbsp;&nbsp;</h4>`);
                }
                $("#content").append("<div id=" + ((page - 1) * 20 + i) + " class='subcontainer sub-div notification'>\
                <p style='font-size:1.2em'>" + notifications[i].msg + "</p>\
                <p style='font-size:0.8em;color:#888888'>" + time.toLocaleString() + "</p>\
                </div>");
            }
            if (r.nextpage != -1) $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn' onclick='ShowMore()'>Show More</a>");
            else $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn'>The End</a>");
            page = r.nextpage;
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

updating = false;

function ShowMore() {
    if (page == -1 || updating) return;
    updating = true;
    $(".more-btn").html("Loading... <i class='fa fa-spinner fa-spin'></i>");
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
                if (time.toLocaleDateString() != lstmd) {
                    lstmd = time.toLocaleDateString();
                    $("#content").append(`<h4><br>` + lstmd + `&nbsp;&nbsp;</h4>`);
                }
                $("#content").append("<div id=" + ((page - 1) * 20 + i) + " class='subcontainer sub-div notification' style='padding:0.8em 0.2em 0.2em 0.8em;'>\
                <p style='font-size:1.2em'>" + notifications[i].msg + "</p>\
                <p style='font-size:0.8em;color:#888888'>" + time.toLocaleString() + "</p>\
                </div>");
            }
            $(".more-btn").remove();
            if (r.nextpage != -1) $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn' onclick='ShowMore()'>Show More</a>");
            else $("#content").append("<a href='#" + (page * 20) + "' class='notification more-btn'>The End</a>");
            page = r.nextpage;
            updating = false;
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}