import json

from .import BUFFERS
from .webbuffer import create_buffer, close_buffer
from .window import current_window, windows


class Session(object):
    def __init__(self, urls=None):
        if urls is None:
            urls = [b.url().toString() for b in BUFFERS]
        self.urls = urls

    @classmethod
    def load(cls, stream):
        data = json.load(stream)
        return cls(urls=data["urls"])

    def apply(self):
        cwin = current_window()

        # close any opened window other than the current one
        for win in windows():
            if win != cwin:
                win.close()

        # close any webview except the current one
        cwin.close_other_views()

        # and close all the buffers
        for buff in BUFFERS:
            close_buffer(buff, keep_one=False)

        # now, load urls in buffers
        for url in reversed(self.urls):
            create_buffer(url)

        # and open the first buffer in the view
        if BUFFERS:
            cwin.current_web_view().setBuffer(BUFFERS[0])

    def save(self, stream):
        json.dump({"urls": self.urls}, stream)
