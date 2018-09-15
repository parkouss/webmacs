from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from docutils import nodes

from webmacs import COMMANDS
from webmacs.commands import InteractiveCommand
from webmacs.commands.webjump import WEBJUMPS
from webmacs.application import _app_requires
from webmacs.variables import VARIABLES
from webmacs.mode import MODES
from webmacs.keymaps import KEYMAPS


# to include all commands, etc.
_app_requires()


def as_rest_table(data):
    numcolumns = len(data[0])
    colsizes = [max(len(r[i]) for r in data) for i in range(numcolumns)]
    formatter = ' '.join('{:<%d}' % c for c in colsizes)
    rowsformatted = [formatter.format(*row) for row in data]
    header = formatter.format(*['=' * c for c in colsizes])

    yield header
    yield rowsformatted[0]
    yield header
    for row in rowsformatted[1:]:
        yield row
    yield header


class SimpleAutoDirective(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        self._result = ViewList()

        self._run()

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self._result, 0, node)
        return node.children


class WebmacsCommands(SimpleAutoDirective):
    def _run(self):
        result = self._result

        def get_doc(cmd):
            if isinstance(cmd, InteractiveCommand):
                cmd = cmd.binding
            return cmd.__doc__ or "No description"

        table = [("Command", "description")]
        for name in sorted(COMMANDS):
            table.append((name, get_doc(COMMANDS[name])))

        for line in as_rest_table(table):
            result.append(line, "")


class WebmacsWebjumps(SimpleAutoDirective):
    def _run(self):
        result = self._result

        table = [("Name", "url", "description")]
        for name in sorted(WEBJUMPS):
            webjump = WEBJUMPS[name]
            table.append((name, webjump.url, webjump.doc))

        for line in as_rest_table(table):
            result.append(line, "")


class WebmacsVariables(SimpleAutoDirective):
    def _run(self):
        result = self._result

        table = [("Name", "description", "default")]
        for name in sorted(VARIABLES):
            variable = VARIABLES[name]
            table.append((name, variable.doc, repr(variable.value)))

        for line in as_rest_table(table):
            result.append(line, "")


class WebmacsModes(SimpleAutoDirective):
    def _run(self):
        result = self._result

        table = [("Name", "Description")]
        for name in sorted(MODES):
            mode = MODES[name]
            table.append((name, mode.description))

        for line in as_rest_table(table):
            result.append(line, "")


class WebmacsKeymaps(SimpleAutoDirective):
    option_spec = {
        "only": lambda a: (a or "").replace(" ", "").split(",")
    }

    def _run(self):
        result = self._result
        keys = self.options.get("only") or sorted(KEYMAPS)

        table = [("Name", "Description")]
        for name in keys:
            km = KEYMAPS[name]
            table.append((name, km.doc or ""))

        for line in as_rest_table(table):
            result.append(line, "")


def webmacs_role(data):
    """
    Create a simple role function handler that check for the text to be in the
    given data, and just create a strong node for the it.
    """
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        # inliner.document.settings.env to access the env
        if text not in data:
            inliner.reporter.error("No such %s: %s" % (name, text))
        node = nodes.strong(text=text)
        return [node], []
    return role


def setup(app):
    app.add_directive("webmacs-commands", WebmacsCommands)
    app.add_directive("webmacs-webjumps", WebmacsWebjumps)
    app.add_directive("webmacs-variables", WebmacsVariables)
    app.add_directive("webmacs-modes", WebmacsModes)
    app.add_directive("webmacs-keymaps", WebmacsKeymaps)

    # use them to ensure doc is not outdated, making references to things that
    # do not exists.
    app.add_role("cmd", webmacs_role(COMMANDS))
    app.add_role("var", webmacs_role(VARIABLES))
    app.add_role("keymap", webmacs_role(KEYMAPS))
