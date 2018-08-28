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
import logging
import re

from PyQt5.QtGui import (QOpenGLContext, QOpenGLVersionProfile,
                         QOffscreenSurface)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QT_VERSION_STR, QT_VERSION  # noqa: F401
from . import __version__ as WEBMACS_VERSION_STR  # noqa: F401


is_mac = sys.platform.startswith('darwin')
is_linux = sys.platform.startswith('linux')
is_windows = sys.platform.startswith('win')
is_posix = os.name == 'posix'


def opengl_vendor():  # pragma: no cover
    """
    Get the OpenGL vendor used.

    This returns a string such as 'nouveau' or
    'Intel Open Source Technology Center'; or None if the vendor can't be
    determined.
    """
    # took from qutebrowser
    assert QApplication.instance()

    old_context = QOpenGLContext.currentContext()
    old_surface = None if old_context is None else old_context.surface()

    surface = QOffscreenSurface()
    surface.create()

    ctx = QOpenGLContext()
    if not ctx.create():
        logging.debug("opengl_vendor: Creating context failed!")
        return None

    if not ctx.makeCurrent(surface):
        logging.debug("opengl_vendor: Making context current failed!")
        return None

    try:
        if ctx.isOpenGLES():
            # Can't use versionFunctions there
            return None

        vp = QOpenGLVersionProfile()
        vp.setVersion(2, 0)

        vf = ctx.versionFunctions(vp)
        if vf is None:
            logging.debug("opengl_vendor: Getting version functions failed!")
            return None

        return vf.glGetString(vf.GL_VENDOR)
    finally:
        ctx.doneCurrent()
        if old_context and old_surface:
            old_context.makeCurrent(old_surface)


def QT_VERSION_CHECK(major, minor=0, patch=0):
    return (major << 16) | (minor << 8) | patch


class QtVersionChecker(object):
    def __init__(self):
        self.version = QT_VERSION

    def __eq__(self, other):
        return self.version == QT_VERSION_CHECK(*other)

    def __lt__(self, other):
        return self.version < QT_VERSION_CHECK(*other)

    def __gt__(self, other):
        return self.version > QT_VERSION_CHECK(*other)

    def __le__(self, other):
        return self.version <= QT_VERSION_CHECK(*other)

    def __ge__(self, other):
        return self.version >= QT_VERSION_CHECK(*other)


qt_version = QtVersionChecker()


def chromium_version():
    """
    Get the Chromium version for QtWebEngine.

    This can also be checked by looking at this file with the right Qt tag:
    https://github.com/qt/qtwebengine/blob/dev/tools/scripts/version_resolver.py#L41
    """
    if QWebEngineProfile is None:
        # This should never happen
        return 'unavailable'
    profile = QWebEngineProfile()
    ua = profile.httpUserAgent()
    match = re.search(r' Chrome/([^ ]*) ', ua)
    if not match:
        logging.error("Could not get Chromium version from: {}".format(ua))
        return 'unknown'
    return match.group(1)
