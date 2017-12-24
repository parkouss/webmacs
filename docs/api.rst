Public api
==========


Initialisation
**************

.. autofunction:: webmacs.main.init


Keymaps
*******

.. autofunction:: webmacs.keymaps.global_key_map

.. autodata:: webmacs.webbuffer.KEYMAP
   :annotation: The keymap used in web buffers when there is nothing editable
		focused.

.. autoclass:: webmacs.keymaps.Keymap
   :members: define_key
