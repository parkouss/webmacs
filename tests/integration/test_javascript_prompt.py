import pytest


def check_js_result(res):
    def check(session):
        session.check_javascript("getContent();", res)
    return check


def check_minibuffer(res):
    def check(session):
        assert session.wait_until(
            lambda: session.minibuffer.label.text() == res
        )
    return check


@pytest.mark.parametrize("selection,input,check", [
    # first variable is what is typed in follow command,
    # to select the right button to click.
    ("pro", "y", check_js_result("true")),
    ("pro", "n", check_js_result("false")),
    ("aler", None, check_minibuffer("[js-alert] hello there")),
])
def test_confirm(session, selection, input, check):
    """
    test javascript confirm.
    """
    session.load_page("javascript_prompt")
    end_waiter = session.waiter()

    def prompt_follow(prompt, _):
        session.keyclicks(selection)
        session.set_prompt_exec(confirm)
        with session.wait_signal(prompt.closed):
            session.wkeyclicks("Enter")
        if not input:
            session.call_next(do_check)

    def confirm(prompt , _1):
        with session.wait_signal(prompt.closed):
            session.keyclicks(input)

        session.call_next(do_check)

    def do_check():
        check(session)
        end_waiter.set()

    session.set_prompt_exec(prompt_follow)
    session.wkeyclicks("f")
    end_waiter.wait()
