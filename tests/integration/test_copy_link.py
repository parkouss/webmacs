from webmacs.keyboardhandler import CommandContext
from webmacs.application import app
from webmacs.commands import COMMANDS


def clipboard_contains(text):
    return app().clipboard().text() == text


def test_copy_current_link(session):
    session.load_page("iframe_follow", wait_iframes=True)

    link = "document.getElementById('a_top')"

    session.buffer.runJavaScript("%s.focus()" % link)
    session.check_javascript("document.activeElement == %s" % link, True)

    COMMANDS["copy-current-link"](CommandContext())

    assert session.wait_until(
        lambda: clipboard_contains("https://foo/top.html")
    )


def test_copy_current_link_in_subframe(session):
    session.load_page("iframe_follow", wait_iframes=True)

    link = "window.frames[0].document.getElementById('a_inside')"

    session.buffer.runJavaScript("%s.focus()" % link)

    session.check_javascript(
        "document.activeElement.tagName",
        'IFRAME'
    )
    session.check_javascript(
        "window.frames[0].document.activeElement == %s" % link,
        True
    )

    COMMANDS["copy-current-link"](CommandContext())

    assert session.wait_until(
        lambda: clipboard_contains("https://foo/inside.html")
    )


def test_copy_current_url(session):
    session.load_page("iframe_follow")
    url = session.buffer.url().toString()

    COMMANDS["copy-current-buffer-url"](CommandContext())

    assert session.wait_until(
        lambda: clipboard_contains(url)
    )


def test_copy_current_title(session):
    session.load_page("iframe_follow")

    COMMANDS["copy-current-buffer-title"](CommandContext())

    assert session.wait_until(
        lambda: clipboard_contains("iframe testing")
    )
