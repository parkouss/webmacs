FAQ
===

How do I run a new webmacs instance instead of a new buffer from the command-line?
**********************************************************************************

When a webmacs instance is already running, calling `webmacs <url>` from a
shell will open the URL in a new buffer of the running instance. To run a fresh
new instance, use `webmacs --instance <instance-unique-name> <url>`.


How do I run webmacs with a specific profile from the command-line?
**********************************************************************************
To have webmacs use a specific profile, use
`webmacs --profile <profile-name> <url>`. Each profile directory will contain
distinct navigation data (history, cookies, ...).


Website is blocked, turn off the extensions
*******************************************

This message will appear in the browser when the URL has got filtered by the
ad-blocker.

To overcome this, you can temporarily disable the ad-blocker with *M-x toggle-ad-block*.

For a permanent change, edit the :var:`adblock-urls-rules` variable, to remove
some URLs in there. Note if you set this variable to an empty list, the
adblocker will be completely disabled. See the :ref:`user_conf_variables`
section in the documentation.
