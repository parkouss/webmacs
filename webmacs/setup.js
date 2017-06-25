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
    this.active = false;
    this.manager = manager;
}

Hint.prototype.setActive = function(on) {
    if (this.active == on) { return; }
    let bg;
    if (on) {
        bg = this.manager.options.background_active;
    } else {
        bg = this.manager.options.background;
    }
    this.active = on;
    this.obj.style.background = bg;
}

Hint.prototype.remove = function() {
    this.obj.style.background = this.objBackground;
    this.hint.parentNode.removeChild(this.hint);
}

function HintManager() {
    this.hints = [];
    this.options = {
        hint_background: "red",
        hint_color: "white",
        background: "yellow",
        background_active: "#88FF00"
    };
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
        hint.setActive(this.hints.length == 1);
        fragment.appendChild(hint.hint);
    }
    document.documentElement.appendChild(fragment);
}

HintManager.prototype.clearBrowserObjects = function() {
    for (let hint of this.hints) {
        hint.remove();
    }
    this.hints = [];
}

var hints = new HintManager();
