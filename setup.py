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
import re
import subprocess

from setuptools import setup, Extension, find_packages
from distutils.command.build_py import build_py as _build_py


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
    extra_compile_args=(["-g0", "-std=c++11"] if os.name != "nt" else []),
    sources=[
        os.path.join(bloom_dir, "BloomFilter.cpp"),
        os.path.join(bloom_dir, "hashFn.cpp"),
        os.path.join(hashset_dir, "hash_set.cc"),
        os.path.join(adblock_dir, "ad_block_client.cc"),
        os.path.join(adblock_dir, "filter.cc"),
        os.path.join(adblock_dir, "cosmetic_filter.cc"),
        os.path.join(adblock_dir, "no_fingerprint_domain.cc"),
        os.path.join(adblock_dir, "protocol.cc"),
        os.path.join(THIS_DIR, "c", "adblock.cc"),
    ])


def get_version():
    with open(os.path.join(THIS_DIR, "webmacs", "__init__.py")) as f:
        version = re.findall("__version__ = '(.+)'", f.read())
    return version[0]


def get_revision():
    # ensure we are in a git dir
    if not os.path.exists(os.path.join(THIS_DIR, ".git")):
        return None
    p = subprocess.Popen(
        ["git", "rev-parse", "HEAD"], cwd=THIS_DIR,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    if p.returncode == 0:
        return out.strip().decode("utf-8")


class build_py(_build_py):
    """
    Override build to generate a revision file to install.
    """
    def run(self):
        rev = get_revision()
        # honor the --dry-run flag
        if not self.dry_run and rev:
            target_dir = os.path.join(self.build_lib, 'webmacs')

            # mkpath is a distutils helper to create directories
            self.mkpath(target_dir)

            with open(os.path.join(target_dir, 'revision'), 'w') as f:
                f.write(rev)

        # distutils uses old-style classes, so no super()
        _build_py.run(self)


setup(
    name='webmacs',
    version=get_version(),
    description='Keyboard driven web browser, emacs-like',
    author='Julien Pagès',
    author_email='j.parkouss@gmail.com',
    url='https://github.com/parkouss/webmacs',
    long_description='''
A browser for keyboard-based web navigation.

Keybindings are emacs-friendly, most of them took from the conkeror
(http://conkeror.org/) project which is not maintained anymore.

It is based on qtwebengine, which in turns uses chromium for the web engine.

Some of the features are:

- integrated ad-blocker
- emacs like navigation nearly everywhere (C-n, C-p, ...)
- hinting to navigate with keyboard only
- and a lot more, see the project url

''',
    packages=find_packages(),
    install_requires=["dateparser", "jinja2", "pygments"],
    entry_points={"console_scripts": ["webmacs = webmacs.main:main"]},
    package_data={"webmacs": [
        "scripts/*.js",
        "scheme_handlers/webmacs/js/*.js",
        "scheme_handlers/webmacs/templates/*.html",
    ]},
    cmdclass={'build_py': build_py},
    python_requires=">=3.3",
    ext_modules=[adblocker],
)
