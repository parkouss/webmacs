# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [Unreleased]

### Fixed

- Mouse events are now propagated to the minibuffer input and popup.
- Fixed a bug that prevented to use multi-modifiers keybindings (e.g., C-M-a)
- Fixed regression in **close-other-buffers** command.
- The keyboard is not anymore lost when a new buffer is opened from javascript.
- The **follow** command is now working in cross-origin iframes.
- Text edition in web pages is now working in cross-origin iframes.
- Text zoom in web pages is now working in cross-origin iframes.
- Caret navigation is now working in cross-origin iframes.

### Changed

- Use smooth scroll in **scroll-page-down** and **scroll-page-up**.

### Added

- The minibuffer input now flashes under some circumstances to grab user's
  attention.
- Added **minibuffer-flash-duration**, **minibuffer-flash-color**, and
  **minibuffer-flash-count** variables to customize the flash animation.

## [0.4] - 2018-05-04

### Fixed

- Fixed closing buffer in some circumstances using C-k from the
  switch-buffer command.
- Improved position of the minibuffer popup, removing empty pixels
  between the popup and the input.
- Fixed using i-search when caret browsing is enabled
- improve using multiple views, fixing a lot of bugs around that (keyboard
  focus lost, crash using switch-buffer on an already displayed buffer, ...)

### Changed

- **breaking change**. The completion\_fn argument in define\_webjump has
  changed, see the documentation about that.
- improved webjump completions in multiple ways.
- switching buffers now tries its best to keep the current scroll and cursor
  position, so that coming back to a previous buffer feels more natural. This
  is in part implemented by keeping one internal qt webengineview per buffer.
- improved the visibility of the current view when there are multiple
  views. There is now a border on each side of the view, with one pixel red and
  one black.

### Added

- added a **revive-buffer** command, bound to **C-x r** in the global keymap.
  This allow to reopen a previously closed buffer.
- added the **revive-buffers-limit** variable, to specify how many buffers might
  be revived. This defaults to 10.
- added basic handling of web features to enable video, audio from javascript.
- added two variables to customize how webmacs starts: **home-page** and
  **home-page-in-new-window**.
- added a command to restore previous session (windows and buffers),
  **restore-session**.
- Under X11, if the --instance is passed at the command line, the
  WM_CLASS property is set to "webmacs-{instance}".
- added basic support for multiple windows. New commands added: **make-window**,
  **other-window**, **close-window**, **close-other-window**.
- saving and restoring web views in session
- saving and restoring window position and state in session
- added a variable **webview-stylesheet** to customize the above view style.
- added a command **buffer-unselect** to clear selection in the current buffer.
- bound **buffer-unselect** to **C-g** in the webbuffer keymap.

## [0.3]

### Added

- keymaps can now have a name and associated documentation
- added command **describe-commands** to list all named webmacs commands
- added command **describe-bindings** to list named commands in named keymaps
- added command **describe-variables** to list named webmacs variables
- added command **downloads** to open a buffer to see downloads of the session
- added command **version** to open a version buffer.
- added command **describe-variable** to describe a variable (bound to C-h v)
- added command **describe-command** to describe a command (bound to C-h c)
- added command **describe-key** to describe a keychord (bound to C-h k)
- added python dependency *pygments* to render source code.
- added a command line flag **--instance** to run named instances of webmacs

### Fixed

- If webmacs has crashed, the local socket used for ipc is now cleaned, so other
  commands for this webmacs instance are forwarded and does not anymore create a
  new instance.
- do not set the webbuffer active keymap as the current local keymap if the
  minibuffer input is currently opened.


## [0.2]

The distinction between 0.1 and 0.2 version is not clear unfortunately - patches
were just going in the main git branch. To highlight some features, let's start
the version 0.2 from the commit cb0cea39eaab6a01ee74ca16261c2b467b4af5a3.

### Added

- buffers loading from last session are delayed until they are displayed
- added caret browsing support, with a specific keymap and its set of commands.
  The **C** binding in a web buffer enter the caret browsing mode
- added new variable **adblock-urls-rules** to list rules url for the ad-blocker
- added new variable **webjump-default**
- better prompt completion
- added information in the minibuffer
- added new variable **minibuffer-right-label** for the format of the displayed
  information in the minibuffer
- support for bookmarks (see **bookmark-add** and **bookmark-open** commands,
  bound to respectively **M** and **m** in the webbuffer keymap).
- support for zoom and text zoom. See the **zoom-\*** and **text-zoom-\***
  commands.
- added undefine_key method on Keymaps to unbind keys
- added command **close-other-buffers**
- added basic notion of mode to a web buffer, normal usage being "standard-mode"
  and a new mode "no-keybindings"
- added new variable **auto-buffer-modes** to set up rules for settings web
  buffer mode based on urls
- added new command **content-edit-open-external-editor** to open a text editor
  to edit web content, bound to **Cx e** and **C-x C-e** in the webcontent-edit
  keymap. The external command to run is stored in the variable
  **external-editor-command**.
- added **content-edit-undo** and **content-edit-redo** commands, bound
  respectively to **C-/** and **C-?** in webcontent-edit keymap.
- added spell check support, configurable with the
  **spell-checking-dictionaries** variable.

### Fixed

- fixed segfault with some graphic cards
- retrieving ad-block rules and compiling them is now done in a thread, so
  webmacs is not slow at startup anymore
- added a warning when using opengl with the nouveau driver.
- default qt shortcuts in webviews are removed, so webmacs bindings are working
  without side-effect anymore (e.g., C-a was sometimes selecting the text)
- changed implementation of the webcontent-edit movement text commands, so now
  undo redo works better and it also mostly works in contenteditable fields

