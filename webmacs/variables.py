VARIABLES = {}


class VariableConditionError(Exception):
    "Raised when a variable condition is not fulfilled"


def condition(func, doc):
    def _condition(value):
        if not func(value):
            assert False, doc

    _condition.__doc__ = doc
    return _condition


class Variable(object):
    __slots__ = ("name", "doc", "value", "conditions", "callbacks", "type")

    def __init__(self, name, doc, value, conditions=(), callbacks=(),
                 type=None):
        self.name = name
        self.doc = doc
        self.conditions = conditions
        assert isinstance(type, Type)
        self.type = type
        self.validate(value)
        self.value = value
        self.callbacks = callbacks

    def validate(self, value):
        self.type.validate(value)
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


class Type(object):
    def validate(self, value):
        pass


class ChoiceMixin(object):
    def __init__(self, choices=None, **kwargs):
        super().__init__(**kwargs)
        self.choices = choices

    def validate(self, value):
        super().validate(value)
        if self.choices and value not in self.choices:
            raise VariableConditionError("Must be one of %r"
                                         % (tuple(self.choices),))


class RangeMixin(object):
    def __init__(self, min=None, max=None, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max

    def validate(self, value):
        super().validate(value)
        if self.min is not None and value < self.min:
            raise VariableConditionError(
                "Must be greater or equal to %s" % self.min
            )
        if self.max is not None and value > self.max:
            raise VariableConditionError(
                "Must be lesser or equal to %s" % self.max
            )


class String(ChoiceMixin, Type):
    def validate(self, value):
        if not isinstance(value, str):
            raise VariableConditionError("Must be a string")
        super().validate(value)


class Int(ChoiceMixin, RangeMixin, Type):
    def validate(self, value):
        if not isinstance(value, int):
            raise VariableConditionError("Must be an integer")
        super().validate(value)


class Float(ChoiceMixin, RangeMixin, Type):
    def validate(self, value):
        if not isinstance(value, float):
            raise VariableConditionError("Must be a float")
        super().validate(value)


class Bool(Type):
    def validate(self, value):
        if not isinstance(value, bool):
            raise VariableConditionError("Must be True or False")


class List(Type):
    def __init__(self, type):
        self.type = type

    def validate(self, value):
        if not isinstance(value, (tuple, list)):
            raise VariableConditionError("Must be a list")

        for i, v in enumerate(value):
            try:
                self.type.validate(v)
            except VariableConditionError as exc:
                raise VariableConditionError("List at position %d: %s"
                                             % (i, exc)) from None


class Tuple(Type):
    def __init__(self, *types):
        self.types = types

    def validate(self, value):
        if not (isinstance(value, (tuple, list))
                and len(self.types) == len(value)):
            raise VariableConditionError("Must be a tuple of size %d"
                                         % len(self.types))
        for i, v in enumerate(value):
            try:
                self.types[i].validate(value[i])
            except VariableConditionError as exc:
                raise VariableConditionError("Tuple at position %d: %s"
                                             % (i, exc)) from None


class Dict(Type):
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type

    def validate(self, value):
        if not (isinstance(value, dict)):
            raise VariableConditionError("Must be a dict")
        for k, v in value.items():
            try:
                self.key_type.validate(k)
            except VariableConditionError as exc:
                raise VariableConditionError("Key %r: %s" % (k, exc))
            try:
                self.value_type.validate(v)
            except VariableConditionError as exc:
                raise VariableConditionError("Value for key %r: %s" % (k, exc))


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
    """
    Returns the variable value.

    :param name: the name of the variable.
    """
    return get_variable(name).value


def set(name, value):
    """
    Set a value for a variable.

    :param name: the name of the variable.
    :param value: the new value.
    :raises: KeyError if the variable does not exists, or
             :class:`VariableConditionError` if the value is incorrect.
    """
    get_variable(name).set_value(value)


define_variable(
    "home-page",
    "Defines the url to use when webmacs starts. If set to the empty"
    " string, the last session will be loaded. You can set it to"
    " 'about:blank' if you want an empty page.",
    "",
    type=String(),
)

define_variable(
    "home-page-in-new-window",
    "Use the home page when creating a new window with *make-window*."
    " Default to False.",
    False,
    type=Bool()
)
