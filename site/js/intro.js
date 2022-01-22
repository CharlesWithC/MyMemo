// Copyright (C) 2021 Charles All rights reserved.
// Author: @Charles-1414
// License: GNU General Public License v3.0

var questions = [{
        "question": "adulting",
        "answer": "the action of becoming or acting like an adult"
    },
    {
        "question": "awe work",
        "answer": "taking a walk outside and making an effort to look at the things around you"
    },
    {
        "question": "contactless",
        "answer": "not having to physically touch or interact with people"
    },
    {
        "question": "doomscrolling",
        "answer": "reading the news on social media and expecting it to be bad – so much so that you become obsessed with looking at updates"
    },
    {
        "question": "PPE",
        "answer": "an abbreviation for personal protective equipment"
    },
    {
        "question": "quarenteen",
        "answer": "a teenager during the COVID-19 pandemic"
    },
    {
        "question": "thirsty",
        "answer": "having a need for attention or approval"
    },
    {
        "question": "ruthiness",
        "answer": "something that seems true but isn’t backed up by evidence"
    },
    {
        "question": "unconscious bias",
        "answer": "unconscious prejudice against people of a certain race, gender, or group"
    },
    {
        "question": "WFH",
        "answer": "an abbreviation for work (or working) from home"
    }
];
var qid = 0;
var ccCorrect = 0;
var disturbance = [];
var ccAnswered = false;
var ccCorrectAudio = new Audio('/audio/correct.mp3');
var ccWrongAudio = new Audio('/audio/wrong.mp3');

function DemoGetNext() {
    ccAnswered = false;
    $(".choice").css("background", "transparent");
    qid = parseInt(Math.random() * questions.length);
    $("#cc-question").html(questions[qid].answer);
    ccCorrect = parseInt(Math.random() * 4);
    $("#choice-" + ccCorrect).html(questions[qid].question);
    disturbance = [];
    for (var i = 0; i < 4; i++) {
        if (i == ccCorrect) continue;
        dis = parseInt(Math.random() * questions.length);
        while (dis == qid || disturbance.indexOf(dis) != -1)
            dis = parseInt(Math.random() * questions.length);
        disturbance.push(dis);
        $("#choice-" + i).html(questions[dis].question);
    }
}

function DemoChallengeChoice(userChoice) {
    $(".choice").css("background", "#cc0000");
    $("#div-choice-" + ccCorrect).css("background", "#00b300");
    if (ccAnswered) {
        DemoGetNext();
        return;
    }
    ccAnswered = true;
    if (userChoice == ccCorrect) {
        ccCorrectAudio.pause();
        ccCorrectAudio.currentTime = 0;
        ccCorrectAudio.play();
        setTimeout(DemoGetNext, 500);
    } else {
        ccWrongAudio.pause();
        ccWrongAudio.currentTime = 0;
        ccWrongAudio.play();
    }
}

function SetCookie(cName, cValue, expMinutes) {
    let date = new Date();
    date.setTime(date.getTime() + (expMinutes * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = cName + "=" + cValue + "; " + expires + "; path=/";
}

function GetCookie(cName) {
    const name = cName + "=";
    const cDecoded = decodeURIComponent(document.cookie); //to be careful
    const cArr = cDecoded.split('; ');
    let res;
    cArr.forEach(val => {
        if (val.indexOf(name) === 0) res = val.substring(name.length);
    })
    return res;
}

function PageInit() {
    if (GetCookie("version") == undefined) {
        $.ajax({
            url: "/api/version",
            method: 'GET',
            async: true,
            dataType: "json",
            success: function (r) {
                $("#version").html(r.version + '  <i class="fa fa-check-circle"></i>');
                SetCookie("version", r.version, 60);
            }
        });
    } else {
        $("#version").html(GetCookie("version") + '  <i class="fa fa-check-circle"></i>');
    }
    DemoGetNext();
}