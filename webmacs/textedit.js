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
