var text_marks = {};

function set_or_unset_mark(e) {
    let enabled = !has_mark(e);
    text_marks[e] = enabled;
    if (!enabled) {
        var pos = e.selectionDirection == "forward" ? e.selectionEnd : e.selectionStart;
        e.setSelectionRange(pos, pos);
    }
}

function has_mark(e) {
    return text_marks[e];
}

function has_any_mark(e) {
    return has_mark(e) || (e.selectionEnd < e.selectionStart);
}

function _move_char(e, way) {
    let start = e.selectionStart;
    let end = e.selectionEnd;
    let direction = e.selectionDirection;
    if (end > start) {
        // there is a selection
        if (direction == "forward") {
            end = end + way;
        } else {
            start = start + way;
        }
    }
    else if (has_mark(e)) {
        // no selection yet, but in mark mode
        if (way > 0) {
            direction = "forward";
            end = end + way;
        } else {
            direction = "backward";
            start = start + way;
        }
    } else {
        // no selection
        direction = "none";
        end = end + way;
        start = end;
    }
    e.setSelectionRange(start, end, direction);
}

function forward_char(e) {
    _move_char(e, 1);
}

function backward_char(e) {
    _move_char(e, -1);
}

var LETTER_RE = /[A-Za-z0-9]/;

String.prototype.nextWordPosition = function(startpos) {
    var max = this.length;
    var foundletter = false;
    for (var i=startpos + 1; i < max; i++) {
        var char = this.charAt(i);
        if (char.search(LETTER_RE) != -1) {
            foundletter = true;
        }
        else if (foundletter) {
            return i;
        }
    }
    return max;
}

String.prototype.prevWordPosition = function(startpos) {
    var foundletter = false;
    for (var i=startpos - 1; i>=0; i--) {
        var char = this.charAt(i);
        if (char.search(LETTER_RE) != -1) {
            foundletter = true;
        }
        else if (foundletter) {
            return i+1;
        }
    }
    return 0;
}

function forward_word(e) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;
    var next_word_pos = e.value.nextWordPosition(pos);
    _move_char(e, next_word_pos - pos);
}

function backward_word(e) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;
    var prev_word_pos = e.value.prevWordPosition(pos);
    _move_char(e, prev_word_pos - pos);
}

function move_end_of_line(e) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;

    var eolpos = e.value.indexOf("\n", pos);
    if (eolpos == -1) eolpos = e.value.length;
    _move_char(e, eolpos - pos);
}

function move_beginning_of_line(e) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;

    var eolpos = e.value.lastIndexOf("\n", pos);
    if (eolpos == -1) eolpos = 0;
    _move_char(e, eolpos - pos);
}
