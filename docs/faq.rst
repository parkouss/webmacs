FAQ
===

How do I run a new webmacs instance instead of a new buffer from the command-line?
**********************************************************************************

When there is already a webmacs instance running, calling `webmacs <url>` from a
shell will open the url in a new buffer of the running instance. To run a fresh
new instance, use `webmacs --instance <instance-unique-name> <url>`.


Website is blocked, turn off the extensions
*******************************************

This message will appear in the browser when the url was filtered by the
ad-blocker.

You can temporarily disable the ad-blocker with *M-x toggle-ad-block* to
overcome this.

For a permanent change, edit the :var:`adblock-urls-rules` variable, to remove
some urls in there. Note if you set this variable to an empty list, the
adblocker will be completely disabled. See the :ref:`user_conf_variables`
section in the documentation.
