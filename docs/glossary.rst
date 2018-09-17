Glossary
========

.. glossary::

  buffer
  web buffer
    The content of a web page, not including its window or view.

    You can learn the basics of buffer handing in :ref:`managing_buffers`.

  command
  commands
    A command is a named action doable in the browser.

    See :ref:`concept_commands` for a detailed description.

    See :ref:`Commands <user_conf_commands>` for a list of commands, or better
    use the :cmd:`describe-commands` command to get live documentation.

  hinting
   hinting is used to navigate through visible links and objects of the current
   web buffer's page using the keyboard only.

   See :ref:`link_hinting` for more information.

  key binding
  key bindings
    A **key binding** is a combination of key presses used to trigger commands.

    See :ref:`concept_commands` for a detailed description, and
    :ref:`user_conf_binding_keys` for custom configuration of key bindings.

  keymap
  keymaps
    A **keymap** is an object holding a mapping between key bindings and
    commands.

    See :ref:`concept_commands` for a detailed description.

    See :ref:`Keymaps <user_conf_keymaps>` for a list of keymaps, or better use
    the :cmd:`describe-bindings` command to get live documentation.

  minibuffer
    The minibuffer is what can be seen at the bottom of a webmacs window. It
    displays some information on the right, like the currently active keymap and
    the number of opened buffers.

  minibuffer input
    When webmacs is waiting some information from you, the **minibuffer input**
    is shown: it's a text edit field in which you can type some text.

    Often there also is a completion list above the minibuffer input.

  variable
  variables
    Some behaviors of *webmacs* can be customized using variables.

    See :ref:`user_conf_variables` for variables configuration.

    See :ref:`All variables <user_conf_all_variables>` to see all the variables,
    or better use :cmd:`describe-variables` to get live documentation.

  view
  views
    A view is a part of a window displaying a buffer. There can be multiple
    views in one window.

    See :ref:`managing_views`.

  webjump
  webjumps
    A Webjump represents a quick way to access an url, possibly with a variable
    part. A webjump name becomes a part of the webmacs :cmd:`go-to` command, so
    for example you can type ``google foo bar`` to execute a google query with
    "foo bar" terms.

    See :ref:`user_conf_webjumps` to see the builtins webjumps and how to
    configure you owns.
