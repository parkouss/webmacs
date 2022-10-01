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
import re
import sys
import logging
import traceback

from PyQt6.QtNetwork import QLocalSocket

from . import version


class NoFilter(object):
    def __init__(self, *a, **kw):
        pass

    def enable(self):
        pass


class OutputFilter(object):
    """
    Filter what is send on stderr file descriptor, on unix systems only.
    """
    def __init__(self, regexes):
        # duplicate stderr on a new file descriptor that we assign to
        # sys.stderr (so from python there is no difference when writing to the
        # standard error) and redirect stderr to a pipe that we will read,
        # filter and log manually.
        sys.stderr.flush()
        r, w = os.pipe()

        newerr = os.dup(sys.stderr.fileno())
        os.dup2(w, sys.stderr.fileno())

        os.close(w)
        sys.stderr = os.fdopen(newerr, "w")

        def _excepthook(e, v, tb):
            # use our custom stderr
            traceback.print_exception(e, v, tb, None, sys.stderr)
            sys.exit(1)

        sys.excepthook = _excepthook

        self._notifier = QLocalSocket()
        self._fd = r
        self._regexes = regexes

    def enable(self):
        self._notifier.setSocketDescriptor(self._fd)
        self._notifier.readyRead.connect(self._redirect)

    def _redirect(self):
        while self._notifier.canReadLine():
            line = self._notifier.readLine().data().rstrip().decode("utf-8")
            logging.log(self._regexes.get_level_for_line(line), line)


class FilterRegexes(object):
    def __init__(self):
        self._data = []

    def get_level_for_line(self, line):
        for regex, level in self._data:
            if regex.match(line):
                return level
        return logging.CRITICAL

    def filter(self, regexstr, level=logging.DEBUG):
        self._data.append((re.compile(regexstr), level))


def make_filter():
    # when there is a qtwebengine crash, the OutputFilter will prevent the
    # stack trace from being printed. Need to find a way to have those stack
    # traces somewhere before filtering.
    return NoFilter()

    regexes = FilterRegexes()

    regexes.filter(r"^libpng warning: iCCP: known incorrect sRGB profile$")
    regexes.filter(r".*gles2_cmd_decoder_autogen.h.*")

    if version.qt_version >= (5, 12):
        regexes.filter(
            r"QNetworkReplyHttpImplPrivate::_q_startOperation was called more"
            r" than once.*"
        )
    else:
        # see https://bugreports.qt.io/browse/QTBUG-68547
        regexes.filter(r".*stack_trace_posix\.cc.* Failed to open file: .*")
        regexes.filter(r"^  Error: No such file or directory$")

        regexes.filter(r".*nss_ocsp.cc.*No URLRequestContext for NSS HTTP"
                       r" handler..*")

    cls = OutputFilter if version.is_posix else NoFilter
    return cls(regexes)
