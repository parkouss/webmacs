Basic usage
===========

Don't panic
***********

When you are stuck in some interactive :term:`command` or text field and you are
unsure what to do, press **C-g**. This :term:`key binding` usually let you get
out of the current action - you may have to press it more than once. **C-g** is
the universal *get me out of there* command.

.. note::

  Usually pressing **C-g** enough let you focus on the current :term:`web
  buffer` and so activate the :keymap:`webbuffer` :term:`keymap`.


.. current-keymap:: global


Running a command using its name
********************************

It is always possible to run a :term:`command` using its name. Some commands
does not have default :term:`key bindings` and so requires to be called this
way. To call a command using its name, use the :key:`M-x` keybinding, then
select in the list (or type) the command you want to run, followed by **Return**
(the Enter key).

For example, :key:`M-x` toggle-toolbar <Return> will toggle the webmac's
toolbar.


Live documentation
******************

webmacs is self-documenting. You can have access to it easily by running the
following commands:

- :cmd:`describe-commands` to see all available commands.
- :cmd:`describe-command` (bound to :key:`C-h c`) to choose one command and get
  a detailed description.
- :cmd:`describe-variables` to see all the available :term:`variables`.
- :cmd:`describe-variable` (bound to :key:`C-h v`) to choose one variable and
  get a detailed description.
- :cmd:`describe-key` (bound to :key:`C-h k`) to discover what a key binding
  would trigger.
- :cmd:`describe-bindings` to see the list of every keymaps, with the bindings
  and commands they contain.


.. note::

  Self-documentation is super useful for many things. If you want for example to
  define a custom binding for a command but you don't know its name, you can
  always use :key:`C-h k` to help you.

  Also, do not hesitate to use :key:`C-h v` to see the description of a
  :term:`variable`.


.. current-keymap:: webbuffer


Visiting urls
*************

An easy way to go to a new url is to type :key:`g`. This calls the :cmd:`go-to`
command, that lets you type an url or a :term:`webjump`. Pressing **Return**
will then open it in the current web buffer.

For example, try typing: **g g<tab> webmacs <Return>**. This should open a new
google page with the query webmacs.

.. important::

  Typing **C-u** before :key:`g` will open the url or webjump in a new buffer.


.. _link_hinting:

Link hinting
************

Link hinting is used to navigate through visible links of the current web
buffer's page using the keyboard only.

Press :key:`f`. You should see the :term:`minibuffer` right label displaying
that you are in the :keymap:`hint` keymap, and the links on the page
highlighted.

.. current-keymap:: hint

Hinting in webmacs can be done using two methods: filter (the default) and
alphabet. You can use the :term:`variable` :var:`hint-method` to change it.

filter
------

There is one active hint. Typing text will narrow down the hint selection by
fuzzy matching against the link's texts. It is also possible to directly type
the number of the link to activate it, and to cycle the visible hints (next,
previous) to change the active hint.

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
randomly. This is configured with the :term:`variable`
:var:`hint-alphabet-characters`, defaulting to the home row characters of a
qwerty keyboard.


.. current-keymap:: webbuffer


.. _managing_buffers:

Managing buffers
****************

You can switch to a buffer using :key:`C-x b (global)`, which opens a list on
top of the :term:`minibuffer`. Select the buffer you want to switch to by
fuzzy-matching text of the url or title page, or just use the arrow keys (or
better, standard emacs bindings such as **C-n**, **C-p**, **C-v**, **M-v**, etc)
and validate with **Return**.

.. important::

  Most of the lists displayed in the :term:`minibuffer` works in the same way
  and have the same basic bindings.

The command is called :cmd:`switch-recent-buffer`.

.. note::

  The above command order the buffers so the most recently used is on top. If
  you want the buffers to be ordeded by their numbers, you can call the
  command :cmd:`switch-buffer`.


You can also navigate to the next or previous buffer by using respectively
:key:`M-n (global)` and :key:`M-p (global)`.


A buffer can be closed by just pressing :key:`q`. When you are running
:cmd:`switch-buffer` or :cmd:`switch-recent-buffer`, pressing :key:`C-k
(buffer-list)` will also kills the buffer currently highlighted in the list.


.. important::

  If you killed a buffer by accident, no worries! Just use :key:`C-x r (global)`
  to resurrect it.


Navigating through buffer history
*********************************

- :key:`B` goes backward in the buffer history
- :key:`F` goes forward in the buffer history
- :key:`b` shows current buffer's history as a list in the :term:`minibuffer`
  and allows to navigate in there easily.


Navigating through global history
*********************************

Type :key:`h` to display a list of every visited urls (those are saved in a
database file and are persistent in your profile). Select one to open it in the
current buffer.

.. note::

  Use **C-u** before :key:`h` to open the url in a new buffer.


Scrolling in current web buffer
*******************************

- :key:`C-n` or :key:`n` scroll the current buffer down a bit.
- :key:`C-p` or :key:`p` scroll the current buffer up a bit.
- :key:`C-b` scroll the current buffer left a bit.
- :key:`C-f` scroll the current buffer right a bit.

- :key:`C-v` scroll the current buffer down for one visible page.
- :key:`M-v` scroll the current buffer up for one visible page.

- :key:`M-<` lets you go to the top of the page.
- :key:`M->` lets you go to the bottom of the page.


Searching in current web buffer
*******************************

Type :key:`C-s` to start incremental search. Then you can type the text you are
looking for. Press :key:`C-s` again to go to the next match, or :key:`C-r` to go
to the previous match.

.. note::

  :key:`C-r` can also be used to start incremental search.


Copying links
*************

- :key:`c u` to copy the url of the current buffer.
- :key:`c l` to copy a visible link in the buffer (by :term:`hinting`).
- :key:`c c` to copy the currently selected link.
- :key:`c t` to copy the current buffer page title.


Downloading
***********

A download can be started by clicking on a link or button or :term:`hinting`.

When a download is about to be started, the :term:`minibuffer` will propose to
either **download** or **open** it.

- **download** will start downloading, and save the file in your hard drive.
- **open** will temporarily download, then will open the file with the given
  command. A list of available commands is shown in the minibuffer completion
  list. Note when the command will exit, the file will be automatically deleted
  from your hard drive.

  .. note::

    open is useful for viewing pdf files for example, as you can use your
    preferred pdf file viewer to read it.

The list of downloads can be accessed using the :cmd:`downloads` command.

.. seealso::

  See the :var:`default-download-dir` and :var:`keep-temporary-download-dir`
  variables.


Zooming
*******

- :key:`+` zoom in.
- :key:`-` zoom out.
- :key:`=` reset the zoom to its default value.

.. note::

  There are variants for the zoom, using the Control modifier (:key:`C-+`,
  :key:`C--`, and :key:`C-=` that are used for text zoom only.
