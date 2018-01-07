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
   level, such as defining **webjumps** or **binding keys**.


Using more than one configuration file
**************************************

It is possible to write more than one configuration file. The
directory where the ``__init__.py`` file lives is a python package, so
it is possible to just use relative imports.

For example:

``__init__.py``

.. code-block:: python

   import .webjumps


``webjumps.py``

.. code-block:: python

   print("definition of my custom webjumps should go there.")


Variables
*********

Some behaviors of *webmacs* can be customized using variables.

It is possible to change a variable in the configuration using
:func:`webmacs.variables.set`:

.. code-block:: python

   from webmacs import variables

   variables.set("webjump-default", "google ")


Here is the list of the variables:

.. webmacs-variables::


Binding keys
************

In webmacs, like in emacs, it is possible to bind a key to command on a given keymap.

Keymaps
-------

There are multiple keymaps, the most useful are:

- the global keymap (returned by
  :func:`webmacs.keymaps.global_keymap`). This keymap is almost always
  enabled and act as a fallback to the current local keymap.

- the webbuffer keymap (returned by
  :data:`webmacs.keymaps.webbuffer_keymap`). This keymap is active as
  the current local keymap when there is not editable field focused in
  the web content buffer.


Commands
--------

Here is the list of the currently available commands:

.. webmacs-commands::


Binding a command to a keymap
-----------------------------

You should use :meth:`webmacs.keymaps.Keymap.define_key`. Here is an example:

.. code-block:: python

   from webmacs import keymaps

   global_map = keymaps.global_keymap()
   global_map.define_key("C-c |", "split-view-right")
   global_map.define_key("C-c _", "split-view-bottom")

   buffer_keymap = keymaps.webbuffer_keymap()
   buffer_keymap.define_key("x", "close-buffer")


.. note::

   The global buffer should not define single letter keychords, as you
   won't be able to type that letter in editable fields, thus this is
   possible in the webbuffer keymap.


Webjumps
********

Webjumps represents a quick way to access some urls, possibly with a
variable part. A webjump name becomes a part of the webmacs "go-to"
bar, so for example you can type:

``google foo bar``

to execute a google query with "foo bar" terms. Here is the
implementation of the google webjump:

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
