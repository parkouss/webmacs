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

class Hint {
    constructor(obj, manager, left, top, index) {
        this.obj = obj;
        this.objBackground = obj.style.background;
        this.objColor = obj.style.color;
        obj.style.background = manager.options.background;
        obj.style.color = manager.options.text_color;
        this.index = index;
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

    text() {
        if (this.obj.textContent) {
            return this.obj.textContent;
        }
        return null;
    }

    url() {
        if (this.obj.href) {
            return this.obj.href;
        }
        return null;
    }

    remove() {
        this.obj.style.background = this.objBackground;
        this.obj.style.color = this.objColor;
        this.hint.parentNode.removeChild(this.hint);
    }

    setVisible(on) {
        this.hint.style.display = on ? "initial" : "none";
        this.refresh();
    }

    refresh() {
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

    isVisible() {
        return this.hint.style.display != "none";
    }

    serialize() {
        return JSON.stringify({
            nodeName: this.obj.nodeName,
            text: this.text(),
            id: this.hint.textContent,
            url: this.url()
        });
    }
}



class HintFrame {
    constructor(frame) {
        this.frame = frame;
    }

    remove() {
        post_message(this.frame.contentWindow, "hints.select_clear", null);
    }
}


// took from conkeror
XPATH_NS = {
    xhtml: "http://www.w3.org/1999/xhtml",
    m: "http://www.w3.org/1998/Math/MathML",
    xul: "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul",
    svg: "http://www.w3.org/2000/svg"
};

function xpath_lookup_namespace (prefix) {
    return XPATH_NS[prefix] || null;
}


class Hinter {
    constructor() {
        this.options = {
            hint_background: "red",
            hint_color: "white",
            background: "yellow",
            background_active: "#88FF00",
            text_color: "black"
        };
    }

    init(selector) {
        this.selector = selector;
        this.xres = document.evaluate(selector, document, xpath_lookup_namespace,
                                      XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                                      null);
        this.fragment = document.createDocumentFragment();
        this.index = 0;
        this.hints = [];
        this.activeHint = null;
    }

    next(hint_index) {
        // has been cleared.
        if (this.hints === null) {
            return;
        }

        for (; this.index < this.xres.snapshotLength; this.index++) {
            let obj = this.xres.snapshotItem(this.index);
            let rect = rectElementInViewport(obj, window);
            if (!rect) {
                continue;
            }
            if (obj.tagName == "IFRAME") {
                post_message(obj.contentWindow, "hints.select_in_iframe_start",
                             {selector: this.selector, hint_index: hint_index});
                this.hints.push(new HintFrame(obj));
                this.index+=1;
                return;
            }
            hint_index += 1;
            var hint = new Hint(obj, this,
                                (rect.left + window.scrollX) + "px",
                                (rect.top + window.scrollY) + "px",
                                hint_index
                               );
            this.hints.push(hint);
            this.fragment.appendChild(hint.hint);
        }
        document.documentElement.appendChild(this.fragment);

        if (self !== top) {
            post_message(parent, "hints.select_in_iframe_end", hint_index);
        }
    }

    selectBrowserObjects(selector) {
        this.init(selector);
        this.next(0);
        this.activateNextHint(false);
    }

    clearBrowserObjects() {
        // has been cleared.
        if (this.hints === null) {
            return;
        }
        for (var hint of this.hints) {
            hint.remove();
        }
        this.hints = null;
    }

    frameUpActivateHint(indexes) {
        let hint = null;
        if (indexes !== null) {
            let index = indexes.shift();
            hint = this.hints[index];
        }
        let prev = this.activeHint;


        if (hint === prev) {
            return hint;
        }
        this.clearFrameSelection();

        this.activeHint = hint;
        if (top != self) {
            post_message(parent, "hints.frameUpActivateHint", indexes);
        }
        return hint;
    }

    clearFrameSelection() {
        let prevHint = this.activeHint;
        if (! prevHint) {
            return;
        }
        this.activeHint = null;
        if (prevHint instanceof Hint) {
            prevHint.refresh();
        } else {
            post_message(prevHint.frame.contentWindow,
                         "hints.clearFrameSelection");
        }
    }

    setCurrentActiveHint(indexes) {
        let hint = this.frameUpActivateHint(indexes);
        if (hint) {
            // refresh the hint style to make it appear activated.
            hint.refresh();
            post_webmacs_message("_browserObjectActivated", [hint.serialize()]);
        }
    }

    frameActivateNextHint(args) {
        let traverse = function(hinter, index) {
            let hint = hinter.hints[index];
            if (hint instanceof Hint) {
                if (hint.isVisible()) {
                    hinter.setCurrentActiveHint([index].concat(args.parent_indexes));
                    return true;
                }
            } else {
                let parent_indexes = args.parent_indexes;
                // this is a hint frame, so go down that frame
                post_message(hint.frame.contentWindow,
                             "hints.frameActivateNextHint", {
                                 // a list of ordered indexes of the calling
                                 // frame hint
                                 parent_indexes: [index].concat(args.parent_indexes),
                                 way: args.way
                             });
                return true;
            }
            return false;
        };


        let index = args.index;
        if (index === undefined) {
            if (this.activeHint) {
                // just go down on the current hint if it is a frame
                index = this.hints.indexOf(this.activeHint);

                // else, activate the next hint
                if (this.activeHint instanceof Hint) {
                    index += args.way;
                    // if we are out of bounds, and that this is the main frame,
                    // just loop.
                    if (self == top) {
                        if (index === -1 || index >= this.hints.length) {
                            index = args.way == 1 ? 0: this.hints.length - 1;
                        }
                    }
                }
            } else {
                // if no selection, select the first one
                index = args.way == 1 ? 0: this.hints.length - 1;
            }
        }

        if (args.way === 1) {
            for (; index < this.hints.length; index++) {
                if (traverse(this, index)) {
                    return;
                }
            }
        } else {
            for (; index >= 0; index--) {
                if (traverse(this, index)) {
                    return;
                }
            }
        }

        // we found no selection if we are here
        if (self !== top) {
            // recall the parent frame
            post_message(parent, "hints.frameActivateNextHint", {
                index: args.parent_indexes[0] + args.way,
                way: args.way
            });
        }
    }

    activateNextHint(backward) {
        this.frameActivateNextHint({
            way: backward ? -1 : 1,
            parent_indexes: [],
        });
    }

    followCurrentLink() {
        if (this.activeHint) {
            if (this.activeHint instanceof Hint) {
                clickLike(this.activeHint.obj);
            } else {
                post_message(this.activeHint.frame.contentWindow,
                             "hints.followCurrentLink");
            }
        }
    }

    frameSelectVisibleHint(args) {
        let frameHint = null;
        let index = args.index;

        for (let hint_index=0; hint_index < this.hints.length; hint_index++) {
            let hint = this.hints[hint_index];
            if (hint instanceof Hint) {
                let nb = parseInt(hint.hint.textContent);
                if (nb === index) {
                    this.setCurrentActiveHint([hint_index].concat(args.parent_indexes));
                    return;
                } else if (nb > index) {
                    if (frameHint) {
                        post_message(
                            frameHint.window,
                            "hints.frameSelectVisibleHint", {
                                index: index,
                                parent_indexes: [frameHint.index].concat(args.parent_indexes)
                            });
                    }
                    return;
                }
            } else {
                frameHint = {window: hint.frame.contentWindow, index: hint_index};
            }
        }
    }
    selectVisibleHint(index) {
        this.frameSelectVisibleHint({index: parseInt(index), parent_indexes: []});
    }

    frameFilterSelection(args) {
        let hint_index = args.hint_index;

        // match everything when text selector is empty
        let match_hint = hint => true;

        if (args.text) {
            // else, we fuzzy-match on the hint text
            let parts = args.text.split(/\s+/).map(escapeRegExp);
            let re = new RegExp(".*" + parts.join(".*") + ".*", "i");
            match_hint = function(hint) {
                let text = hint.text();
                if (text !== null) {
                    return (text.match(re) !== null);
                }
                return false;
            };
        }

        for (let index = args.index; index < this.hints.length; index++) {
            let hint = this.hints[index];
            if (hint instanceof HintFrame) {
                // iframe, let's go down
                post_message(hint.frame.contentWindow, "hints.frameFilterSelection", {
                    text: args.text,
                    index: 0,
                    parent_index: index,
                    hint_index: hint_index
                });
                return;
            }

            // else see if we match the hint, and update its visibility
            if (match_hint(hint)) {
                hint_index +=1;
                hint.setVisible(true);
                hint.hint.textContent = hint_index;
            } else {
                hint.setVisible(false);
                if (hint == this.activeHint) {
                    this.setCurrentActiveHint(null);
                }
            }
        }

        if (self !== top) {
            // if we are in a sub frame, we call back the parent so he will
            // continue.
            post_message(parent, "hints.frameFilterSelection", {
                text: args.text,
                index: args.parent_index + 1,
                hint_index: hint_index
            });
        } else {
            // else if we lose the selection, put it back to the first hint.
            if (this.activeHint === null) {
                this.activateNextHint(false);
            }
        }
    }

    filterSelection(text) {
        this.frameFilterSelection({
            text: text,
            index: 0,
            hint_index: 0,
        });
    }
}

var hints = new Hinter();

if (self !== top) {
    register_message_handler("hints.select_in_iframe_start", function(args) {
        hints.init(args.selector);
        hints.next(args.hint_index);
    });
    register_message_handler("hints.select_clear",
                             _ => hints.clearBrowserObjects());
    register_message_handler("hints.clearFrameSelection",
                             _ => hints.clearFrameSelection());
    register_message_handler("hints.frameSelectVisibleHint",
                             args => hints.frameSelectVisibleHint(args));
}
register_message_handler("hints.select_in_iframe_end",
                         hint_index => hints.next(hint_index));
register_message_handler("hints.frameActivateNextHint",
                         args => hints.frameActivateNextHint(args));
register_message_handler("hints.followCurrentLink",
                         _ => hints.followCurrentLink());
register_message_handler("hints.frameFilterSelection",
                         args => hints.frameFilterSelection(args));
register_message_handler("hints.frameUpActivateHint",
                         args => hints.frameUpActivateHint(args));
