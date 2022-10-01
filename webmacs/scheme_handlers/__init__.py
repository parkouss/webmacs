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

from .webmacs import WebmacsSchemeHandler
from .. import version


def all_schemes():
    return (WebmacsSchemeHandler,)


def register_schemes():
    if version.pyqt_version < (5, 12):
        return

    from PyQt6.QtWebEngineCore import QWebEngineUrlScheme

    for scheme in all_schemes():
        qscheme = QWebEngineUrlScheme(scheme.scheme)
        QWebEngineUrlScheme.registerScheme(qscheme)
