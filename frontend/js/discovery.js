// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var discoveryId = -1;
var discoveryList = [];
var liked = false;
var shareCode = "";
var distype = 1;
var title = "";
var description = "";

var search = "";
var page = 1;
var pagelen = 10;
var total = 1;

function RefreshDiscovery(p = -1) {
    if (p != -1) {
        page = p;
    }
    $("#refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');

    table = $("#discoveryList").DataTable();
    table.clear();
    if (p == -1) {
        table.row.add([
            [""],
            [""],
            ["Loading <i class='fa fa-spinner fa-spin'></i>"],
            [""],
            [""],
            [""]
        ]);
        table.draw();
    }

    $.ajax({
            url: "/api/discovery",
            method: 'POST',
            async: true,
            dataType: "json",
            data: {
                search: search,
                page: page,
                pagelen: pagelen,
                userId: localStorage.getItem("userId"),
                token: localStorage.getItem("token")
            },
            success: function (r) {
                table.clear();
                discoveryList = r.data;
                total = r.total;
                l = ["", "Book", "Group"];
                for (var i = 1; i < page; i++) {
                    for (var j = 0; j < pagelen; j++) {
                        table.row.add([
                            ["&nbsp;"],
                            [""],
                            [""],
                            [""],
                            [""],
                            [""]
                        ]);
                    }
                }
                for (var i = 0; i < discoveryList.length; i++) {
                    btns = '';
                    if (localStorage.getItem("isAdmin") == "1" || discoveryList[i].publisher == localStorage.getItem("username")) {
                        if (!discoveryList[i].pinned) {
                            btns += '&nbsp;&nbsp;<button id="admin-pin-' + discoveryList[i].discoveryId + '" class="btn btn-primary btn-sm" type="button" onclick="AdminPin(' + discoveryList[i].discoveryId + ',1)"><i class="fa fa-thumbtack"></i> Pin</button>';
                        } else {
                            btns += '&nbsp;&nbsp;<button id="admin-pin-' + discoveryList[i].discoveryId + '" class="btn btn-primary btn-sm" type="button" onclick="AdminPin(' + discoveryList[i].discoveryId + ',0)"><i class="fa fa-thumbtack fa-rotate-180"></i> Unpin</button>';
                        }
                        btns += '&nbsp;&nbsp;<button id="admin-delete-' + discoveryList[i].discoveryId + '" class="btn btn-danger btn-sm" type="button" onclick="AdminUnpublishDiscoveryConfirm(' + discoveryList[i].discoveryId + ')"><i class="fa fa-trash"></i> Delete</button>';
                    }
                    pin = '';
                    if (discoveryList[i].pinned) {
                        pin = '<i class="fa fa-thumbtack"></i> ';
                    }
                    table.row.add([
                        [pin],
                        ["<a href='#' onclick='ShowDiscovery(" + discoveryList[i].discoveryId + ")'>" + discoveryList[i].title + "</a>"],
                        [discoveryList[i].publisher],
                        [discoveryList[i].views],
                        [discoveryList[i].likes],
                        [btns]
                    ]).node().id = discoveryList[i].discoveryId;
                }
                for (var i = page; i < total; i++) {
                    for (var j = 0; j < pagelen; j++) {
                        table.row.add([
                            ["&nbsp;"],
                            [""],
                            [""],
                            [""],
                            [""],
                            [""]
                        ]);
                    }
                }

                table.draw();

                for (var i = 1; i < page; i++) {
                    $("#discoveryList_next").click();
                }

                $(".discovery-top").remove();
                toplist = r.toplist;
                if (toplist.length > 0) {
                    $("#dlist").addClass("sub-left");
                    $("#top-post").fadeIn();
                }

                for (var i = 0; i < toplist.length; i++) {
                    title = "";
                    description = "";
                    info = "";
                    title = toplist[i].title;
                    description = toplist[i].description;
                    info = toplist[i].views + " <i class='fa fa-eye'></i>&nbsp;&nbsp;" + toplist[i].likes + " <i class='fa fa-heart'></i>";
                    $("#top-post").append(`<div class="rect discovery-top" href="#" onclick="ShowDiscovery(` + toplist[i].discoveryId + `);">
                        <p class="rect-title">` + title + `</p>
                        <p class="rect-content">&nbsp;&nbsp;` + marked.parse(description) + `</p>
                        <p class="rect-content">&nbsp;&nbsp;` + info + `</p>
                        </div>`);
                }

            $("#refresh-btn").html('<i class="fa fa-sync"></i>');
        }
    });
}

function AdminPin(disid, op) {
    l = ["unpin", "pin"];
    $.ajax({
        url: '/api/discovery/pin',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: disid,
            operation: l[op],
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                RefreshDiscovery();

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
}

function AdminUnpublishDiscoveryConfirm(disid) {
    $("#admin-delete-" + disid).html("Confirm?");
    $("#admin-delete-" + disid).attr("onclick", "AdminUnpublishDiscovery(" + disid + ");");
}

function AdminUnpublishDiscovery(disid) {
    publisher = "";
    for (var i = 0; i < discoveryList.length; i++) {
        if (discoveryList[i].discoveryId == disid) {
            publisher = discoveryList[i].publisher;
            break;
        }
    }
    if (localStorage.getItem("isAdmin") != "1" && publisher != localStorage.getItem("username")) {
        return;
    }
    $.ajax({
        url: '/api/discovery/unpublish',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: disid,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                RefreshDiscovery();

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
}

function UpdateDiscoveryQuestionList() {
    $(".title").html(`Discovery &nbsp;&nbsp;<button type="button"
    class="btn btn-outline-secondary" onclick="RefreshDiscovery()" id="refresh-btn"><i
        class="fa fa-sync"></i></button>`);
    table = $("#questionList").DataTable();
    table.clear();
    table.row.add([
        ["Loading <i class='fa fa-spinner fa-spin'></i>"],
        [""]
    ]);
    table.draw();

    $.ajax({
        url: "/api/discovery/" + discoveryId,
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
                $(".discovery-detail").hide();
                $(".discovery-list").fadeIn();
                RefreshDiscovery();
                window.history.pushState("My Memo", "My Memo", "/discovery");
                return;
            }
            table.clear();
            title = r.title;
            description = r.description;
            liked = r.liked;
            if (liked) {
                $(".title").html(r.title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
            } else {
                $(".title").html(r.title + ' <a href="#" onclick="LikePost()"><i class="far fa-heart" style="color:red"></i></a>');
            }
            $("#detail-publisher").html(r.publisher);
            $("#detail-description").html(marked.parse(r.description));
            $("#detail-views").html(r.views);
            $("#detail-likes").html(r.likes);
            $("#detail-imports").html(r.imports);
            if (r.type == 1) {
                $("#detail-imports-name").html("Imports");
            } else if (r.type == 2) {
                $("#detail-imports-name").html("Members");
            }

            shareCode = r.shareCode;
            $("#shareCode").html(shareCode);
            $("#groupCode").html(shareCode);

            if (r.isPublisher || localStorage.getItem("isAdmin") == "1") {
                $(".publisher-only").show();
            } else {
                $(".publisher-only").hide();
            }

            if (localStorage.getItem("userId") == null) {
                $(".user-only").hide();
            } else {
                $(".user-only").show();
                distype = r.type;
                if (distype == 1) {
                    $(".book-only").show();
                    $(".group-only").hide();
                } else if (distype == 2) {
                    $(".book-only").hide();
                    $(".group-only").show();
                }
            }

            questionList = r.questions;

            for (var i = 0; i < questionList.length; i++) {
                table.row.add([
                    [questionList[i].question.replaceAll("\n", "<br>")],
                    [questionList[i].answer.replaceAll("\n", "<br>")]
                ]);
            }
            table.draw();
        },
        error: function (r, textStatus, errorThrown) {
            NotyNotification('Error ' + r.status + ": " + errorThrown, type = 'error');
            $(".discovery-list").show();
            $(".discovery-detail").hide();
            discoveryId = -1;
        }
    });
}

function ImportBook() {
    $.ajax({
        url: '/api/book/create',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            name: shareCode,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                NotyNotification("Success! Book imported!");
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

function ShowDiscovery(disid) {
    discoveryId = disid;
    $(".discovery-list").hide();
    $(".discovery-detail").fadeIn();
    UpdateDiscoveryQuestionList();
    window.history.pushState("My Memo", "My Memo", "/discovery?discoveryId=" + disid);
}

function BackToList() {
    $(".title").html(`Discovery &nbsp;&nbsp;<button type="button"
    class="btn btn-outline-secondary" onclick="RefreshDiscovery()" id="refresh-btn"><i
        class="fa fa-sync"></i></button>`);
    $(".discovery-detail").hide();
    $(".discovery-list").fadeIn();
    RefreshDiscovery();
    window.history.pushState("My Memo", "My Memo", "/discovery");
}

function UpdateInformationShow() {
    $("#content").after(`<div class="modal fade" id="modal" tabindex="-1" role="dialog" aria-labelledby="modalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="modalLabel"><i class="fa fa-edit"></i> Edit Post</h5>
                    <button type="button" class="close" style="background-color:transparent;border:none" data-dismiss="modal" aria-label="Close"
                        onclick="$('#modal').modal('hide')">
                        <span aria-hidden=" true"><i class="fa fa-times"></i></span>
                    </button>
                </div>
                <div class="modal-body">
                    <form>
                        <div class="input-group mb-3">
                            <span class="input-group-text" id="basic-addon1">Title</span>
                            <input type="text" class="form-control" id="discovery-title" aria-describedby="basic-addon1">
                        </div>
                        <div class="form-group">
                            <label for="discovery-description" class="col-form-label">Description:</label>
                            <script>var descriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
                            <textarea class="form-control" id="discovery-description"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                        onclick="$('#modal').modal('hide')">Close</button>
                    <button id="publish-to-discovery-btn" type="button" class="btn btn-primary"
                        onclick="UpdateInformation()">Edit <i class="fa fa-paper-plane"></i></button>
                </div>
            </div>
        </div>
    </div>`);
    $("#discovery-title").val(title);
    $("#modal").modal("show");
    $('#modal').on('hidden.bs.modal', function () {
        $("#modal").remove();
    });
    $(".editor-toolbar").css("background-color", "white");
    $(".editor-toolbar").css("opacity", "1");
    $(".cursor").remove();
    $('#modal').on('shown.bs.modal', function () {
        descriptionMDE.value(description);
    });

    $("#discovery-title,#discovery-description").on('keypress', function (e) {
        if (e.which == 13 && e.ctrlKey) {
            UpdateInformation();
        }
    });
}

function UpdateInformation() {
    title = $("#discovery-title").val();
    description = descriptionMDE.value();

    $.ajax({
        url: '/api/discovery/update',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: discoveryId,
            title: title,
            description: description,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                if (liked) {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
                } else {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="far fa-heart" style="color:red"></i></a>');
                }
                $("#detail-description").html(marked.parse(description));

                NotyNotification(r.msg);
                $('#modal').modal('hide');
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

function LikePost() {
    liked = 1 - liked;
    if (liked) {
        $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
    } else {
        $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="far fa-heart" style="color:red"></i></a>');
    }
    $.ajax({
        url: '/api/discovery/like',
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            discoveryId: discoveryId,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            if (r.success == true) {
                liked = r.liked;
                if (liked) {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
                } else {
                    $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="far fa-heart" style="color:red"></i></a>');
                }

                NotyNotification(r.msg);
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            liked = 1 - liked;
            if (liked) {
                $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="fa fa-heart" style="color:red"></i></a>');
            } else {
                $(".title").html(title + ' <a href="#" onclick="LikePost()"><i class="far fa-heart" style="color:red"></i></a>');
            }
        }
    });
}

function CustomizePaginateBtn() {
    $("#discoveryList_paginate > span > a").each(function () {
        $(this).attr("id", $(this).text());
        $(this).attr("onclick", "RefreshDiscovery(" + $(this).text() + ");");
    });
    $("#discoveryList_first").attr("onclick", "RefreshDiscovery(1);");
    $("#discoveryList_previous").attr("onclick", "RefreshDiscovery(" + (page - 1) + ");");
    $("#discoveryList_next").attr("onclick", "RefreshDiscovery(" + (page + 1) + ");");
    $("#discoveryList_last").attr("onclick", "RefreshDiscovery(" + total + ");");
}

function Search() {
    search = $("#search-content").val();
    RefreshDiscovery(1);
}

function PageInit() {
    discoveryId = getUrlParameter("discoveryId");
    if (discoveryId == -1) {
        RefreshDiscovery();
        setInterval(CustomizePaginateBtn, 50);
    } else {
        $(".discovery-list").hide();
        $(".discovery-detail").show();
        UpdateDiscoveryQuestionList();
    }
}