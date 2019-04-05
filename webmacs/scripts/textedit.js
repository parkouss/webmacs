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
textedit.EXTERNAL_EDITOR_REQUESTS = {};


textedit.clear_mark = function() {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.clear_mark", null);
    } else {
        if (! elt.isContentEditable) {
	          var pos = elt.selectionDirection == "forward" ? elt.selectionEnd : elt.selectionStart;
	          elt.setSelectionRange(pos, pos);
        } else {
	          let sel = document.getSelection();
	          if (! sel.isCollapsed) {
	              sel.collapse(sel.focusNode, sel.focusOffset);
	          }
        }
    }
}

textedit.blur = function() {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.blur", null);
    } else {
        elt.blur();
    }
}

textedit.copy_text = function(reset_selection) {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.copy_text", null);
    } else {
        let sel = document.getSelection();
        if (sel.type !== 'Range') {
	          return;
        }
        post_webmacs_message("copyToClipboard", [sel.toString()]);
        if (reset_selection) {
	          textedit.clear_mark();
        }
    }
}

textedit.select_text = function(direction, granularity) {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.select_text", null);
    } else {
        textedit.clear_mark();
        document.getSelection().modify("extend", direction, granularity);
    }
}

textedit._change_next_word_case = function(fn) {
    let elt = document.activeElement;
    textedit.select_text('forward', 'word');
    if (elt.isContentEditable) {
	      return;
    }
    var pos = elt.selectionStart;
    var txt = elt.value;
    var nextpos = elt.selectionEnd;
    elt.value = txt.slice(0, pos) + fn(txt.slice(pos, nextpos))
activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.upcase_word", null);
    } else {
        textedit._change_next_word_case(function(t) {
	          return t.toUpperCase();
        });
    }
}

textedit.downcase_word = function() {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.downcase_word", null);
    } else {
        textedit._change_next_word_case(function(t) {
	          return t.toLowerCase();
        });
    }
}

textedit.capitalize_word = function() {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.capitalize_word", null);
    } else {
        textedit._change_next_word_case(function(t) {
	          return t.toLowerCase().replace(/(?:^|\s)\S/g, function(a) {
	              return a.toUpperCase();
	          });
        });
    }
}

textedit.external_editor_open = function() {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.external_editor_open", null);
    } else {
        var id = new Date().getUTCMilliseconds() + "";
        let txt = (elt.isContentEditable) ?
	          elt.innerText : elt.value;
        post_webmacs_message("openExternalEditor", [id, txt]);
        textedit.EXTERNAL_EDITOR_REQUESTS[id] = elt;
    }
}

textedit.external_editor_finish = function(id, content) {
    let elt = document.activeElement;
    if (elt.tagName == "IFRAME") {
        post_message(elt.contentWindow, "textedit.external_editor_finish", [id, content]);
    } else {
        textedit._external_editor_finish([id, content]);
    }
}

textedit._external_editor_finish = function(args) {
    let id = args[0];
    let content = args[1];

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

if (self !== top) {
    register_message_handler("textedit.clear_mark", textedit.clear_mark);
    register_message_handler("textedit.blur", textedit.blur);
    register_message_handler("textedit.copy_text", textedit.copy_text);
    register_message_handler("textedit.select_text", textedit.select_text);
    register_message_handler("textedit.upcase_word", textedit.upcase_word);
    register_message_handler("textedit.downcase_word", textedit.downcase_word);
    register_message_handler("textedit.external_editor_open",
                             textedit.external_editor_open);
    register_message_handler("textedit.external_editor_finish",
                             textedit._external_editor_finish);
}
