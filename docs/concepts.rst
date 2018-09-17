Concepts
========

Please be sure to understand the following basic webmacs concepts before going
further reading the documentation.


.. _concept_commands:

Commands, key bindings and keymaps
**********************************

Those are quite similar to the definitions found in the emacs manual.

- A :term:`command` is a named action doable in the browser. For example
  :cmd:`follow` is the command that allow to start hinting links to navigate.

- A :term:`key binding` is a combination of key presses used to trigger commands.
  Key bindings are represented as in emacs, for example **C-x C-b** means
  holding the Control key while pressing x, then b on the keyboard.

  .. note::

    The control key is called a modifier. There are three keyboard modifiers:

    - **C** represents the Control key.
    - **M** represents the Alt key.
    - **S** represents the Super key (often called the window key)

  .. note::

    .. current-keymap:: webbuffer

    A key binding can be a single key press too. For example pressing :key:`f`
    while in the :keymap:`webbuffer` keymap will trigger the :cmd:`follow`
    command.

- A :term:`keymap` is an object holding a mapping between key bindings and
  commands, so that a command can be triggered by pressing keyboard keys. There
  is one global keymap, and one active local keymap usually activated at the
  same time - the local keymap changes interactively depending on the context.

  Some important keymaps:

  .. webmacs-keymaps::
    :only: global, webbuffer, webcontent-edit, caret-browsing


Web buffers
***********

A :term:`web buffer` is like an emacs buffer, but for a web page. Buffers are
like tabs in other browsers, except that they are not bound to any view or
window.

Windows, views
**************

Unlike the terminology in emacs, a window is a what we nowadays usually call a
window and :term:`views` (sometimes called frames) are contained in windows.
