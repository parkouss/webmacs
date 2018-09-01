# This file is part of webmacs.
#
# webmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# webmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webmacs.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re
import importlib
import inspect
from PyQt5.QtCore import QBuffer, QFile, QUrlQuery
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from jinja2 import Environment, PackageLoader
from ... import version, COMMANDS
from ...variables import VARIABLES
from ...keymaps import KEYMAPS


PAGES = []
_REQUESTS_HANDLER = []
THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def register_page(match_url=None, visible=True):
    def wrapper(meth):
        if visible:
            PAGES.append(meth.__name__)
        if match_url is None:
            match = re.compile(r"^(%s)$" % re.escape(meth.__name__))
        elif isinstance(match_url, str):
            match = re.compile(match_url)
        else:
            match = match_url

        _REQUESTS_HANDLER.append((match, meth))

        return meth
    return wrapper


class WebmacsSchemeHandler(QWebEngineUrlSchemeHandler):
    scheme = b"webmacs"

    def __init__(self, parent=None):
        QWebEngineUrlSchemeHandler.__init__(self, parent)
        self.env = Environment(
            autoescape=True,
            loader=PackageLoader(__name__),
        )

    def reply_template(self, job, tpl_name, data):
        template = self.env.get_template(tpl_name + ".html")
        buffer = QBuffer(self)
        buffer.setData(template.render(**data).encode("utf-8"))
        job.reply(b"text/html", buffer)

    def requestStarted(self, job):
        url = job.requestUrl()
        url_s = url.toString()[10:]  # strip webmacs://

        for re_match, meth in _REQUESTS_HANDLER:
            res = re_match.match(url_s)
            if res:
                meth(self, job, url, *res.groups())
                return

    @register_page(match_url=r"^/js/(.+\.js)$", visible=False)
    def to_js(self, job, _, path):
        js_path = os.path.join(THIS_DIR, "js", path)
        if os.path.isfile(js_path):
            f = QFile(js_path, self)
            job.reply(b"application/javascript", f)

    @register_page()
    def version(self, job, _, name):
        self.reply_template(job, name, {
            "versions": (
                ("Webmacs version", version.WEBMACS_VERSION_STR),
                ("Operating system", sys.platform),
                ("Python version", sys.version),
                ("Qt version", version.QT_VERSION_STR),
                ("Chromium version", version.chromium_version()),
                ("Opengl vendor", version.opengl_vendor()),
            )
        })

    @register_page()
    def downloads(self, job, _, name):
        self.reply_template(job, name, {})

    @register_page()
    def commands(self, job, _, name):
        self.reply_template(job, name, {"commands": COMMANDS})

    @register_page(match_url=r"^command/(\S+)$", visible=False)
    def command(self, job, _, command):
        used_in_keymaps = []

        for name, km in KEYMAPS.items():
            def add(prefix, cmd):
                if cmd == command:
                    used_in_keymaps.append((
                        " ".join(str(k) for k in prefix),
                        name,
                    ))

            km.traverse_commands(add)

        cmd = COMMANDS[command]

        src_url = get_src_url(cmd.binding)

        self.reply_template(job, "command", {
            "command_name": command,
            "command": cmd,
            "command_src_url": src_url,
            "used_in_keymaps": used_in_keymaps,
        })

    @register_page()
    def variables(self, job, _, name):
        self.reply_template(job, name, {"variables": VARIABLES})

    @register_page(match_url=r"^variable/(\S+)$", visible=False)
    def variable(self, job, _, name):
        self.reply_template(job, "variable", {"variable": VARIABLES[name]})

    @register_page(match_url=r"^keymap/(\S+)$", visible=False)
    def keymap(self, job, _, keymap):
        km = KEYMAPS[keymap]

        self.reply_template(job, "keymap", {
            "name": keymap,
            "keymap": km,
            "bindings": _get_keymap_bindings(km),
        })

    @register_page()
    def bindings(self, job, _, name):
        bindings = {}
        for kname, km in KEYMAPS.items():
            bindings[kname] = _get_keymap_bindings(km)

        self.reply_template(job, name, {"bindings": bindings,
                                        "keymaps": KEYMAPS})

    @register_page(match_url=r"^pydoc/.+$", visible=False)
    def pydoc(self, job, url):
        from pygments.formatters import HtmlFormatter
        from pygments.lexers.python import Python3Lexer
        from pygments import highlight

        modname = url.path().lstrip("/")
        query = QUrlQuery(url)
        extras = {}
        if query.hasQueryItem("hl_lines"):
            start, end = query.queryItemValue("hl_lines").split("-")
            extras["hl_lines"] = list(range(int(start), int(end) + 1))

        mod = importlib.import_module(modname)
        filepath = inspect.getsourcefile(mod)

        formatter = HtmlFormatter(
            title="Module %s" % modname,
            full=True,
            lineanchors="line",
            **extras
        )

        with open(filepath) as f:
            code = highlight(f.read(), Python3Lexer(), formatter)

        buffer = QBuffer(self)
        buffer.setData(code.encode("utf-8"))
        job.reply(b"text/html", buffer)

    @register_page(match_url=r"^key/.+$", visible=False)
    def key(self, job, url):
        key = url.path().lstrip("/")
        query = QUrlQuery(url)
        command = query.queryItemValue("command")
        keymap = query.queryItemValue("keymap")

        if ":" in command:
            modname, fname = command.split(":", 1)
            fn = getattr(importlib.import_module(modname), fname)
            command_name = fn.__name__
            named_command = False
        else:
            command_name = command
            cmd = COMMANDS[command]
            fn = cmd.binding
            named_command = True
            modname = fn.__module__
        command_doc = fn.__doc__
        src_url = get_src_url(fn)

        def _get_all_keys(km):
            acc = []

            cmd = command_name if named_command else fn

            def add(prefix, cmd_):
                if cmd == cmd_:
                    acc.append(" ".join(str(k) for k in prefix))
            km.traverse_commands(add)
            return acc

        try:
            all_keys = _get_all_keys(KEYMAPS[keymap])
        except KeyError:
            all_keys = (key,)

        self.reply_template(job, "key", {
            "command_name": command_name,
            "keymap": keymap,
            "key": key,
            "command_doc": command_doc,
            "named_command": named_command,
            "command_src_url": src_url,
            "modname": modname,
            "all_keys": all_keys,
        })


def _get_keymap_bindings(km):
    acc = []

    def add(prefix, cmd):
        if isinstance(cmd, str):
            acc.append((
                " ".join(str(k) for k in prefix),
                cmd
            ))
    km.traverse_commands(add)
    return acc


def get_src_url(obj):
    lines, loc = inspect.getsourcelines(obj)
    return "webmacs://pydoc/{}?hl_lines={}-{}#line-{}".format(
        obj.__module__,
        loc,
        loc + len(lines),
        loc
    )
