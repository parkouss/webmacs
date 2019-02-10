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
import stat


def get_runtime_dir():
    # Return whether a path matches the requirements set by
    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    def test_valid(path):
        try:
            stats = os.stat(path)
            perms = stat.S_IMODE(stats.st_mode)

            return (os.path.isdir(path) and
                    stats.st_uid == os.getuid() and
                    perms & stat.S_IRWXU == 448 and
                    perms & (stat.S_IRWXG | stat.S_IRWXO) == 0)

        except FileNotFoundError:
            return False

    custom = os.getenv("XDG_RUNTIME_DIR")
    if custom and test_valid(custom):
        return custom
    elif custom:
        print("Warning: '{}' does not match the requirements for a valid "
              "XDG_RUNTIME_DIR. Falling back to a default directory.\n"
              "Please see the spec at https://specifications.freedesktop."
              "org/basedir-spec/basedir-spec-latest.html for more information."
              .format(custom,))

    defaults = [
        "/run/user/{}".format(os.getuid()),
        "/var/run/user/{}".format(os.getuid())
    ]

    try:
        return next(filter(test_valid, defaults))
    except StopIteration:
        # /tmp does not really match the requirements, but it's better
        # than nothing. We'll just make sure permissions are set
        # properly on /tmp/.webmacs.
        os.makedirs("/tmp/.webmacs")
        os.chmod("/tmp/.webmacs", stat.S_IRWXU)
        return "/tmp/.webmacs"


XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME",
                           os.path.expanduser("~/.cache"))
XDG_CONFIG_HOME = os.getenv("XDG_CONFIG_HOME",
                            os.path.expanduser("~/.config"))
XDG_DATA_HOME = os.getenv("XDG_DATA_HOME",
                          os.path.expanduser("~/.local/share"))
XDG_RUNTIME_DIR = get_runtime_dir()
