import pytest

from webmacs.variables import (
    VariableConditionError, String, Int, Bool, Float, List, Tuple, Dict
)


def check_type_error(type, value, regex):
    with pytest.raises(VariableConditionError) as ei:
        type.validate(value)

    assert ei.match(regex)


def test_type_string():
    s = String()
    s.validate("")
    s.validate("hello")
    check_type_error(s, 1, r"Must be a string")

    s = String(choices=["aha", "hoho"])
    s.validate("aha")
    s.validate("hoho")
    check_type_error(s, 1, r"Must be a string")
    check_type_error(s, "invalid", r"Must be one of \('aha', 'hoho'\)")


def test_type_int():
    i = Int()
    i.validate(-5)
    i.validate(0)
    i.validate(5)
    check_type_error(i, "1", r"Must be an integer")

    i = Int(min=0, max=5)
    i.validate(0)
    i.validate(1)
    i.validate(5)
    check_type_error(i, "1", r"Must be an integer")
    check_type_error(i, 6, r"Must be lesser or equal to 5")
    check_type_error(i, -1, r"Must be greater or equal to 0")


def test_type_bool():
    b = Bool()
    b.validate(True)
    b.validate(False)


def test_type_list():
    l = List(Float(min=0.0))  # noqa: E741
    l.validate([])
    l.validate([1.1, 6.1])
    check_type_error(l, 123, "Must be a list")
    check_type_error(l, [2.3, "1"], r"List at position 1: Must be a float")
    check_type_error(l, [-2.3, 3.2],
                     r"List at position 0: Must be greater or equal to 0.0")


def test_type_dict():
    d = Dict(String(), Tuple(Int(), Float(min=0.0, max=1.1)))
    d.validate({})
    d.validate({"1": (1, 0.5)})
    check_type_error(d, 123, "Must be a dict")
    check_type_error(d, {"1": (1,)},
                     "Value for key '1': Must be a tuple of size 2")
