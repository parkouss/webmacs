import os
import tempfile
import subprocess
from . import variables
import shlex


editor_cmd = variables.define_variable(
    "external-editor-command",
    "command to open an external editor. You must use the {file}"
    " placeholder in the command, as it will be used to open the"
    " temporary file.",
    "emacsclient -c -a '' {file}",
    conditions=(
        variables.condition(lambda v: isinstance(v, str),
                            "Must be an instance of string"),
    ),
)


def open_external_editor(content):
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(content)

    cmd = editor_cmd.value.format(file=shlex.quote(tf.name))

    if subprocess.call(cmd, shell=True) != 0:
        return

    with open(tf.name) as f:
        return f.read()

    os.unlink(tf.name)
