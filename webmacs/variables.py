VARIABLES = {}


class VariableConditionError(Exception):
    pass


def condition(func, doc):
    def _condition(value):
        if not func(value):
            assert False, doc

    _condition.__doc__ = doc
    return _condition


class Variable(object):
    __slots__ = ("name", "doc", "value", "conditions", "callbacks")

    def __init__(self, name, doc, value, conditions=(), callbacks=()):
        self.name = name
        self.doc = doc
        self.conditions = conditions
        self.validate(value)
        self.value = value
        self.callbacks = callbacks

    def validate(self, value):
        for cond in self.conditions:
            try:
                cond(value)
            except Exception as exc:
                raise VariableConditionError(
                    "Condition failed for variable {} with value {}: {}"
                    .format(self.name, repr(value), exc)
                ) from None

    def set_value(self, value):
        if value != self.value:
            self.validate(value)
            self.value = value
            for callback in self.callbacks:
                callback(self)

    def add_callback(self, callback):
        if not isinstance(self.callbacks, list):
            self.callbacks = list(self.callbacks)
        self.callbacks.append(callback)


def define_variable(name, doc, value, **kwargs):
    var = Variable(name, doc, value, **kwargs)
    VARIABLES[name] = var
    return var


def get_variable(name):
    try:
        return VARIABLES[name]
    except KeyError:
        raise KeyError("No such variable %s" % name)


def get(name):
    return get_variable(name).value


def set(name, value):
    get_variable(name).set_value(value)
