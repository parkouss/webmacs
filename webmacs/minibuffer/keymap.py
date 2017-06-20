import re

from ..keymap import Keymap

KEYMAP = Keymap("minibuffer")


def current_minibuffer():
    from ..window import current_window
    return current_window().minibuffer()


@KEYMAP.define_key("Tab")
def complete():
    input = current_minibuffer().input()

    if not input.popup().isVisible():
        input.show_completions()
    else:
        input.select_next_completion()


@KEYMAP.define_key("C-n")
@KEYMAP.define_key("Down")
def next_completion():
    current_minibuffer().input().select_next_completion()


@KEYMAP.define_key("C-p")
@KEYMAP.define_key("Top")
def previous_completion():
    current_minibuffer().input().select_next_completion(False)


@KEYMAP.define_key("Return")
def edition_finished():
    current_minibuffer().input().complete()
    current_minibuffer().input().popup().hide()
    current_minibuffer().input().returnPressed.emit()


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    minibuffer = current_minibuffer()
    input = minibuffer.input()
    if input.popup().isVisible():
        input.popup().hide()
    elif input.selectedText():
        input.deselect()
    else:
        minibuffer.close_prompt()


@KEYMAP.define_key("M-Backspace")
def clean_aindent_bsunindent():
    input = current_minibuffer().input()

    parts = re.split(r"([-_ ])", input.text())
    while parts:
        if parts[-1] in ("", "-", "_", " "):
            parts.pop()
        else:
            break
    input.setText("".join(parts[:-1]))


@KEYMAP.define_key("C-Space")
def set_mark():
    if not current_minibuffer().input().set_mark():
        current_minibuffer().input().deselect()


@KEYMAP.define_key("C-f")
@KEYMAP.define_key("Right")
def forward_char():
    edit = current_minibuffer().input()
    edit.cursorForward(edit.mark(), 1)


@KEYMAP.define_key("C-b")
@KEYMAP.define_key("Left")
def backward_char():
    edit = current_minibuffer().input()
    edit.cursorBackward(edit.mark(), 1)


@KEYMAP.define_key("M-f")
@KEYMAP.define_key("M-Right")
def forward_word():
    edit = current_minibuffer().input()
    edit.cursorWordForward(edit.mark())


@KEYMAP.define_key("M-b")
@KEYMAP.define_key("M-Left")
def backward_word():
    edit = current_minibuffer().input()
    edit.cursorWordBackward(edit.mark())


@KEYMAP.define_key("M-w")
def copy():
    current_minibuffer().input().copy()
    current_minibuffer().input().deselect()


@KEYMAP.define_key("C-w")
def cut():
    current_minibuffer().input().cut()


@KEYMAP.define_key("C-y")
def paste():
    current_minibuffer().input().paste()


@KEYMAP.define_key("C-d")
def delete_char():
    current_minibuffer().input().del_()


@KEYMAP.define_key("M-d")
def delete_word():
    edit = current_minibuffer().input()
    if edit.hasSelectedText():
        edit.del_()
    else:
        pos = edit.cursorPosition()
        text = edit.text()
        deleted_some = False
        for i in range(pos, len(text)):
            char = text[i]
            if char in ("-", "_", " "):
                if deleted_some:
                    break
                edit.del_()
            else:
                deleted_some = True
                edit.del_()


@KEYMAP.define_key("C-a")
def beginning_of_line():
    edit = current_minibuffer().input()
    edit.home(edit.mark())


@KEYMAP.define_key("C-e")
def end_of_line():
    edit = current_minibuffer().input()
    edit.end(edit.mark())
