var notifications = [];
var cur = 0;

function PageInit() {
    $("#refresh-btn-noti").html('<i class="fa fa-refresh fa-spin"></i>');
    $(".notification").remove();
    $.ajax({
        url: '/api/user/events',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            notifications = r;
            cur = Math.min(20, notifications.length);
            for (var i = 0; i < cur; i++) {
                var time = new Date(parseInt(notifications[i].timestamp) * 1000);
                $("#content").append("<div id="+i+" class='notification'>\
                <p style='font-size:1.2em'>" + notifications[i].msg + "</p>\
                <p style='font-size:0.8em;color:#888888'>" + time.toString() + "</p>\
                <hr>\
                </div>");
            }
            if(cur < notifications.length) $("#content").append("<a href='#"+(cur-1)+"' class='notification more-btn' onclick='ShowMore()'>Show More</a>");
            else $("#content").append("<a href='#"+(cur-1)+"' class='notification more-btn'>The End</a>");
            $("#refresh-btn-noti").html('<i class="fa fa-refresh"></i>');
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

function ShowMore(){
    nxt = Math.min(cur + 20, notifications.length);
    $(".more-btn").remove();
    for (var i = cur; i < nxt; i++) {
        var time = new Date(parseInt(notifications[i].timestamp) * 1000);
        $("#content").append("<div id="+i+" class='notification'>\
        <p style='font-size:1.2em'>" + notifications[i].msg + "</p>\
        <p style='font-size:0.8em;color:#888888'>" + time.toString() + "</p>\
        <hr>\
        </div>");
    }
    cur = nxt;
    if(cur < notifications.length) $("#content").append("<a href='#"+(cur-1)+"' class='notification more-btn' onclick='ShowMore()'>Show More</a>");
    else $("#content").append("<a href='#"+(cur-1)+"' class='notification more-btn'>The End</a>");
}