Concepts
========

Please be sure to understand the following basic webmacs concepts before going
further reading the documentation.


Commands, key bindings and keymaps
**********************************

Those are quite similar to the definitions found in the emacs manual.

- A **command** is a named action doable in the browser. For example **follow**
  is the command that allow to start hinting links to navigate.

- A **key binding** is a combination of key chords used to trigger commands. Key
  bindings are represented as in emacs, for example **C-x C-b** means holding
  the Control key while pressing x, then b on the keyboard.

  .. note::

    The control key is called a modifier. There are three keyboard modifiers:

    - **C** represents the Control key.
    - **M** represents the Alt key.
    - **S** represents the Super key (often called the window key)

  .. note::

    A key binding can be a single key press too. For example pressing **f**
    while in the **webbuffer** keymap will trigger the **follow** command.

- A **keymap** is an object holding a mapping between key bindings and commands,
  so that a command can be triggered by pressing keyboard keys. There is one
  global keymap, and one active local keymap usually activated at the same
  time - the local keymap changes interactively depending on the context.

  .. webmacs-keymaps::
    :only: global, webbuffer, webcontent-edit, caret-browsing


Windows, frames
***************

Unlike the terminology in emacs, a window is a what we nowadays usually call a
window and frames are contained in windows.
