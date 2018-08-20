Public api
==========


Initialisation
**************

.. autofunction:: webmacs.main.init


Keymaps
*******

.. autofunction:: webmacs.keymaps.keymap

.. autoclass:: webmacs.keymaps.Keymap
   :members: define_key, undefine_key


Webjumps
********

.. autofunction:: webmacs.commands.webjump.define_webjump

.. autoclass:: webmacs.commands.webjump.WebJumpCompleter
   :members:

.. autoclass:: webmacs.commands.webjump.WebJumpRequestCompleter

.. autoclass:: webmacs.commands.webjump.SyncWebJumpCompleter


Variables
*********

.. autofunction:: webmacs.variables.set

.. autofunction:: webmacs.variables.get

.. autoexception:: webmacs.variables.VariableConditionError
