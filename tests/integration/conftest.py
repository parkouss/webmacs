import pytest
import os
import time
import subprocess

from PyQt5.QtTest import QTest
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QEvent, QTimer

from webmacs.application import Application, _app_requires
from webmacs import (windows, buffers, WINDOWS_HANDLER, current_buffer,
                     current_window, current_minibuffer)
from webmacs.webbuffer import create_buffer
from webmacs.window import Window
from webmacs.webbuffer import close_buffer
from webmacs.keymaps import KeyPress


THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_app = None


def get_test_page(name):
    if name.endswith(".html"):
        return os.path.join(THIS_DIR, name)
    return os.path.join(THIS_DIR, name, "index.html")


def iter_widgets_for_events(w):
    # web engine views hide the widget that receive events.
    # this function tries to workaround that.
    if isinstance(w, QWebEngineView):
        for c in w.children():
            if isinstance(c, QWidget):
                yield c
    else:
        yield w


@pytest.fixture(scope="session")
def wm(xvfb):
    if xvfb is None:
        yield None
    else:
        if not any(
                os.access(os.path.join(path, 'herbstluftwm'), os.X_OK)
                for path in os.environ["PATH"].split(os.pathsep)
        ):
            raise RuntimeError("herbstluftwm is not installed, can not run"
                               " graphical tests.")
        env = dict(os.environ)
        env["DISPLAY"] = str(":%s" % xvfb.display)
        proc = subprocess.Popen(
            ["herbstluftwm"], env=env
        )
        time.sleep(2)  # wait for the wm to be active
        yield proc
        proc.kill()
        proc.wait()


@pytest.fixture(scope='session')
def qapp(wm, qapp_args):
    _app_requires()
    global _app
    # TODO FIXME use another path for tests
    conf_path = os.path.join(os.path.expanduser("~"), ".webmacs")
    _app = Application(conf_path, ["webmacs"])
    return _app


class TestSession(object):
    NAV_HIGHLIGHT_COLOR = 'rgb(136, 255, 0)'

    def __init__(self, qtbot, qapp, prompt_exec):
        self.qtbot = qtbot
        self.qapp = qapp
        self.prompt_exec = prompt_exec

    def set_prompt_exec(self, fn):
        self.prompt_exec.side_effect = fn

    def waiter(self):
        return Waiter(self)

    def call_next(self, fn):
        QTimer.singleShot(0, fn)

    @property
    def buffer(self):
        return current_buffer()

    @property
    def window(self):
        return current_window()

    @property
    def minibuffer(self):
        return current_minibuffer()

    @property
    def minibuffer_input(self):
        return self.minibuffer.input()

    def wait_signal(self, *args, **kwargs):
        return self.qtbot.wait_signal(*args, **kwargs)

    def wait_until(self, func, wait=2.0, delay=0.01):
        delay = int(delay * 1000)
        end = time.time() + wait
        while not func():
            QTest.qWait(delay)
            if time.time() > end:
                return False
        return True

    def test_page_url(self, name):
        return "file://" + get_test_page(name)

    def load_page(self, name, buffer=None, wait_iframes=False):
        buffer = buffer or self.buffer
        with self.wait_signal(buffer.loadFinished):
            buffer.load(self.test_page_url(name))

        script = (
            "__webmacs_loaded = window.__webmacsHandler__ !== null;"
            "if (! __webmacs_loaded) {"
            "  document.addEventListener('_webmacs_external_created',"
            "                             function() {"
            "    __webmacs_loaded = true;"
            "  });"
            " }"
        )
        buffer.runJavaScript(script)
        self.check_javascript("__webmacs_loaded", True)

        if wait_iframes:
            self.wait_iframes(buffer=buffer)

    def check_javascript(self, script, return_value, buffer=None):
        buffer = buffer or self.buffer
        result = [None]

        if return_value is None:
            raise ValueError("return value can't be None")

        def ready():
            if result[0] == return_value:
                return True
            buffer.runJavaScript(script, lambda r: result.__setitem__(0, r))

        assert self.wait_until(ready), "javascript result was %r" % result[0]
        return True

    def check_nav_highlighted(self, js_elem):
        self.check_javascript("%s.style.backgroundColor" % js_elem,
                              self.NAV_HIGHLIGHT_COLOR)

    def wait_iframes(self, buffer=None):
        buffer = buffer or self.buffer
        script = (
            "var result = true;"
            "for (var i = 0; i < window.frames.length; i++) { "
            "  if (window.frames[i].document.readyState != 'complete') {"
            "    result = false;"
            "  }"
            "}"
            "result;"
        )
        self.check_javascript(script, True, buffer=buffer)

    def keyclick(self, key, widget=None, **kwargs):
        widget = widget or self.qapp.focusWidget()
        for w in iter_widgets_for_events(widget):
            QTest.keyClick(w, key, **kwargs)

    def keyclicks(self, keys, widget=None, **kwargs):
        widget = widget or self.qapp.focusWidget()
        for w in iter_widgets_for_events(widget):
            QTest.keyClicks(w, keys, **kwargs)

    def wkeyclicks(self, shortcut, widget=None):
        widget = widget or self.qapp.focusWidget()
        keys = [KeyPress.from_str(k) for k in shortcut.split()]
        for w in iter_widgets_for_events(widget):
            for key in keys:
                self.qapp.postEvent(w, key.to_qevent(QEvent.KeyPress))
                self.qapp.postEvent(w, key.to_qevent(QEvent.KeyRelease))
        self.qapp.processEvents()


class Waiter(object):
    def __init__(self, session):
        self.session = session
        self.end = False

    def set(self):
        self.end = True

    def wait(self, wait=5, **kwargs):
        kwargs["wait"] = wait
        return self.session.wait_until(lambda: self.end, **kwargs)


@pytest.yield_fixture()
def session(qtbot, qapp, mocker):
    # do not close the application on last window closed
    mocker.patch("webmacs.WindowsHandler._on_last_window_closing") \
        .return_value = False

    prompt_exec = mocker.patch("webmacs.minibuffer.prompt._prompt_exec")
    sess = TestSession(qtbot, qapp, prompt_exec)

    window = Window()
    WINDOWS_HANDLER.current_window = window
    window.current_webview().setBuffer(create_buffer())

    window.show()
    qtbot.waitForWindowShown(window)

    yield sess

    for w in windows():
        w.current_webview().setBuffer(None)
        w.close()
        w.deleteLater()

    for buffer in buffers():
        close_buffer(buffer)

    qapp.processEvents()
