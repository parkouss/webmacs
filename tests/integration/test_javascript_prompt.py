import pytest
from PyQt5.QtCore import QTimer


@pytest.mark.parametrize("selection,input,result", [
    # first variable is what is typed in follow command,
    # to select the right button to click.
    ("pro", "y", "true"),
    ("pro", "n", "false"),
])
def test_prompt(session, selection, input, result):
    """
    test javascript prompts.
    """
    session.load_page("javascript_prompt")
    end = []

    def prompt_follow(prompt, _):
        session.keyclicks(selection)
        session.set_prompt_exec(confirm)
        with session.wait_signal(prompt.closed):
            session.wkeyclicks("Enter")

    def confirm(prompt , _1):
        with session.wait_signal(prompt.closed):
            session.keyclicks(input)

        QTimer.singleShot(0, check)

    def check():
        session.check_javascript("getContent();", result)
        end.append(True)

    session.set_prompt_exec(prompt_follow)
    session.wkeyclicks("f")
    session.wait_until(lambda: end, wait=5)
