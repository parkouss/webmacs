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

// per frame handlers for the message sent with window.postMessage.
MESSAGE_HANDLERS = {};


/*
  Use window.postMessage to send a cross-origin message.

  This allow to bypass the same origin policy in frames. An id is injected
  in the message sent, to be more secure.

  w: the window to send to.
  name: the message name.
  args: the message parameters.
*/
function post_message(w, name, args) {
    w.postMessage({
        webmacsid: WEBMACS_SECURE_ID,
        name: name,
        args: args
    }, "*");
}

// register sent messages on each frame.
window.addEventListener("message", function(e) {
    let data = e.data;
    if (typeof(data) == "object"
        && data.webmacsid === WEBMACS_SECURE_ID) {
        let handler = MESSAGE_HANDLERS[data.name];
        if (handler !== undefined) {
            handler(data.args);
        }
    }
})

/*
  register a message handler in the current frame.
*/
function register_message_handler(name, func) {
    MESSAGE_HANDLERS[name] = func;
}

/*
  Post a message on the webmacs python side, using the qtwebchannel.

  This use post_message if we are not on the main_frame, as only the main frame
  posses the __webmacsHandler__ web channel object.
*/
function post_webmacs_message(name, args) {
    if (self === top) {
        __webmacsHandler__[name].apply(__webmacsHandler__, args);
    } else {
        post_message(top, name, args);
    }
}

function isTextInput(node) {
    return node.isContentEditable
        || node.nodeName == "INPUT" || node.nodeName == "TEXTAREA";
}

// register focus in and out event on each frame.
document.addEventListener("focusin", function(e) {
    if (isTextInput(e.target)) {
        post_webmacs_message("onTextFocus", [true]);
    }
}, true);

document.addEventListener("focusout", function(e) {
    if (isTextInput(e.target)) {
        post_webmacs_message("onTextFocus", [false]);
    }
}, true);


if (self === top) {
    // for post_webmacs_message to works when called from iframes.
    register_message_handler("onTextFocus",
                             args => post_webmacs_message("onTextFocus", args))
    register_message_handler("copyToClipboard",
                             args => post_webmacs_message("copyToClipboard",
                                                          args))
    register_message_handler("openExternalEditor",
                             args => post_webmacs_message("openExternalEditor", args))

    // and now, register the web channel on the top frame.
    function registerWebmacs(w) {
        // only called in main frame
        console.log("registering...");
        window.__webmacsHandler__ = w;

        // force the focus on the current web content
        post_webmacs_message(
            "onTextFocus",
            [!!(document.activeElement && isTextInput(document.activeElement))]
        );

        var event = document.createEvent('Event');
        event.initEvent('_webmacs_external_created', true, true);
        document.dispatchEvent(event);
    }

    function registerWebChannel() {
        try {
            new QWebChannel(
                qt.webChannelTransport,
                channel => registerWebmacs(channel.objects.contentHandler)
            );
        } catch (e) {
            setTimeout(registerWebChannel, 50);
        }
    }

    registerWebChannel();
}
