User configuration
==================

**webmacs** can be configured by writing Python code. The files should lives in
a ``~/.webmacs/init`` directory, starting with an ``__init__.py`` file.

If this file exists, it will be loaded early in the application.

Note you have the full power of Python in there, and as it is loaded early you
can change and adapt nearly everything of the webmacs behavior.

.. note::

   Only the documented functions and objects here are considered stable (meaning
   it won't change without change notes and explanations). The other api you can
   use is considered internal and might change without notification.


The init function
*****************

You can write a function **init** that would be called when webmacs is about to
start. This function must takes one parameter (usually named *opts*), that
contains the result of the parsed command line. For now, there is only one
useful parameter:

- opts.url:  the url given in the command line, or None

Overriding the init function does override the default init function of webmacs,
though it is still accessible with :func:`webmacs.main.init`. Hello world
example:

.. code-block:: python

   import webmacs.main


   def init(opts):
       print("hello wordl")
       if opts.url:
           print("{} was given as a command line argument".format(opts.url))
       webmacs.main.init(opts)


The default webmacs.main.init function is responsible restoring the session, or
opening the given url for example.


.. note::

   It is not required to create an init function in the user configuration
   _\_init_\_.py file. Only do so if you want to change the default webmacs
   initialization. Other changes can be applied early, directly at the module
   level, such as defining :term:`webjumps` or **binding keys**.


Using more than one configuration file
**************************************

It is possible to write more than one configuration file. The
directory where the ``__init__.py`` file lives is a python package, so
it is possible to just use relative imports.

For example:

``__init__.py``

.. code-block:: python

   from . import webjumps


``webjumps.py``

.. code-block:: python

   print("definition of my custom webjumps should go there.")


.. _user_conf_variables:

Variables
*********

It is possible to change a variable in the configuration using
:func:`webmacs.variables.set`:

.. code-block:: python

   from webmacs import variables

   variables.set("webjump-default", "google ")


.. _user_conf_all_variables:

Here is the list of the variables:

.. webmacs-variables::


Modes
*****

Modes are used to bind keymaps to a web buffer, by assigning the buffer a given
mode. By default all buffers are using the "standard-mode".

Here is the list of the pre-defined modes:

.. webmacs-modes::

Automatically assign modes depending on the url
-----------------------------------------------

You can use the `auto-buffer-modes` variable.

Example:

.. code-block:: python

   import re
   from webmacs import variables

   variables.set("auto-buffer-modes", [
      (".*www.gnu.org.*", "no-keybindings"),
      ("https://mail.google.com/.*", "no-keybindings")
  ])

Binding keys
************

In webmacs, like in emacs, it is possible to bind a key to command on a given
keymap.

.. _user_conf_keymaps:

Keymaps
-------

Here is the list of available keymaps. Note you can see them live (with their
associated key bindings) in webmacs by running the command `describe-bindings`.

.. webmacs-keymaps::

A keymap object in user configuration is retrieved with
:func:`webmacs.keymaps.keymap`.


.. _user_conf_commands:

Commands
--------

Here is the list of the currently available commands:

.. webmacs-commands::


.. _user_conf_binding_keys:

Binding a command to a keymap
-----------------------------

You should use :meth:`webmacs.keymaps.Keymap.define_key`. Here is an example:

.. code-block:: python

   from webmacs import keymaps

   global_map = keymaps.keymap("global")
   global_map.define_key("C-c |", "split-view-right")
   global_map.define_key("C-c _", "split-view-bottom")

   buffer_keymap = keymaps.keymap("webbuffer")
   buffer_keymap.define_key("x", "close-buffer")


.. note::

   The global buffer should not define single letter keychords, as you
   won't be able to type that letter in editable fields, thus this is
   possible in the webbuffer :term:`keymap`.

.. _user_conf_webjumps:

Webjumps
********

Here is the implementation of the google :term:`webjump`:

.. literalinclude:: ../webmacs/default_webjumps.py
   :start-after: # ----------- doc example
   :end-before: # ----------- end of doc example


The list of defined webjumps in webmacs:

.. webmacs-webjumps::


You can implement your own webjumps, or override the existing
ones. See :func:`webmacs.commands.webjump.define_webjump` and the
example above.

By default in webmacs, pressing the ``s`` key will call the command
``search-default``, wich will use the duckduckgo webjump. To change
that default, change the value of the variable *webjump-default*.
