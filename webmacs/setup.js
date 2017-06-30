var webbuffer_id = null;
var socket = new WebSocket(webmacsBaseUrl);

socket.onclose = function() {
  console.log("web channel closed");
};
socket.onerror = function(error) {
  console.error("web channel error: " + error);
};
socket.onopen = function() {
  console.log("WebSocket connected, setting up QWebChannel.");
  new QWebChannel(socket, function(channel) {
    window.__webmacsHandler__ = channel.objects.contentHandler;

    function isTextInput(nodeName) {
      return nodeName == "INPUT" || nodeName == "TEXTAREA";
    }

    document.addEventListener("focus", function(e) {
      if (isTextInput(e.target.nodeName)) {
        __webmacsHandler__.onTextFocus(true);
      }
    }, true);

    document.addEventListener("blur", function(e) {
      if (isTextInput(e.target.nodeName)) {
        __webmacsHandler__.onTextFocus(false);
      }
    }, true);

      window.onfocus = function() {
          __webmacsHandler__.onBufferFocus(webbuffer_id);
      }
  });
};

function rectElementInViewport(node) {  // eslint-disable-line complexity
    var i;
    var boundingRect = (node.getClientRects()[0] ||
                        node.getBoundingClientRect());

    if (boundingRect.width <= 1 && boundingRect.height <= 1) {
        var rects = node.getClientRects();
        for (i = 0; i < rects.length; i++) {
            if (rects[i].width > rects[0].height &&
                rects[i].height > rects[0].height) {
                boundingRect = rects[i];
            }
        }
    }
    if (boundingRect === undefined) {
        return null;
    }
    var viewHeight = document.documentElement.clientHeight; // innerHeight
    var viewWidth = document.documentElement.clientWidth;  // innerWidth
    if (boundingRect.top > viewHeight || boundingRect.left > viewWidth) {
        return null;
    }
    if (boundingRect.width <= 1 || boundingRect.height <= 1) {
        var children = node.children;
        var visibleChildNode = false;
        for (i = 0; i < children.length; ++i) {
            boundingRect = (children[i].getClientRects()[0] ||
                            children[i].getBoundingClientRect());
            if (boundingRect.width > 1 && boundingRect.height > 1) {
                visibleChildNode = true;
                break;
            }
        }
        if (visibleChildNode === false) {
            return null;
        }
    }
    if (boundingRect.top + boundingRect.height < 10 ||
        boundingRect.left + boundingRect.width < -10) {
        return null;
    }
    var computedStyle = window.getComputedStyle(node, null);
    if (computedStyle.visibility !== "visible" ||
        computedStyle.display === "none" ||
        node.hasAttribute("disabled") ||
        parseInt(computedStyle.width, 10) === 0 ||
        parseInt(computedStyle.height, 10) === 0) {
        return null;
    }
    if (boundingRect.top < -20) {
        return null;
    }
    return boundingRect;
}

function escapeRegExp(str) {
    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function Hint(obj, manager, left, top) {
    this.obj = obj;
    this.objBackground = obj.style.background;
    obj.style.background = manager.options.background;
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
    } else {
        this.obj.style.background = this.objBackground;
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
        background_active: "#88FF00"
    };
    this.activeHint = null;
}

HintManager.prototype.selectBrowserObjects = function(selector, options) {
    Object.assign(this.options, options || {});
    let objs = document.body.querySelectorAll(selector);
    let scrollX = window.scrollX;
    let scrollY = window.scrollY;
    let fragment = document.createDocumentFragment();

    for (let obj of objs) {
        let rect = rectElementInViewport(obj);
        if (!rect) {
            continue;
        }
        var hint = new Hint(obj, this,
                            (rect.left + scrollX) + "px",
                            (rect.top + scrollY) + "px");
        this.hints.push(hint);
        fragment.appendChild(hint.hint);
    }
    this.setActiveHint((this.hints.length > 0) ? this.hints[0] : null);
    document.documentElement.appendChild(fragment);
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
