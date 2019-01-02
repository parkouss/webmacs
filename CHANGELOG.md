# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [Unreleased]

### Fixed

- Fixed displaying long lines in the minibuffer popup (such as long urls in
  history)
- Fixed regression, unable to revive a buffer.
- webmacs command line now handle correctly opening relative local file paths.
- Fixed scrolling top or bottom when switching view, and losing focus sometimes.
- Use one session file per webmacs instance.

### Added

- Improved customization of key bindings for incremental search, hinting and
  minibuffer
- Added key bindings **C-/** and **C-?** (resp. undo and redo) as minibuffer
  input key bindings
- Added a **clipboard-copy** variable to be able to copy to primary clipboard
  (still the default), mouse selection clipboard or both.
- Added a **--list-instances** command line flag, allowing to list current
  running instances.
- Passing an empty string to the **--instance** command line flag will generate
  a new unique instance name.
- Added a **raise-instance** command, to raise the current window of another
  webmacs instance.
- Added a **current-instance** command that show the name of the current
  instance name.
- Added **C-u C-u** prefix argument for command opening urls. Using it will open
  the chosen url in a new window.
- Added the variable **visited-links-display-limit**, to limit the number of
  elements displayed in the **visited-links-history** command. Defaults to 2000.

## [0.7] - 2018-09-20

### Fixed

- Fix refreshing buffer count in the minibuffer right label when a buffer is
  closed.
- Fix reviving buffers that were not loaded (after restoring a session).
- Fix hinting urls in iframes when opening in a new buffer.
- Fixed support for Qt 5.7
- Fixed requiring escaping of raw % signs in custom webjumps.
- Fixed zoom-normal was bound to **0** instead of **=**.

### Added

- Added the **switch-buffer-current-color** variable that customize the color of
  the current buffer row in the **switch-buffer** displayed list. The color
  defaults to a light blue. Set to an empty string to get the old behavior (no
  specific color).
- **switch-buffer** now list buffers using the internal buffer order.
- Buffers now have numbers and the current buffer number is displayed in the
  minibuffer right label as well as in the **switch-buffer** and
  **switch-recent-buffer** lists.
- **M-n** and **M-p** are bound respectively to the new commands **next-buffer**
  and **previous-buffer**, allowing to cycle through buffers.
- **M-<**, **M->**, **C-v**, **M-v** bindings in the minibuffer lists for
  navigation.
- New commands and bindings added to copy stuff to clipboard.
  **copy-current-link** bound to **c c**, **copy-current-buffer-title** bound to
  **c t**, and copy-current-buffer-url bound to **c u** (all in the webbuffer
  keymap)
- Added a new method for hinting: alphabet. This allow to navigate only using
  the home row keys, and without using Enter. Can be enabled by setting the
  new variable **hint-method** to "alphabet".
- Added a new variable **hint-alphabet-characters** to specify which characters
  to use with the alphabet hinting.
- Added a new variable **hint-node-style** to change the style of the hint div
  nodes.
- Added a **close-buffer-close-window** variable to be able to close a window
  when a buffer is closed.
- **C-g** in webbuffer is now bound to **buffer-escape** instead of
  **buffer-unselect**, which does the same thing and send the Escape too (which
  closes popup and other things).
- Added two variables, **default-download-dir** and
  **keep-temporary-download-dir**.

### Changed

- The old **switch-buffer** behavior is now offered with the
  **switch-recent-buffer** command. The latter is now bound to **C-x b** and
  **C-x C-b** so there is no visible change using those keybindings.
- The **c** (copy-link) binding is now available using **c l** (think about Copy
  Link).
- The css style of the hints has been changed. If you prefer the old style, just
  set the **hint-node-style** variable to {"background": "red", "color":
  "white"}.
- The **go-to** command (bounds to **g**) now set the current url in the
  minibuffer input and select it.
- The **go-to-selected-url** and **go-to-selected-url-new-buffer** commands are
  renamed to **go-to-alternate-url** and **go-to-alternate-url-new-buffer**.
  Also they do not anymore select the current url, but only set the cursor at
  the end of the url.

## [0.6] - 2018-08-20

### Fixed

- crash when opening in a new window (from right-click menu on a link), in qt
  5.11.1.
- crash when reviving closed buffers in some cases.
- crash when calling switch-buffer and closing buffer (including the current
  one) using C-k.

### Added

- added a basic navigation toolbar, that can be shown using the command
  **toggle-toolbar**. Also added a new variable, **window-toolbar-on-startup**
  that can be set to True to show the toolbar automatically.
- added a database to keep feature permissions (geolocation, camera, ...) on a
  per-url basis (thanks to Patrick Lafrance)
- the allow permission for feature dialog now ask for Always/Never, and save
  that in the database. (thanks to Patrick Lafrance)
- it is now possible to answer Never when webmacs ask to save a password.
  (thanks to Patrick Lafrance)
- it is now possible to answer Always to bypass certificate errors. (thanks to
  Patrick Lafrance)
- when opening a download, there is now a prompt to ask to download or to open
  the file with an external command.
  
### Changed

- the functions **webmacs.keymaps.global_keymap()**,
  **webmacs.keymaps.webbuffer_keymap()**,
  **webmacs.keymaps.content_edit_keymap()** have been deprecated in favor of
  **webmacs.keymaps.keymap()** (respectively with the argument "global",
  "webbuffer" and "webcontent-edit").
- loading page information is now displayed in the minibuffer right label, using
  the **loading** key in the **minibuffer-right-label** variable (default value
  of this variable has changed)

## [0.5] - 2018-07-08

### Fixed

- focus is not lost anymore in the minibuffer input on page loading
- adblock is fully disabled when the variable **adblock-urls-rules** is set to
  an empty list.
- adblock cache is rebuilt when the variable **adblock-urls-rules** has changed.
- Fixed the **copy-link** command (**c**) when used with the argument 0.
- Added a space after the default webjump when calling **search-default**.
- Mouse events are now propagated to the minibuffer input and popup.
- Fixed a bug that prevented to use multi-modifiers keybindings (e.g., C-M-a)
- Fixed regression in **close-other-buffers** command.
- The keyboard is not anymore lost when a new buffer is opened from javascript.
- The **follow** command is now working in cross-origin iframes.
- Text edition in web pages is now working in cross-origin iframes.
- Text zoom in web pages is now working in cross-origin iframes.
- Caret navigation is now working in cross-origin iframes.

### Changed

- **scroll-page-down**, **scroll-page-up**, **scroll-bottom** and
  **scroll-top** are now implemented by sending the PageDown, PageUp and End
  and Home key presses.
- **search-default** now defaults to google.

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

