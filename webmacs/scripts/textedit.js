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

var textedit = {};

textedit.context = function() {
    let e = textedit.getActiveElement();
    return {
	element: e,
	sel: e. ownerDocument.getSelection(),
	isContentEditable: e.isContentEditable
    }
}

textedit.getActiveElement = function( doc ){
    doc = doc || document;

    var elt = doc.activeElement;
    if (elt.tagName == 'IFRAME') {
        return getActiveElement(elt.contentWindow.document);
    }
    return elt;
};

textedit.clear_mark = function(ctx) {
    ctx = ctx || textedit.context();
    if (! ctx.isContentEditable) {
	let e = ctx.element;
	var pos = e.selectionDirection == "forward" ? e.selectionEnd : e.selectionStart;
	e.setSelectionRange(pos, pos);
    } else {
	let sel = ctx.sel;
	if (! sel.isCollapsed) {
	    sel.collapse(sel.focusNode, sel.focusOffset);
	}
    }
}

textedit.select_text = function(direction, granularity, ctx) {
    ctx = ctx || textedit.context();
    textedit.clear_mark(ctx);
    ctx.sel.modify("extend", direction, granularity);
}

textedit.copy_text = function(reset_selection, ctx) {
    ctx = ctx || textedit.context();
    let sel = ctx.sel;
    if (sel.type !== 'Range') {
	return;
    }
    __webmacsHandler__.copyToClipboard(sel.toString());
    if (reset_selection) {
	textedit.clear_mark(ctx);
    }
}

textedit._change_next_word_case = function(ctx, fn) {
    ctx = ctx || textedit.context();
    textedit.select_text('forward', 'word', ctx);
    if (ctx.isContentEditable) {
	return;
    }
    let e = ctx.element;
    var pos = e.selectionStart;
    var txt = e.value;
    var nextpos = e.selectionEnd;
    e.value = txt.slice(0, pos) + fn(txt.slice(pos, nextpos))
	+ txt.slice(nextpos);
    e.setSelectionRange(nextpos, nextpos);
}


textedit.upcase_word = function(ctx) {
    textedit._change_next_word_case(ctx, function(t) {
	return t.toUpperCase();
    });
}

textedit.downcase_word = function(ctx) {
    textedit._change_next_word_case(ctx, function(t) {
	return t.toLowerCase();
    });
}

textedit.capitalize_word = function(ctx) {
    textedit._change_next_word_case(ctx, function(t) {
	return t.toLowerCase().replace(/(?:^|\s)\S/g, function(a) {
	    return a.toUpperCase();
	});
    });
}

textedit.EXTERNAL_EDITOR_REQUESTS = {};

textedit.external_editor_open = function(ctx) {
    ctx = ctx || textedit.context();
    var id = new Date().getUTCMilliseconds() + "";
    let e = ctx.element;
    let txt = (ctx.isContentEditable) ?
	e.innerText : e.value;
    __webmacsHandler__.openExternalEditor(id, txt);
    textedit.EXTERNAL_EDITOR_REQUESTS[id] = e;
}

textedit.external_editor_finish = function(id, content) {
    if (content !== false) {
	let e = textedit.EXTERNAL_EDITOR_REQUESTS[id];
	if (e.isContentEditable) {
	    e.innerText = content;
	} else {
	    e.value = content;
	}
    }
    delete textedit.EXTERNAL_EDITOR_REQUESTS[id];
}
