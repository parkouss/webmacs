import logging

from PyQt5.QtNetwork import QNetworkProxy, QNetworkProxyFactory
from PyQt5.QtCore import QUrl

from . import variables


def _update_custom_proxy(variable):
    logging.info("Setting up proxy from %s" % variable.value)
    try:
        if variable.value == 'system':
            ProxyFactory.CUSTOM_PROXY = None
        elif variable.value == "direct":
            ProxyFactory.CUSTOM_PROXY = proxy_from_url("direct://")
        else:
            ProxyFactory.CUSTOM_PROXY = proxy_from_url(variable.value)
    except Exception as exc:
        raise variables.VariableConditionError(str(exc)) from None


proxy = variables.define_variable(
    "proxy",
    "Defines a proxy for the application. Possible values: 'system', 'direct',"
    " or a proxy url like socks5://user:password@host:port. If 'system', it"
    " will use the proxy system, on linux defined by the environment variable"
    " http_proxy. 'direct' will not proxy anything.",
    'system',
    type=variables.String(),
    callbacks=(
        _update_custom_proxy,
    )
)


proxy_dns_requests = variables.define_variable(
    "proxy-dns-requests",
    "Boolean to redirect dns requests using the proxy.",
    False,
    conditions=(
        variables.condition(
            lambda v: isinstance(v, bool), "Must be a boolean"
        ),
    ),
    type=variables.Bool(),
)


def init():
    global PROXY_FACTORY  # keep a python reference around

    PROXY_FACTORY = ProxyFactory()
    ProxyFactory.setApplicationProxyFactory(PROXY_FACTORY)
    _update_custom_proxy(proxy)


def shutdown():
    global PROXY_FACTORY

    ProxyFactory.setApplicationProxyFactory(None)
    del PROXY_FACTORY


def proxy_from_url(url):
    """
    Create a QNetworkProxy from an url.
    """
    if not isinstance(url, QUrl):
        url = QUrl.fromUserInput(url)

    if not url.isValid():
        raise RuntimeError("Invalid url %s" % url.toString())

    scheme = url.scheme()

    types = {
        'http': QNetworkProxy.HttpProxy,
        'socks': QNetworkProxy.Socks5Proxy,
        'socks5': QNetworkProxy.Socks5Proxy,
        'direct': QNetworkProxy.NoProxy,
    }
    if scheme not in types:
        raise RuntimeError("scheme %s for url is invalid" % scheme)

    proxy = QNetworkProxy(types[scheme], url.host())

    if url.port() != -1:
        proxy.setPort(url.port())
    if url.userName():
        proxy.setUser(url.userName())
    if url.password():
        proxy.setPassword(url.password())
    return proxy


class ProxyFactory(QNetworkProxyFactory):
    """
    Handle proxy at the application level.
    """
    CUSTOM_PROXY = None

    def queryProxy(self, query):
        if self.CUSTOM_PROXY is None:
            proxies = QNetworkProxyFactory.systemProxyForQuery(query)
        else:
            proxies = [self.CUSTOM_PROXY]

        for p in proxies:
            if p.type() != QNetworkProxy.NoProxy:
                capabilities = p.capabilities()
                if proxy_dns_requests.value:
                    capabilities |= QNetworkProxy.HostNameLookupCapability
                else:
                    capabilities &= ~QNetworkProxy.HostNameLookupCapability
                p.setCapabilities(capabilities)
        return proxies
