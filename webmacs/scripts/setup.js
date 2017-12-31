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

function registerWebmacs(w) {
    console.log("registering...");
    window.__webmacsHandler__ = w;

    function isTextInput(node) {
        return node.isContentEditable
            || node.nodeName == "INPUT" || node.nodeName == "TEXTAREA";
    }

    document.addEventListener("focusin", function(e) {
        if (isTextInput(e.target)) {
            __webmacsHandler__.onTextFocus(true);
        }
    }, true);

    document.addEventListener("focusout", function(e) {
        if (isTextInput(e.target)) {
            __webmacsHandler__.onTextFocus(false);
        }
    }, true);

    window.onfocus = function() {
        __webmacsHandler__.onBufferFocus();
    };

    if (self != top) {return;}

    // force the focus on the current web content
    if (document.activeElement && isTextInput(document.activeElement)) {
	__webmacsHandler__.onTextFocus(true);
    } else {
	__webmacsHandler__.onTextFocus(false);
    }

    var event = document.createEvent('Event');
    event.initEvent('_webmacs_external_created', true, true);
    document.dispatchEvent(event);
}

function registerExternal(channel) {
    registerWebmacs(channel.objects.contentHandler);
}

function registerWebChannel() {
    try {
        new QWebChannel(qt.webChannelTransport, registerExternal);
    } catch (e) {
        setTimeout(registerWebChannel, 50);
    }
}

if (self != top) {
    if (top.__webmacsHandler__) {
        registerWebmacs(top.__webmacsHandler__);
    } else {
        top.document.addEventListener('_webmacs_external_created', function() {
            registerWebmacs(top.__webmacsHandler__);
        })
    }
} else {
    registerWebChannel();
}


function clickLike(elem) {
    elem.focus();
    var doc = elem.ownerDocument;
    var view = doc.defaultView;

    var evt = doc.createEvent("MouseEvents");
    evt.initMouseEvent("mousedown", true, true, view, 1, 0, 0, 0, 0, /*ctrl*/ 0, /*event.altKey*/0,
                       /*event.shiftKey*/ 0, /*event.metaKey*/ 0, 0, null);
    elem.dispatchEvent(evt);

    evt = doc.createEvent("MouseEvents");
    evt.initMouseEvent("click", true, true, view, 1, 0, 0, 0, 0, /*ctrl*/ 0, /*event.altKey*/0,
                       /*event.shiftKey*/ 0, /*event.metaKey*/ 0, 0, null);
    elem.dispatchEvent(evt);

    evt = doc.createEvent("MouseEvents");
    evt.initMouseEvent("mouseup", true, true, view, 1, 0, 0, 0, 0, /*ctrl*/ 0, /*event.altKey*/0,
                       /*event.shiftKey*/ 0, /*event.metaKey*/ 0, 0, null);
    elem.dispatchEvent(evt);
}

function rectElementInViewport(elem, w) {  // eslint-disable-line complexity
    var win = elem.ownerDocument.defaultView;
    var rect = elem.getBoundingClientRect();
    w = w || window;

    if (!rect ||
        rect.top > w.innerHeight ||
        rect.bottom < 0 ||
        rect.left > w.innerWidth ||
        rect.right < 0) {
        return null;
    }

    rect = elem.getClientRects()[0];
    if (!rect) {
        return null;
    }

    var style = win.getComputedStyle(elem, null);
    if (style.getPropertyValue("visibility") !== "visible" ||
        style.getPropertyValue("display") === "none" ||
        style.getPropertyValue("opacity") === "0") {
        return null;
    }
    return rect;
}

function escapeRegExp(str) {
    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function Hint(obj, manager, left, top) {
    this.obj = obj;
    this.objBackground = obj.style.background;
    this.objColor = obj.style.color;
    obj.style.background = manager.options.background;
    obj.style.color = manager.options.text_color;
    this.index = manager.hints.length + 1;
    var hint = document.createElement("span");
    hint.textContent = this.index;
    hint.style.background = manager.options.hint_background;
    hint.style.color = manager.options.hint_color;
    hint.style.position = "absolute";
    hint.style.zIndex = "2147483647";
    hint.style.left = left;
    hint.style.top = top;
    this.hint = hint;
    this.manager = manager;
}

Hint.prototype.text = function() {
    if (this.obj.textContent) {
        return this.obj.textContent;
    }
    return null;
}

Hint.prototype.url = function() {
    if (this.obj.href) {
        return this.obj.href;
    }
    return null;
}

Hint.prototype.remove = function() {
    this.obj.style.background = this.objBackground;
    this.obj.style.color = this.objColor;
    this.hint.parentNode.removeChild(this.hint);
}

Hint.prototype.setVisible = function(on) {
    this.hint.style.display = on ? "initial" : "none";
    this.refresh();
}

Hint.prototype.refresh = function() {
    if (this.isVisible()) {
        if (this.manager.activeHint == this) {
            this.obj.style.background = this.manager.options.background_active;
        } else {
            this.obj.style.background = this.manager.options.background;
        }
        this.obj.style.color = this.manager.options.text_color;
    } else {
        this.obj.style.background = this.objBackground;
        this.obj.style.color = this.objColor;
    }
}

Hint.prototype.isVisible = function() {
    return this.hint.style.display != "none";
}

Hint.prototype.serialize = function() {
    return JSON.stringify({
        nodeName: this.obj.nodeName,
        text: this.text(),
        id: this.hint.textContent,
        url: this.url()
    });
}

function HintManager() {
    this.hints = [];
    this.options = {
        hint_background: "red",
        hint_color: "white",
        background: "yellow",
        background_active: "#88FF00",
        text_color: "black"
    };
    this.activeHint = null;
}

// took from conkeror
XHTML_NS = "http://www.w3.org/1999/xhtml";
XUL_NS = "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul";
MATHML_NS = "http://www.w3.org/1998/Math/MathML";
XLINK_NS = "http://www.w3.org/1999/xlink";
SVG_NS = "http://www.w3.org/2000/svg";

function xpath_lookup_namespace (prefix) {
    return {
        xhtml: XHTML_NS,
        m: MATHML_NS,
        xul: XUL_NS,
        svg: SVG_NS
    }[prefix] || null;
}

HintManager.prototype.selectBrowserObjecsInWindow = function(w, selector) {
    var doc = w.document;
    let xres = doc.evaluate (selector, doc, xpath_lookup_namespace,
                             XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    let scrollX = window.scrollX;
    let scrollY = window.scrollY;
    let fragment = doc.createDocumentFragment();

    for (var j = 0; j < xres.snapshotLength; j++) {
        let obj = xres.snapshotItem(j);
        let rect = rectElementInViewport(obj, w);
        if (!rect) {
            continue;
        }
        if (obj.tagName == "IFRAME") {
            this.selectBrowserObjecsInWindow(obj.contentWindow, selector);
            continue;
        }
        var hint = new Hint(obj, this,
                            (rect.left + scrollX) + "px",
                            (rect.top + scrollY) + "px");
        this.hints.push(hint);
        fragment.appendChild(hint.hint);
    }
    doc.documentElement.appendChild(fragment);
}

HintManager.prototype.selectBrowserObjects = function(selector, options) {
    Object.assign(this.options, options || {});
    this.selectBrowserObjecsInWindow(window, selector);
    this.setActiveHint((this.hints.length > 0) ? this.hints[0] : null);
}

HintManager.prototype.setActiveHint = function(hint) {
    var prevActive = this.activeHint;
    this.activeHint = hint;
    if (prevActive) { prevActive.refresh(); }
    if (hint) {
        hint.refresh();
        __webmacsHandler__._browserObjectActivated(hint.serialize());
    }
}

HintManager.prototype.visibleHints = function() {
    let visibles = [];
    for (let hint of this.hints) {
        if (hint.isVisible()) {
            visibles.push(hint);
        }
    }
    return visibles;
}

HintManager.prototype.selectVisibleHint = function(index) {
    for (let hint of this.visibleHints()) {
        if (hint.hint.textContent == index) {
            this.setActiveHint(hint);
            return;
        }
    }
    this.setActiveHint(null);
}

HintManager.prototype.activateNextHint = function(backward) {
    let visibles = this.visibleHints();
    if (visibles.length == 0) {
        return;
    }
    let pos = visibles.indexOf(this.activeHint);
    if (pos == -1) {
        this.setActiveHint(visibles[backward ? visibles.length - 1 : 0]);
        return;
    }
    pos = pos + (backward ? -1 : 1);
    if (pos < 0) {
        pos = visibles.length - 1;
    } else if (pos >= visibles.length) {
        pos = 0;
    }
    this.setActiveHint(visibles[pos]);
}

HintManager.prototype.filterSelection = function(text) {
    let i = 0;
    if (!text) {
        for (let hint of this.hints) {
            i = i+1;
            hint.setVisible(true);
            hint.hint.textContent = i;
        }
        return;
    }
    let activeHintRemoved = false;
    let firstHint = null;
    var parts = text.split(/\s+/).map(escapeRegExp);
    var re = new RegExp(".*" + parts.join(".*") + ".*", "i");
    for (let hint of this.hints) {
        let matched = false;
        text = hint.text();
        if (text !== null) {
            matched = (text.match(re) !== null);
        }

        if (matched) {
            i = i+1;
            hint.setVisible(true);
            hint.hint.textContent = i;
            if (! firstHint) {
                firstHint = hint;
            }
        } else {
            hint.setVisible(false);
            if (hint == this.activeHint) {
                activeHintRemoved = true;
            }
        }
    }
    if (activeHintRemoved && firstHint) {
        this.setActiveHint(firstHint);
    }
}

HintManager.prototype.clearBrowserObjects = function() {
    for (let hint of this.hints) {
        hint.remove();
    }
    this.hints = [];
}

var hints = new HintManager();
