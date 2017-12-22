from webmacs.minibuffer.prompt import PromptHistory


def test_history():
    p = PromptHistory(maxsize=10)
    # calling next or previous on empty history is alright
    assert p.get_next() == ""
    assert p.get_previous() == ""
    assert p.in_user_value()  # we are in user value

    # insert some values, a bit more than what the buffer can store
    for i in range(12):
        p.push(str("test_%d" % i))

    # playing around with next/previous
    assert p.get_previous() == "test_11"
    assert p.get_previous() == "test_10"
    assert p.get_next() == "test_11"
    assert not p.in_user_value()

    # we get back in user value when we do an equal amount of next/previous
    # calls
    assert p.get_next() == ""
    assert p.in_user_value()

    # test the custom user value
    p.set_user_value("foobar")

    assert p.get_next() == "test_2"
    assert not p.in_user_value()

    assert p.get_previous() == "foobar"
    assert p.in_user_value()

    assert p.get_next() == "test_2"
    assert not p.in_user_value()

    # resetting put the state back to initial, including the custom user value
    p.reset()
    assert p.in_user_value()
    assert p.get_next() == "test_2"
    assert p.get_previous() == ""
