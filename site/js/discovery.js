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
var curModalId = "";

var page = 1;
var pageLimit = 10;
var orderBy = "title";
var order = "asc";
var search = "";

function RefreshDiscovery(p = -1) {
    if (p != -1) page = p;
    $("#refresh-btn").html('<i class="fa fa-sync fa-spin"></i>');

    $.ajax({
        url: "/api/discovery",
        method: 'POST',
        async: true,
        dataType: "json",
        data: {
            page: page,
            pageLimit: pageLimit,
            orderBy: orderBy,
            order: order,
            search: search,
            userId: localStorage.getItem("userId"),
            token: localStorage.getItem("token")
        },
        success: function (r) {
            $("tbody tr").remove();
            discoveryList = r.data;
            total = r.total;
            totalD = r.totalD;
            toplist = r.toplist;
            l = ["", "Book", "Group"];
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
                atitle = "<a href='#' onclick='ShowDiscovery(" + discoveryList[i].discoveryId + ")'>" + discoveryList[i].title + "</a>"
                pin = '';
                if (discoveryList[i].pinned) pin = '<i class="fa fa-thumbtack"></i> ';
                AppendTableData("discoveryList", [pin, atitle, discoveryList[i].publisher, discoveryList[i].views, discoveryList[i].likes, btns], discoveryList[i].discoveryId)
            }
            l = (page - 1) * pageLimit + 1;
            r = l + discoveryList.length - 1;
            if (localStorage.getItem("isAdmin") != "1") $("#discoveryList tr > *:nth-child(6)").hide();
            PaginateTable("discoveryList", page, total, "RefreshDiscovery");
            if (discoveryList.length == 0) {
                l = 0;
                AppendTableData("discoveryList", ["No data available"], undefined, "100%");
            }
            SetTableInfo("discoveryList", "<p style='opacity:80%'>Showing " + l + " - " + r + " / " + totalD + "</p>");

            $(".discovery-top").remove();
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
                        ` + marked.parse(description) + `
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
            AjaxErrorHandler(r, textStatus, errorThrown);
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
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function UpdateDiscoveryQuestionList() {
    $(".title").html(`Discovery &nbsp;&nbsp;<button type="button"
    class="btn btn-outline-secondary" onclick="RefreshDiscovery()" id="refresh-btn"><i
        class="fa fa-sync"></i></button>`);

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
            $("#shareCode").html(shareCode +
                ' <button type="button" class="btn btn-primary btn-sm" onclick="CopyToClipboard(\'' + shareCode + '\')"><i class="fa fa-copy"></i></button>');
            $("#groupCode").html(shareCode +
                ' <button type="button" class="btn btn-primary btn-sm" onclick="CopyToClipboard(\'' + shareCode + '\')"><i class="fa fa-copy"></i></button>');

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

            questionList = r.preview;

            for (var i = 0; i < questionList.length; i++)
                AppendTableData("questionList", [marked.parse(questionList[i].question), marked.parse(questionList[i].answer)]);
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
        url: '/api/share/import',
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
                NotyNotification("Book imported!");
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
        }
    });
}

function ShowDiscovery(disid) {
    discoveryId = disid;
    $(".discovery-list").hide();
    $("#top-post").hide();
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
    curModalId = GenModal(`<i class="fa fa-edit"></i> Edit Post`,
        `<div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">Title</span>
            <input type="text" class="form-control" id="discovery-title" aria-describedby="basic-addon1">
        </div>
        <div class="form-group">
            <label for="discovery-description" class="col-form-label">Description:</label>
            <script>var descriptionMDE = new SimpleMDE({autoDownloadFontAwesome:false,spellChecker:false,tabSize:4});</script>
            <textarea class="form-control" id="discovery-description" style="height:10em"></textarea>
        </div>`,
        `<button id="publish-to-discovery-btn" type="button" class="btn btn-primary" onclick="UpdateInformation()">Edit</button>`)
    $("#discovery-title").val(title);
    $('#' + modalId).on('shown.bs.modal', function () {
        descriptionMDE.value(description);
    });
    BeautifyMarkdownEditor();
    OnSubmit("#discovery-title,#discovery-description", UpdateInformation, true);
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
                $('#' + curModalId).modal('hide');
            } else {
                NotyNotification(r.msg, type = 'error');
            }
        },
        error: function (r, textStatus, errorThrown) {
            AjaxErrorHandler(r, textStatus, errorThrown);
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

function Search() {
    search = $("#search-content").val();
    orderBy = "none";
    SortTable(orderBy);
    RefreshDiscovery(1);
}

function DiscoveryListSort(id) {
    orderBy = id;
    if ($("#sorting_" + id).hasClass("sorting-desc")) {
        order = "desc";
    } else {
        order = "asc";
    }
    RefreshDiscovery();
}

function UpdatePageLimit(pl) {
    if (pageLimit != pl) {
        page = Math.ceil((page - 1) * pageLimit / pl + 1);
        pageLimit = pl;
        RefreshDiscovery();
    }
}

function PageInit() {
    InitTable("discoveryList", [10, 25, 50, 100], 10, UpdatePageLimit, Search);
    InitSorting("discoveryList", ["title", "publisher", "views", "likes"], ["asc", undefined, undefined, undefined], "DiscoveryListSort");

    discoveryId = getUrlParameter("discoveryId");
    if (discoveryId == -1) {
        RefreshDiscovery();
        $(".discovery-list").show();
    } else {
        $(".discovery-list").hide();
        $(".discovery-detail").show();
        UpdateDiscoveryQuestionList();
    }
}