Advanced topics
===============

.. current-keymap:: global

Managing views
**************

It is possible to manage multiple views in webmacs window:

- :key:`C-x 2` split the current view in two horizontally.
- :key:`C-x 3` split the current view in two vertically.
- :key:`C-x o` navigates in current window views.
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

Then you can navigate using arrow keys or standard emacs bindings:

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
