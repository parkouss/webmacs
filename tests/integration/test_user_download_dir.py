import pytest
import os

from webmacs import download_manager

# should be more or less in unit test section, but uses the variables fixture.


def test_get_user_download_dir(variables, tmpdir):
    # by default, no custom user download dir
    assert download_manager.get_user_download_dir() is None

    d1 = str(tmpdir.mkdir("d1"))
    d2 = str(tmpdir.mkdir("d2"))

    download_manager.TEMPORARY_DOWNLOAD_DIR = d2

    # if default-download-_dir is set, use it
    variables.set("default-download-dir", d1)
    assert download_manager.get_user_download_dir() == d1

    # if keep-temporary-download-dir is set, it takes precendence
    variables.set("keep-temporary-download-dir", True)
    assert download_manager.get_user_download_dir() == d2

    variables.set("default-download-dir", "")
    assert download_manager.get_user_download_dir() == d2


@pytest.mark.parametrize("fname,expected", [
    ("/path/to", ("/path", "to")),
    ("/path/to(1)", ("/path", "to")),
    ("/path/to(3)", ("/path", "to")),
    ("/path/to.txt", ("/path", "to.txt")),
    ("/path/to(1).txt", ("/path", "to.txt")),
    ("/path/to(3).tar.gz", ("/path", "to.tar.gz")),
])
def test_extract_suggested_filename(fname, expected):
    assert download_manager.extract_suggested_filename(fname) == expected


@pytest.mark.parametrize("files, filename, expected", [
    ([], "toto", "toto"),
    (["toto"], "toto", "toto(1)"),
    ([], "toto.txt", "toto.txt"),
    (["toto.txt"], "toto.txt", "toto(1).txt"),
    (["toto.tar.gz", "toto(1).tar.gz"], "toto.tar.gz", "toto(2).tar.gz"),
])
def test_find_unique_suggested_path(tmpdir, files, filename, expected):
    for name in files:
        tmpdir.join(name).ensure(file=True)

    dir = str(tmpdir)

    assert download_manager.find_unique_suggested_path(dir, filename) \
        == os.path.join(dir, expected)
