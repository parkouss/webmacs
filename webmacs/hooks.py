# This file is part of webmacs.
#
# webmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# webmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webmacs.  If not, see <http://www.gnu.org/licenses/>.


class Hook(list):
    def call(self, *arg, **kwargs):
        for callback in self:
            callback(*arg, **kwargs)

    __call__ = call

    add = list.append


webview_created = Hook()

webview_closed = Hook()

webbuffer_created = Hook()

webbuffer_closed = Hook()

local_mode_changed = Hook()
