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
      return nodeName == "INPUT";
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

Hint.prototype.remove = function() {
    this.obj.style.background = this.objBackground;
    this.hint.parentNode.removeChild(this.hint);
}

Hint.prototype.setVisible = function(on) {
    if (on) {
        this.hint.style.display = "initial";
        this.obj.style.background = this.manager.options.background;
    } else {
        this.hint.style.display = "none";
        this.obj.style.background = this.objBackground;
    }
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
    if (this.activeHint) {
        this.activeHint.obj.style.background = this.options.background;
    }
    if (hint) {
        hint.obj.style.background = this.options.background_active;
    }
    this.activeHint = hint;
}

HintManager.prototype.activateNextHint = function(backward) {
    if (this.hints.length == 0) {
        return;
    }
    let pos = this.hints.indexOf(this.activeHint);
    if (pos == -1) {
        this.setActiveHint(this.hints[backward ? this.hints.length - 1 : 0]);
        return;
    }
    pos = pos + (backward ? -1 : 1);
    if (pos < 0) {
        pos = this.hints.length - 1;
    } else if (pos >= this.hints.length) {
        pos = 0;
    }
    this.setActiveHint(this.hints[pos]);
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
        } else {
            hint.setVisible(false);
        }
    }
}

HintManager.prototype.clearBrowserObjects = function() {
    for (let hint of this.hints) {
        hint.remove();
    }
    this.hints = [];
}

var hints = new HintManager();
