__version__ = '0.1'

import importlib


# access to every opened buffers
BUFFERS = []


def require(module, package=__package__):
        return importlib.import_module(module, package)
