from ..keyboardhandler import current_prefix_arg
from ..webbuffer import create_buffer
from .. import current_window, current_buffer


class PromptNewBuffer(object):
    """
    An object to automatically handle current prefix arg in a prompt
    to open in a new buffer.
    """
    def __init__(self, force_new_buffer=False):
        self.new_buffer = force_new_buffer or current_prefix_arg() == (4,)

    def __bool__(self):
        return self.new_buffer

    def enable(self, minibuffer):
        if self.new_buffer:
            minibuffer.label.setText(minibuffer.label.text() + " (new buffer)")

    def get_buffer(self):
        if self.new_buffer:
            buf = create_buffer()
            view = current_window().current_web_view()
            view.setBuffer(buf)
        else:
            buf = current_buffer()
        return buf
