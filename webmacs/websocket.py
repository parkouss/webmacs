import socket
import json

from PyQt5.QtWebSockets import QWebSocketServer
from PyQt5.QtWebChannel import QWebChannelAbstractTransport, QWebChannel
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal

from .window import current_window
from .keyboardhandler import LOCAL_KEYMAP_SETTER
from .webbuffer import buffer_for_id


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", 0))
        return s.getsockname()[1]
    finally:
        s.close()


class WebContentHandler(QObject):
    """
    Interface to communicate with the javascript side in the web pages.
    """
    browserObjectActivated = Signal(dict)

    @Slot(bool)
    def onTextFocus(self, enabled):
        win = current_window()
        LOCAL_KEYMAP_SETTER.web_content_edit_focus_changed(win, enabled)

    @Slot(str)
    def _browserObjectActivated(self, obj):
        # It is hard to pass dict objects from javascript, so a string is used
        # and decoded here.
        self.browserObjectActivated.emit(json.loads(obj))

    @Slot(str)
    def onBufferFocus(self, bid):
        # Qt do not send focus events for the QWebEngineView, so we have to
        # trick and use javascript to know which buffer (and its attached view)
        # gain the focus.
        buffer = buffer_for_id(bid)
        if buffer and buffer.view():
            buffer.view().set_current()

    @Slot(str)
    def copyToClipboard(self, text):
        from .application import Application

        Application.INSTANCE.clipboard().setText(text)


class WebSocketClientWrapper(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.port = get_free_port()
        self.content_handler = WebContentHandler()
        self.transports = {}
        self.server = QWebSocketServer("Example Server",
                                       QWebSocketServer.NonSecureMode)
        if not self.server.listen(QHostAddress.LocalHost, self.port):
            raise "Can't start the server"

        self.channel = QWebChannel()
        self.server.newConnection.connect(self.handleNewConnection)
        self.channel.registerObject("contentHandler", self.content_handler)

    def handleNewConnection(self):
        sock = self.server.nextPendingConnection()
        sock.disconnected.connect(self.socket_disconnected)
        transport = WebSocketTransport(sock)
        # keep a reference of the transport to stay connected
        self.transports[sock] = transport
        self.channel.connectTo(transport)

    def socket_disconnected(self):
        sock = self.sender()
        del self.transports[sock]


class WebSocketTransport(QWebChannelAbstractTransport):
    def __init__(self, socket):
        QWebChannelAbstractTransport.__init__(self, socket)
        self._socket = socket
        self._socket.textMessageReceived.connect(self.textMessageReceived)

    def sendMessage(self, message):
        for k in message.keys():
            message[k] = message[k].toVariant()
        self._socket.sendTextMessage(json.dumps(message))

    def textMessageReceived(self, message):
        message = json.loads(message)
        self.messageReceived.emit(message, self)
