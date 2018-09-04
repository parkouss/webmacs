import pytest
from webmacs.version import qt_version

pytestmark = pytest.mark.skipif(
    qt_version < (5, 10),
    reason="Qt version >= 5.10 required for iframes"
)


INPUT0 = "document.getElementById('input0')"
INPUT0_IFRAME = "window.frames[0].document.getElementById('input0')"


def test_iframe_navigation(session):
    """
    Webcontent-edit keymaps are used even in sub frames.
    """
    session.load_page("iframe_follow", wait_iframes=True)

    session.wkeyclicks("Tab")
    session.check_javascript("%s === document.activeElement" % INPUT0, True)

    # type some text in INPUT0 and move word backward

    session.keyclicks("hello world")
    session.check_javascript("%s.value" % INPUT0, "hello world")
    session.check_javascript("%s.selectionEnd" % INPUT0, 11)
    session.wkeyclicks("M-b")
    session.check_javascript("%s.selectionEnd" % INPUT0, 6)

    session.wkeyclicks("Tab")
    session.check_javascript("%s === window.frames[0].document.activeElement"
                             % INPUT0_IFRAME, True)

    # type some text in INPUT0  inside the iframe and move word backward
    session.keyclicks("hello world2")
    session.check_javascript("%s.value" % INPUT0_IFRAME, "hello world2")
    session.check_javascript("%s.selectionEnd" % INPUT0_IFRAME, 12)
    session.wkeyclicks("M-b")
    session.check_javascript("%s.selectionEnd" % INPUT0_IFRAME, 6)


@pytest.mark.parametrize("hint_method", ["filter", "alphabet"])
def test_iframe_follow(session, pytestconfig, hint_method, variables):
    """
    It is possible to hint things inside sub frames.
    """
    variables.set("hint-method", hint_method)
    session.load_page("iframe_follow", wait_iframes=True)

    with session.wait_hints_ready():
        session.keyclick("f")

    if hint_method == "filter":
        session.wkeyclicks("C-n")
        # wait until the background color is green, the above keypress has been
        # taken in account.
        session.check_nav_highlighted(INPUT0_IFRAME)
        session.wkeyclicks("Enter")
    else:
        session.keyclick("d")

    session.check_javascript("%s === window.frames[0].document.activeElement"
                             % INPUT0_IFRAME, True)
    session.keyclicks("youhou")

    session.check_javascript("%s.value" % INPUT0_IFRAME, "youhou")
