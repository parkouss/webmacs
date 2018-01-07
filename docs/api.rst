Public api
==========


Initialisation
**************

.. autofunction:: webmacs.main.init


Keymaps
*******

.. autofunction:: webmacs.keymaps.global_keymap

.. autofunction:: webmacs.keymaps.webbuffer_keymap

.. autoclass:: webmacs.keymaps.Keymap
   :members: define_key


Webjumps
********

.. autofunction:: webmacs.commands.webjump.define_webjump


Variables
*********

.. autofunction:: webmacs.variables.set

.. autofunction:: webmacs.variables.get

.. autoexception:: webmacs.variables.VariableConditionError
