import os

from distutils.core import setup, Extension


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
    extra_compile_args=["-g0"],
    sources=[
        os.path.join(bloom_dir, "BloomFilter.cpp"),
        os.path.join(bloom_dir, "hashFn.cpp"),
        os.path.join(hashset_dir, "HashSet.cpp"),
        os.path.join(adblock_dir, "ad_block_client.cc"),
        os.path.join(adblock_dir, "filter.cc"),
        os.path.join(adblock_dir, "cosmetic_filter.cc"),
        os.path.join(THIS_DIR, "c", "adblock.c"),
    ])

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
    ext_modules=[adblocker])
