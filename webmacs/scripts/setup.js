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
