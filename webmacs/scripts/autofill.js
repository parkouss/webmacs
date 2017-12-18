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

var allowedInputTypeForName = ['text', 'email', 'tel'];

(function() {
    function findUsername(inputs) {
        var usernameNames = ['user', 'name', 'login'];
        for (var i = 0; i < usernameNames.length; ++i) {
            for (var j = 0; j < inputs.length; ++j)
                if (inputs[j].type == 'text' && inputs[j].value.length && inputs[j].name.indexOf(usernameNames[i]) != -1)
                    return inputs[j].value;
        }
        for (let inputType of allowedInputTypeForName) {
            for (var i = 0; i < inputs.length; ++i)
                if (inputs[i].type == inputType && inputs[i].value.length)
                    return inputs[i].value;
        }
        return '';
    }

    function registerForm(form) {
        form.addEventListener('submit', function() {
            var form = this;
            var data = '';
            var password = '';
            var inputs = form.getElementsByTagName('input');
            for (var i = 0; i < inputs.length; ++i) {
                var input = inputs[i];
                var type = input.type.toLowerCase();
                if (type != 'password' && !allowedInputTypeForName.includes(type))
                    continue;
                if (!password && type == 'password')
                    password = input.value;
                data += encodeURIComponent(input.name);
                data += '=';
                data += encodeURIComponent(input.value);
                data += '&';
            }
            if (!password)
                return;
            data = data.substring(0, data.length - 1);
            var url = window.location.href;
            var username = findUsername(inputs);
            __webmacsHandler__.autoFillFormSubmitted(url, username, password, data);
        }, true);
    }

    if (!document.documentElement) return;

    for (var i = 0; i < document.forms.length; ++i)
        registerForm(document.forms[i]);

    var observer = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; ++i)
            for (var j = 0; j < mutations[i].addedNodes.length; ++j)
                if (mutations[i].addedNodes[j].tagName == 'FORM')
                    registerForm(mutations[i].addedNodes[j]);
    });
    observer.observe(document.documentElement, { childList: true, subtree: true
                                               });

})();

function complete_form_data(d) {
    var data = d.split('&');
    var inputs = document.getElementsByTagName('input');

    for (var i = 0; i < data.length; ++i) {
        var pair = data[i].split('=');
        if (pair.length != 2)
            continue;
        var key = decodeURIComponent(pair[0]);
        var val = decodeURIComponent(pair[1]);
        for (var j = 0; j < inputs.length; ++j) {
            var input = inputs[j];
            var type = input.type.toLowerCase();
            if (type != 'password' && !allowedInputTypeForName.includes(type))
                continue;
            if (input.name == key)
                input.value = val;
        }
    }

}
