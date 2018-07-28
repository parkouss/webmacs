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
    "{loading}{mode}: {local_keymap} [{buffer_count}]",
    conditions=(
        variables.condition(lambda v: isinstance(v, str),
                            "Must be an instance of string"),
    ),
)


def update_minibuffer_right_label(window):
    buff = window.current_webview().buffer()

    try:
        loading_p = BUFF_PROGRESS[buff]
    except KeyError:
        loading = ""
    else:
        loading = " loading: %d%% " % loading_p

    window.minibuffer().rlabel.setText(
        MINIBUFFER_RIGHTLABEL.value.format(
            buffer_count=len(BUFFERS),
            local_keymap=keyboardhandler.local_keymap(),
            mode=getattr(buff, "mode", "unknown"),
            loading=loading,
        )
    )


def update_minibuffer_right_labels():
    for window in windows():
        update_minibuffer_right_label(window)


BUFF_PROGRESS = {}


def update_label_for_buffer(buff):
    update_minibuffer_right_label(buff.view().main_window)


def init_minibuffer_right_labels():

    def register_buffer_load_progress(buff):
        # first update all labels because the buffer count changed
        update_minibuffer_right_labels()

        def load_changed(p):
            if p is None:
                del BUFF_PROGRESS[buff]
            else:
                BUFF_PROGRESS[buff] = p

            view = buff.view()
            if view and view.main_window.current_webview() == view:
                update_minibuffer_right_label(view.main_window)

        # then connect this buffer to keep track of its load percent
        buff.loadStarted.connect(lambda: load_changed(0))
        buff.loadProgress.connect(load_changed)
        buff.loadFinished.connect(lambda: load_changed(None))

    for buff in BUFFERS:
        register_buffer_load_progress(buff)

    hooks.webbuffer_created.add(register_buffer_load_progress)
    hooks.webbuffer_current_changed.add(update_label_for_buffer)

    def on_buffer_closed(buff):
        # first update all labels because the buffer count changed
        update_minibuffer_right_labels()
        BUFF_PROGRESS.pop(buff, None)

    hooks.local_mode_changed.add(
        lambda a: update_minibuffer_right_labels()
    )

    update_minibuffer_right_labels()
