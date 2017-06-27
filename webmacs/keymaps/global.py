from ..keymaps import global_key_map

KEYMAP = global_key_map()


KEYMAP.define_key("C-x C-c", "quit")
KEYMAP.define_key("M-x", "M-x")
KEYMAP.define_key("C-x C-f", "go-to-new-buffer")
KEYMAP.define_key("C-x b", "switch-buffer")
KEYMAP.define_key("C-x o", "other-view")
KEYMAP.define_key("C-x 3", "split-view-right")
KEYMAP.define_key("C-x 2", "split-view-bottom")
KEYMAP.define_key("C-x 0", "close-view")
KEYMAP.define_key("C-x 1", "maximise-view")
# handle the case were numbers needs to be hit using shift
KEYMAP.define_key("C-x S-3", "split-view-right")
KEYMAP.define_key("C-x S-2", "split-view-bottom")
KEYMAP.define_key("C-x S-0", "close-view")
KEYMAP.define_key("C-x S-1", "maximise-view")
