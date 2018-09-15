Basic usage
===========

Don't panic
***********

When you are stuck in some command and you are unsure what to do, press **C-g**.
This binding usually let you get out of the current action - you may have to
press it more than once. **C-g** is the universal *get me out of there* command.

.. note::

  Usually pressing **C-g** enough let you focus on the current web buffer and so
  activate the :keymap:`webbuffer` keymap.


Running a command using its name
********************************

It is always possible to run a command using its name. Some commands does not
have default key bindings and thought requires to be called this way. To call a
command using its name, use the **M-x** keybinding, then select in the list (or
type) the command you want to run, followed by **Return** (the Enter key).

For example, **M-x** toggle-toolbar <Return> will toggle the webmac's toolbar.


Live documentation
******************

.. current-keymap:: global

webmacs is self-documenting. You can have access to it easily by running the
following commands:

- :cmd:`describe-commands` to let you see all available commands.
- :cmd:`describe-command` (bound to :key:`C-h c` to let you choose one command
  and get a detailed description.
- :cmd:`describe-variables` to let you see all the available variables.
- :cmd:`describe-variable` (bound to :key:`C-h v`) to let you choose one
  variable and get a detailed description.
- :cmd:`describe-key` (bound to :key:`C-h k` to discover what a key binding
  would trigger.
- :cmd:`describe-bindings` to see the list of every keymaps, with the bindings
  and commands they contain.


.. note::

  Self-documentation is super useful for many things. If you want for example to
  define a custom binding for a command but you don't know its name, you can
  always use :key:`C-h k` to help you.

  Also, do not hesitate to use :key:`C-h v` to see the description of a
  variable.


Navigation
**********

.. current-keymap:: webbuffer

When you are in the :keymap:`webbuffer` keymap:

- :key:`C-n` or :key:`n` scroll the current buffer down a bit.
- :key:`C-p` or :key:`p` scroll the current buffer up a bit.
- :key:`C-b` scroll the current buffer left a bit.
- :key:`C-f` scroll the current buffer right a bit.

- :key:`C-v` scroll the current buffer down for one visible page.
- :key:`M-v` scroll the current buffer up for one visible page.

- :key:`M-<` lets you go to the top of the page.
- :key:`M->` lets you go to the bottom of the page.

Zooming
*******

When you are in the :keymap:`webbuffer` keymap:

- :key:`+` zoom in.
- :key:`-` zoom out.
- :key:`=` reset the zoom to its default value.

.. note::

  There are variants for the zoom, using the Control modifier (:key:`C-+`,
  :key:`C--`, and :key:`C-=` that are used for text zoom only.


Link hinting
************

Link hinting is used to navigate through visible links of the current web
buffer's page using the keyboard only.

When you are in the :keymap:`webbuffer` keymap, press :key:`f`. You should see
the minibuffer right label displaying that you are in the :keymap:`hint` keymap,
and the links on the page highlighted.

.. current-keymap:: hint

Hinting in webmacs can be done using two methods: filter (the default) and
alphabet. You can use the variable :var:`hint-method` to change it.

filter
------

This is conkeror-like method. There is one active hint. Typing text will narrow
down the hint selection by fuzzy matching against the link's texts. It is also
possible to directly type the number of the link to activate it, and to cycle
the visible hints (next, previous) to change the active hint.

Keybindings are as follow:

- :key:`C-n` activate next visible hint
- :key:`C-p` activate previous visible hint

Note to validate hinting, :key:`Return` has to be pressed.

alphabet
--------

This is the method used by default in vimium for example. There is no active
hint, and to each link some characters are associated: there must be entered all
to validate hinting.

Note usually the home row on the keyboard is used to pick up the characters
randomly. This is configured with the variable :var:`hint-alphabet-characters`,
defaulting to the home row characters of a qwerty keyboard.
