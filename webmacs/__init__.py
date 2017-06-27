__version__ = '0.1'

import importlib


def require(module, package=__package__):
        return importlib.import_module(module, package)
