# This file is part of webmacs.
#
# webmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# webmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webmacs.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

from setuptools import setup, Extension, find_packages
from setuptools.command.test import test as TestCommand


THIS_DIR = os.path.dirname(os.path.realpath(__file__))

bloom_dir = os.path.join(THIS_DIR, "vendor", "bloom-filter-cpp")
hashset_dir = os.path.join(THIS_DIR, "vendor", "hashset-cpp")
adblock_dir = os.path.join(THIS_DIR, "vendor", "ad-block")


if "CC" not in os.environ:
    # force g++, not sure why but else gcc is used and the code does not
    # compile...
    os.environ["CC"] = "g++"

adblocker = Extension(
    '_adblock',
    define_macros=[],
    language="c++",
    include_dirs=[bloom_dir, hashset_dir, adblock_dir],
    # not sure if that help for speed. Careful it strip the debug symbols
    extra_compile_args=["-g0", "-std=c++11"],
    sources=[
        os.path.join(bloom_dir, "BloomFilter.cpp"),
        os.path.join(bloom_dir, "hashFn.cpp"),
        os.path.join(hashset_dir, "HashSet.cpp"),
        os.path.join(adblock_dir, "ad_block_client.cc"),
        os.path.join(adblock_dir, "filter.cc"),
        os.path.join(adblock_dir, "cosmetic_filter.cc"),
        os.path.join(THIS_DIR, "c", "adblock.c"),
    ])


class PyTest(TestCommand):
    def run_tests(self):
        import pytest
        sys.path.insert(0, THIS_DIR)
        errno = pytest.main([os.path.join(THIS_DIR, "tests")])
        sys.exit(errno)


setup(
    name='webmacs',
    version='1.0',
    description='Keyboard driven web browser, emacs-like',
    author='Julien Pagès',
    author_email='j.parkouss@gmail.com',
    url='todo',
    long_description='''
Work in progress.
''',
    packages=find_packages(),
    install_requires=["dateparser", "jinja2"],
    tests_require=["pytest"],
    cmdclass={'test': PyTest},
    entry_points={"console_scripts": ["webmacs = webmacs.main:main"]},
    package_data={"webmacs": [
        "app_style.css",
        "scripts/*.js",
        "scheme_handlers/webmacs/js/*.js",
        "scheme_handlers/webmacs/templates/*.html",
    ]},
    python_requires=">=3.3",
    ext_modules=[adblocker],
)
