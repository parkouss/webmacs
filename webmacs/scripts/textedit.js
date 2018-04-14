// This file is part of webmacs.
//
// webmacs is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// webmacs is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with webmacs.  If not, see <http://www.gnu.org/licenses/>.

var text_marks = {};

var getActiveElement = function( doc ){
    doc = doc || document;

    var elt = doc.activeElement;
    if (elt.tagName == 'IFRAME') {
        return getActiveElement(elt.contentWindow.document);
    }
    return elt;
};

function set_or_unset_mark(e) {
    let enabled = !has_mark(e);
    if (!enabled) {
        delete text_marks[e];
        var pos = e.selectionDirection == "forward" ? e.selectionEnd : e.selectionStart;
        e.setSelectionRange(pos, pos);
    } else {
        text_marks[e] = true;
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

    var eolpos = e.value.lastIndexOf("\n", pos-1);
    if (eolpos == -1) eolpos = 0;
    else eolpos +=1;
    _move_char(e, eolpos - pos);
}

function delete_char(e) {
    var start = e.selectionStart, end = e.selectionEnd, pos;
    if (e.selectionDirection == "forward") {
        pos = end - (end - start);
    } else {
        pos = start;
    }
    if (end == start) {
        end = end + 1;
    }
    delete text_marks[e];
    var txt = e.value.slice(0, start) + e.value.slice(end);
    e.value = txt;
    e.setSelectionRange(pos, pos);
}

function delete_word(e) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;
    delete text_marks[e];
    var txt = e.value.slice(0, pos) +
        e.value.slice(e.value.nextWordPosition(pos));
    e.value = txt;
    e.setSelectionRange(pos, pos);
}

function delete_word_backward(e) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;
    delete text_marks[e];
    var delpos = e.value.prevWordPosition(pos);
    var txt = e.value.slice(0, delpos) + e.value.slice(pos);
    e.value = txt;
    e.setSelectionRange(delpos, delpos);
}

function copy_text(e, delselection) {
    var start = e.selectionStart, end = e.selectionEnd, pos;
    pos = e.selectionDirection == "forward" ? end : start;
    delete text_marks[e];
    if (start == end) { return; }
    var txt = e.value;
    __webmacsHandler__.copyToClipboard(txt.slice(start, end));
    if (delselection) {
        txt = txt.slice(0, start) + txt.slice(end);
        e.value = txt;
    }
    e.setSelectionRange(pos, pos);
}

function _change_next_word_case(e, fn) {
    var pos = e.selectionDirection == "forward" ? e.selectionEnd :
        e.selectionStart;
    delete text_marks[e];
    var txt = e.value;
    var nextpos = txt.nextWordPosition(pos);
    e.value = txt.slice(0, pos) + fn(txt.slice(pos, nextpos))
	+ txt.slice(nextpos);
    e.setSelectionRange(nextpos, nextpos);
}


function upcase_word(e) {
    _change_next_word_case(e, function(t) { return t.toUpperCase() });
}

function downcase_word(e) {
    _change_next_word_case(e, function(t) { return t.toLowerCase() });
}

function capitalize_word(e) {
    _change_next_word_case(e, function(t) {
	var startword = t.prevWordPosition(t.length - 1);
	if (startword > 0) {
	    return t.slice(0, startword) + t.charAt(startword).toUpperCase()
		+ t.slice(startword + 1).toLowerCase();
	} else {
	    return t.charAt(0).toUpperCase() + t.slice(1).toLowerCase();
	}
    });
}

var EXTERNAL_EDITOR_REQUESTS = {};

function external_editor_open(e) {
    var id = new Date().getUTCMilliseconds() + "";
    let txt = (e.isContentEditable) ?
	e.innerText : e.value;
    __webmacsHandler__.openExternalEditor(id, txt);
    EXTERNAL_EDITOR_REQUESTS[id] = e;
}

function external_editor_finish(id, content) {
    if (content !== false) {
	let e = EXTERNAL_EDITOR_REQUESTS[id];
	if (e.isContentEditable) {
	    e.innerText = content;
	} else {
	    e.value = content;
	}
    }
    delete EXTERNAL_EDITOR_REQUESTS[id];
}
