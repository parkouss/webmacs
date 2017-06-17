import socket
import json

from PyQt5.QtWebSockets import QWebSocketServer
from PyQt5.QtWebChannel import QWebChannelAbstractTransport, QWebChannel
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtCore import QObject, pyqtSlot


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
    @pyqtSlot(bool)
    def onTextFocus(self, enabled):
        print("text focus: %s" % enabled)


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
