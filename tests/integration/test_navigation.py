from webmacs import BUFFERS
from webmacs.webbuffer import create_buffer


def test_cycle_buffers(session):
    """
    Webcontent-edit keymaps are used even in sub frames.
    """
    session.load_page("navigation")
    session.load_page("navigation/page1.html", buffer=create_buffer())

    def on_index_page():
        return session.buffer.title() == "page index"

    def on_first_page():
        return session.buffer.title() == "first page"

    assert len(BUFFERS) == 2
    assert on_index_page()

    session.wkeyclicks("M-n")
    assert session.wait_until(on_first_page)

    session.wkeyclicks("M-n")
    assert session.wait_until(on_index_page)

    session.wkeyclicks("M-p")
    assert session.wait_until(on_first_page)

    session.wkeyclicks("M-p")
    assert session.wait_until(on_index_page)
