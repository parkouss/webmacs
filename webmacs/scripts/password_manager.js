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

var password_manager = {};

password_manager.create_fake_event = function(typeArg) {
    if (['keydown', 'keyup', 'keypress'].includes(typeArg)) {
        return new KeyboardEvent(typeArg, {
            'key': ' ',
            'code': ' ',
            'charCode': ' '.charCodeAt(0),
            'keyCode': ' '.charCodeAt(0),
            'which': ' '.charCodeAt(0),
            'bubbles': true,
            'composed': true,
            'cancelable': true
        });
    } else if (['input', 'change'].includes(typeArg)) {
        return new InputEvent(typeArg, {
            'bubbles': true,
            'composed': true,
            'cancelable': true
        });
    } else if (['focus', 'blur'].includes(typeArg)) {
        return new FocusEvent(typeArg, {
            'bubbles': true,
            'composed': true,
            'cancelable': true
        });
    } else {
        console.log.error("password_manager.create_fake_event: Unknown event type: " + typeArg);
        return null;
    }
}


password_manager.set_input_value = function(input, value) {
    input.value = value;
    for (let action of ['focus', 'keydown', 'keyup', 'keypress',
                        'input', 'change', 'blur']) {
        input.dispatchEvent(password_manager.create_fake_event(action));
        input.value = value;
    }
}

password_manager.complete_form_data = function(data) {
    var allowedUserAttrib = ["name", "id", "autocomplete", "placeholder"];
    var allowedInputTypeForName = ['text', 'email', 'tel'];

    var inputs = document.getElementsByTagName('input');
    var focusedElem = document.activeElement;

    for (var i=0; i < inputs.length; ++i) {
        var input = inputs[i];
        // don't fill if element is invisible
        if (input.offsetHeight === 0 || input.offsetParent === null) {
            continue;
        }
        var type = input.type.toLowerCase();

        if (data.password !== null && type === 'password') {
            password_manager.set_input_value(input, data.password);
        } else if (data.username !== null && allowedInputTypeForName.includes(type)) {
            password_manager.set_input_value(input, data.username);
        }
        for (const j in allowedUserAttrib) {
            var attribName = allowedUserAttrib[j];
            var attrib = input.getAttribute(attribName);
            for (const field in data.fields) {
                if (attrib == field) {
                    password_manager.set_input_value(input, data.fields[field]);
                    break;
                }
            }
        }
    }

    if (focusedElem) {
        focusedElem.focus();    // get back the focus
    }
}
