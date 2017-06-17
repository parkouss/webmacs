var socket = new WebSocket(webmacsBaseUrl);

socket.onclose = function() {
  console.error("web channel closed");
};
socket.onerror = function(error) {
  console.error("web channel error: " + error);
};
socket.onopen = function() {
  console.error("WebSocket connected, setting up QWebChannel.");
  new QWebChannel(socket, function(channel) {
    window.__webmacsHandler__ = channel.objects.contentHandler;

    function isTextInput(nodeName) {
      return nodeName == "INPUT";
    }

    document.addEventListener("focus", function(e) {
      if (isTextInput(e.target.nodeName)) {
        __webmacsHandler__.onTextFocus(true);
      }
    }, true);

    document.addEventListener("blur", function(e) {
      if (isTextInput(e.target.nodeName)) {
        __webmacsHandler__.onTextFocus(false);
      }
    }, true);
  });
};
