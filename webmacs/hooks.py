class Hook(list):
    def call(self, *arg, **kwargs):
        for callback in self:
            callback(*arg, **kwargs)

    add = list.append


webview_created = Hook()

webview_closed = Hook()
