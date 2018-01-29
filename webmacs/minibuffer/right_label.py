# This file is part of webmacs.
#
# webmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# webmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webmacs.  If not, see <http://www.gnu.org/licenses/>.

from .. import hooks, variables, keyboardhandler
from .. import windows, BUFFERS


MINIBUFFER_RIGHTLABEL = variables.define_variable(
    "minibuffer-right-label",
    "Format for displaying some information in right label of minibuffer.",
    "{local_keymap} [{buffer_count}]",
    conditions=(
        variables.condition(lambda v: isinstance(v, str),
                            "Must be an instance of string"),
    ),
)


def update_minibuffer_right_labels():
    for window in windows():
        window.minibuffer().rlabel.setText(
            MINIBUFFER_RIGHTLABEL.value.format(
                buffer_count=len(BUFFERS),
                local_keymap=keyboardhandler.local_keymap(),
            )
        )


def init_minibuffer_right_labels():
    hooks.webbuffer_created.add(
        lambda a: update_minibuffer_right_labels()
    )

    hooks.webbuffer_closed.add(
        lambda a: update_minibuffer_right_labels()
    )

    hooks.local_mode_changed.add(
        lambda a: update_minibuffer_right_labels()
    )

    update_minibuffer_right_labels()
