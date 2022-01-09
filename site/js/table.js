// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

// Tabling Functions

function InitTable(table, select_val, select_default, select_func, search_func) {
    select_content = "";
    for (var i = 0; i < select_val.length; i++) {
        if (select_val[i] == select_default)
            select_content += "<option value=" + select_val[i] + " selected>" + select_val[i] + "</option>";
        else
            select_content += "<option value=" + select_val[i] + ">" + select_val[i] + "</option>";
    }
    $("#" + table).before("<div id='" + table + "_wrap' class='table_wrap'></div>");
    $("#" + table).appendTo("#" + table + "_wrap");
    $("#" + table).before(`<div id="` + table + `_range" class="table_range">
    <p>Show 
        <select name="` + table + `_range_select" id="` + table + `_range_select" class="form-select" style="display:inline-block;max-width:5em">
            ` + select_content + `
        </select>
        entries
    </p></div>`);
    $('#' + table + "_range_select").change(function () {
        select_func($(this).val());
    });
    $("#" + table).before(`<div id="` + table + `_search" class="table_search input-group mb-3" style="max-width:15em;">
        <span class="input-group-text" id="basic-addon1">Search</span>
        <input type="text" class="form-control" id="search-content" aria-describedby="basic-addon1">
        <div class="input-group-append">
            <button class="btn btn-outline-primary" type="button" onclick="` + search_func.name + `()">Go</button>
        </div>
    </div>`);
    $("#search-content").keypress(function (e) {
        if (e.which == 13 || e.which == 13 && e.ctrlKey) {
            search_func();
        }
    });

    $("#" + table).before("<div id='" + table + "_scroll' class='table_scroll'></div>");
    $("#" + table).appendTo("#" + table + "_scroll");
}

function InitSorting(table, sort_index, default_sort, func) {
    $("#" + table + " thead .sorting").each(function (e) {
        if (default_sort != undefined && default_sort[e] != undefined) {
            fasort = "";
            if (default_sort[e] == "desc") fasort = "down";
            else fasort = "up";
            $(this).append("  <i id='sorting_" + sort_index[e] + "' \
                onclick='SortTable(\"" + sort_index[e] + "\");" + func + "(\"" + sort_index[e] + "\")' \
                class='sorting-ctrl sorting-" + default_sort[e] + " fa fa-sort-" + fasort + "'></i>");
        } else {
            $(this).append("  <i id='sorting_" + sort_index[e] + "' \
                onclick='SortTable(\"" + sort_index[e] + "\");" + func + "(\"" + sort_index[e] + "\")' \
                class='sorting-ctrl sorting-both fa fa-sort'></i>");
        }
    })
}

function SortTable(id) {
    ctrl = $("#sorting_" + id);
    order = "asc";
    if (ctrl.hasClass("sorting-both") || ctrl.hasClass("sorting-desc")) {
        order = "asc";
    } else if (ctrl.hasClass("sorting-asc")) {
        order = "desc";
    }
    // clear other sort
    $(".sorting-asc").addClass("sorting-both");
    $(".sorting-desc").addClass("sorting-both");
    $(".sorting-both").removeClass("sorting-asc");
    $(".sorting-both").removeClass("sorting-desc");
    $(".sorting-both").addClass("fa-sort");
    $(".sorting-both").removeClass("fa-sort-up");
    $(".sorting-both").removeClass("fa-sort-down");
    if (id != "none") {
        // set sort
        ctrl.removeClass("sorting-both");
        ctrl.removeClass("fa-sort");
        ctrl.addClass("sorting-" + order);
        if (ctrl.hasClass("sorting-desc")) {
            ctrl.addClass("fa-sort-down");
        } else if (ctrl.hasClass("sorting-asc")) {
            ctrl.addClass("fa-sort-up");
        }
    }
}

function AppendTableData(table, data, id, colspan) {
    tradd = "";
    tdadd = "";
    if (id != undefined)
        tradd += "id='" + id + "'";
    if (colspan != undefined)
        tdadd += "colspan='" + colspan + "'";
    row = "<tr " + tradd + ">\n"
    for (var i = 0; i < data.length; i++)
        row += "<td " + tdadd + ">" + data[i] + "</td>\n";
    row += "</tr>\n"
    $("#" + table + " tbody").append(row);
}

function PaginateTable(table, current, total, func) {
    if ($("#" + table + "_paginate").length == 0) {
        $("#" + table + "_wrap").append("<div id='" + table + "_paginate' style='float:right'></div>");
        paginate = $("#" + table + "_paginate");
        paginate.append('<button id="table-first" type="button" class="btn btn-outline-primary btn-sm" onclick="' +
            func + '(1)"><i class="fa fa-angles-left"></i></button>');
        paginate.append('<button id="table-previous" type="button" class="btn btn-outline-primary btn-sm" onclick="' +
            func + '(' + Math.max(1, current - 1) + ')"><i class="fa fa-angle-left"></i></button>');
        paginate.append('<button id="table-next" type="button" class="btn btn-outline-primary btn-sm" onclick="' +
            func + '(' + Math.min(total, current + 1) + ')"><i class="fa fa-angle-right"></i></button>');
        paginate.append('<button id="table-last" type="button" class="btn btn-outline-primary btn-sm" onclick="' +
            func + '(' + total + ')"><i class="fa fa-angles-right"></i></button>');
    } else {
        $("#table-first").attr("onclick", func + '(1)');
        $("#table-previous").attr("onclick", func + '(' + Math.max(1, current - 1) + ')');
        $("#table-next").attr("onclick", func + '(' + Math.max(1, current + 1) + ')');
        $("#table-last").attr("onclick", func + '(' + total + ')');
    }
    if (current == 1) {
        $("#table-previous").attr("disabled", "disabled");
        $("#table-first").attr("disabled", "disabled");
    } else {
        $("#table-previous").removeAttr("disabled");
        $("#table-first").removeAttr("disabled");
    }
    if (current == total) {
        $("#table-next").attr("disabled", "disabled");
        $("#table-last").attr("disabled", "disabled");
    } else {
        $("#table-next").removeAttr("disabled");
        $("#table-last").removeAttr("disabled");
    }

    l = Math.max(1, current - 3);
    r = Math.min(total, current + 3);
    if (total > 7) {
        if (current - 3 < 1)
            r += 4 - current;
        if (current + 3 > total)
            l -= 4 - total + current;
        if (l < 1)
            l = 1;
        if (r > total)
            r = total;
    } else {
        l = 1;
        r = total;
    }
    $(".table-btn-middle").remove();
    $("#table-previous").after('<button id="table-' + l + '" type="button" class="btn btn-outline-primary btn-sm table-btn-middle" onclick="' +
        func + '(' + l + ')">' + l + '</button>');
    for (var i = l + 1; i <= r; i++) {
        $("#table-" + (i - 1)).after('<button id="table-' + i + '" type="button" class="btn btn-outline-primary btn-sm table-btn-middle" onclick="' +
            func + '(' + i + ')">' + i + '</button>');
    }
    $("#table-" + current).attr("disabled", "disabled");
}

function SetTableInfo(table, content) {
    if ($("#" + table + "_info").length != 0)
        $("#" + table + "_info").remove();
    $("#" + table + "_paginate").before("<div id='" + table + "_info' style='float:left;font-size:0.8em'></div>");
    info = $("#" + table + "_info");
    info.append(content);
}