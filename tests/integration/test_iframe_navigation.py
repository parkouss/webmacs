import pytest


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

    end_waiter = session.waiter()

    def do_check():
        session.check_javascript(
            "%s === window.frames[0].document.activeElement"
            % INPUT0_IFRAME, True)
        session.keyclicks("youhou")

        session.check_javascript("%s.value" % INPUT0_IFRAME, "youhou")
        end_waiter.set()

    def prompt_follow(prompt, _):
        wait_hint.wait()
        if hint_method == "filter":
            session.wkeyclicks("C-n")
            # wait until the background color is green, the above keypress has
            # been taken in account.
            session.check_nav_highlighted(INPUT0_IFRAME)

            with session.wait_signal(prompt.closed):
                session.wkeyclicks("Enter")
        else:
            with session.wait_signal(prompt.closed):
                session.keyclick("d")

        session.call_next(do_check)

    session.set_prompt_exec(prompt_follow)
    wait_hint = session.wait_hints_ready()
    session.wkeyclicks("f")
    end_waiter.wait()
