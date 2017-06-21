from collections import namedtuple

from PyQt5.QtCore import QUrl

from .minibuffer import Prompt, PromptTableModel
from .commands import define_command
from .webbuffer import current_buffer

WebJump = namedtuple("WebJump", ("url", "doc", "allow_args"))
WEBJUMPS = {}


def define_webjump(name, url, doc=""):
    allow_args = "%s" in url
    WEBJUMPS[name] = WebJump(url, doc, allow_args)


class WebJumpPrompt(Prompt):
    label = "url/webjump:"
    complete_options = {
        "autocomplete": True,
    }

    def completer_model(self):
        data = []
        for name, w in WEBJUMPS.items():
            if w.allow_args:
                name = name + " "
            data.append((name, w.doc))
        return PromptTableModel(data)


@define_command("go-to", prompt=WebJumpPrompt)
def go_to(value):
    args = value.split(" ", 1)
    command = args[0]
    try:
        webjump = WEBJUMPS[command]
    except KeyError:
        return

    if webjump.allow_args:
        args = args[1] if len(args) > 1 else ""
        url = webjump.url % str(QUrl.toPercentEncoding(args), "utf-8")
    else:
        url = webjump.url

    current_buffer().load(url)
