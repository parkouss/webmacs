from .commands.webjump import define_webjump

define_webjump("google",
               "https://www.google.fr/search?q=%s&ie=utf-8&oe=utf-8",
               "Google Search")
