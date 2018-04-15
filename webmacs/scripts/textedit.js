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


var getActiveElement = function( doc ){
    doc = doc || document;

    var elt = doc.activeElement;
    if (elt.tagName == 'IFRAME') {
        return getActiveElement(elt.contentWindow.document);
    }
    return elt;
};

function clear_mark(e) {
    if (e.selectionDirection) {
	var pos = e.selectionDirection == "forward" ? e.selectionEnd : e.selectionStart;
	e.setSelectionRange(pos, pos);
    } else {
	let sel = e.ownerDocument.getSelection();
	if (! sel.isCollapsed) {
	    sel.collapse(sel.focusNode, sel.focusOffset);
	}
    }
}

function select_text(e, direction, granularity) {
    clear_mark(e);
    let sel = e.ownerDocument.getSelection();
    sel.modify("extend", direction, granularity);
}

function copy_text(e, reset_selection) {
    let sel = e.ownerDocument.getSelection();
    if (sel.type !== 'Range') {
	return;
    }
    __webmacsHandler__.copyToClipboard(sel.toString());
    if (reset_selection) {
	clear_mark(e);
    }
}

function _change_next_word_case(e, fn) {
    select_text(e, 'forward', 'word');
    var pos = e.selectionStart;
    var txt = e.value;
    var nextpos = e.selectionEnd;
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
	return t.charAt(0).toUpperCase() + t.substring(1).toLowerCase();
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
