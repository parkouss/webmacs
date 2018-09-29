Advanced topics
===============

.. current-keymap:: global


.. _managing_views:

Managing views
**************

It is possible to manage multiple :term:`views` in a webmacs window:

- :key:`C-x 2` split the current view in two horizontally.
- :key:`C-x 3` split the current view in two vertically.
- :key:`C-x o` navigate in current window views.
- :key:`C-x 0` close the current view.
- :key:`C-x 1` maximize the current view, closing every other view.


Managing windows
****************

You can also manage multiple windows:


- :cmd:`make-window` to create a new window.
- :cmd:`other-window` to navigate through windows.
- :cmd:`close-window` to close the current window.
- :cmd:`close-other-windows` to close all but the current window.


Caret browsing
**************

.. current-keymap:: caret-browsing

Caret browsing allows to navigate in a web page using a caret. It is mainly
useful for copying text inside a web page without using the mouse.

It is enabled by pressing :key:`C (webbuffer)`.

Then you can navigate using arrow keys or standard Emacs bindings:

- :key:`C-n` to go to the next line.
- :key:`C-p` to go to the previous line.
- :key:`C-f` to go to the next character.
- :key:`C-b` to go to the previous character.
- :key:`M-f` to go to the next word.
- :key:`M-b` to go to the previous word.
- :key:`C-e` to go to the end of the line.
- :key:`C-a` to go to the beginning of the line.

You can select some text and copy it using:

- :key:`C-Space` to toggle the mark
- :key:`M-w` to copy the current selection to the clipboard.

.. current-keymap:: webbuffer

.. note::

  Incremental search can be used when in caret browsing, to allow easier
  navigation.

  It is also great to start caret browsing after an incremental search, as the
  caret will be at the beginning of the current web selection.


Bookmarks
*********

Bookmarks are like a dictionary of URLs. Each bookmark must have a unique name.
Bookmarks are stored in the profile, and hence are persistent across sessions.

It is possible to manage bookmarks using:

- :key:`M` to create a bookmark.
- :key:`m` to open the bookmark list.

When in the bookmark list, you can:

- :key:`Return (bookmarks-list)` to open the bookmark URL in the current buffer
- :key:`C-k (bookmarks-list)` to remove the highlighted bookmark.
