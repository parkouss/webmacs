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

import json

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal, \
    QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineScript

from .keyboardhandler import LOCAL_KEYMAP_SETTER
from .autofill import FormData
from .application import app
from .external_editor import open_external_editor


class WebContentHandler(QObject):
    """
    Interface to communicate with the javascript side in the web pages.
    """
    browserObjectActivated = Signal(dict)

    def __init__(self, buff):
        QObject.__init__(self)
        self.buffer = buff

    @Slot(bool)
    def onTextFocus(self, enabled):
        LOCAL_KEYMAP_SETTER.web_content_edit_focus_changed(self.buffer,
                                                           enabled)

    @Slot(bool)
    def onCaretBrowsing(self, enabled):
        LOCAL_KEYMAP_SETTER.caret_browsing_changed(self.buffer, enabled)

    @Slot(str)
    def _browserObjectActivated(self, obj):
        # It is hard to pass dict objects from javascript, so a string is used
        # and decoded here.
        self.browserObjectActivated.emit(json.loads(obj))

    @Slot(str)
    def copyToClipboard(self, text):
        app().clipboard().setText(text)

    @Slot(str, str, str, str)
    def autoFillFormSubmitted(self, url, username, password, data):
        formdata = FormData(url=QUrl(url), username=username,
                            password=password, data=data)
        app().autofill().maybe_save_form_password(self.buffer, formdata)

    @Slot(str, str)
    def openExternalEditor(self, request_id, content):
        new_content = open_external_editor(content.encode("utf-8"))
        if new_content is None:
            new_content = 'false'
        else:
            new_content = repr(new_content)
        self.buffer.runJavaScript(
            "textedit.external_editor_finish({}, {});".format(
                repr(request_id),
                new_content
            ),
            QWebEngineScript.ApplicationWorld
        )
