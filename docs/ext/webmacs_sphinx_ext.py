from sphinx.util.compat import Directive
from docutils.statemachine import ViewList
from docutils import nodes

from webmacs import COMMANDS
from webmacs.commands import InteractiveCommand
from webmacs.commands.webjump import WEBJUMPS
from webmacs.application import _app_requires
from webmacs.variables import VARIABLES


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


def setup(app):
    app.add_directive("webmacs-commands", WebmacsCommands)
    app.add_directive("webmacs-webjumps", WebmacsWebjumps)
    app.add_directive("webmacs-variables", WebmacsVariables)
