from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest


def test_iframe_navigation(session):
    """
    Webcontent-edit keymaps are used even in sub frames.
    """
    session.load_page("iframe_follow", wait_iframes=True)

    session.wkeyclicks("Tab")
    session.wait_local_keymap("webcontent-edit")

    # type some text in input0 and move word backward
    input0 = "document.getElementById('input0')"

    session.keyclicks("hello world")
    session.check_javascript("%s.value" % input0, "hello world")
    session.check_javascript("%s.selectionEnd" % input0, 11)
    session.wkeyclicks("M-b")
    session.check_javascript("%s.selectionEnd" % input0, 6)

    session.wkeyclicks("Tab")
    session.wait_local_keymap("webcontent-edit")

    # type some text in input0  inside the iframe and move word backward
    input0_iframe = "window.frames[0].document.getElementById('input0')"
    session.keyclicks("hello world2")
    session.check_javascript("%s.value" % input0_iframe, "hello world2")
    session.check_javascript("%s.selectionEnd" % input0_iframe, 12)
    session.wkeyclicks("M-b")
    session.check_javascript("%s.selectionEnd" % input0_iframe, 6)


def test_iframe_follow(session, pytestconfig):
    """
    It is possible to hint things inside sub frames.
    """
    session.load_page("iframe_follow", wait_iframes=True)

    session.keyclick("f")

    session.wait_local_keymap("hint")
    # TODO FIXME can't use wkeyclicks("2"), why?
    QTest.qWait(200)
    session.keyclick(Qt.Key_2)
    session.wkeyclicks("Enter")
    session.wait_local_keymap("webcontent-edit")
    session.keyclicks("youhou")

    input0_iframe = "window.frames[0].document.getElementById('input0')"
    session.check_javascript("%s.value" % input0_iframe, "youhou")
