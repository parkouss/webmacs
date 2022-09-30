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


from . import BasePaswordManager, Credentials
from .. import variables

import os
import glob
import subprocess
import threading


pass_store_path = variables.define_variable(
    "password-manager-pass-store-path",
    "The path to store the pass passwords. Defaults to ~/.password-store.",
    os.path.expanduser("~/.password-store"),
    type=variables.String()
)


class PassCredentials:
    """
    Object to store the credentials read from the passwordstore utility.
    """
    def __init__(self):
        self.__cred_by_name = {}
        self.__cred_by_url = {}
        self.__search_needs_compil = True
        self.__search_url_list = None

    def add_credential(self, name, url, credential):
        self.__cred_by_name[name] = credential
        if url:
            self.__cred_by_url[url] = credential
        self.__search_needs_compil = True

    def compile(self):
        if self.__search_needs_compil:
            def by_len_name(tup):
                return len(tup[0])
            shortened_names = [(k.rsplit("/", 1)[-1], v)
                               for k, v in self.__cred_by_name.items()]
            # order by reverse len of url to find best suitable match first
            self.__search_url_list = \
                sorted(self.__cred_by_url.items(),
                       key=by_len_name, reverse=True) + \
                sorted(shortened_names, key=by_len_name,
                       reverse=True)
            self.__search_needs_compil = False

    def for_url(self, url):
        """
        Try to find the appropriate Credential for the given url, or None.
        """
        self.compile()
        for url_part, credential in self.__search_url_list:
            if url.find(url_part) >= 0:
                return credential

    def names(self):
        """
        Return the list of known passwordstore names (file names, without .gpg
        extension)
        """
        return list(self.__cred_by_name.keys())

    def for_name(self, name):
        """
        Return the Credential associated to the given name.
        """
        return self.__cred_by_name[name]


def read_credentials():
    """
    Read passwordstore credentials, and returns an instance of PassCredentials.
    """
    names = [os.path.splitext(fname)[0] for fname in
             glob.glob("**/*.gpg", recursive=True,
                       root_dir=pass_store_path.value)]

    data = PassCredentials()
    for name in names:
        proc = subprocess.Popen(["pass", "show", name], text=True,
                                stdout=subprocess.PIPE)
        passwd = proc.stdout.readline().rstrip()
        fields = {}
        for line in proc.stdout:
            try:
                k, v = line.split(":", 1)
            except ValueError:
                pass
            else:
                fields[k.rstrip()] = v.strip()
        proc.wait()

        username = fields.pop("login", None)
        data.add_credential(name, fields.pop("url", None),
                            Credentials(username, passwd, fields))
    return data


class Pass(BasePaswordManager):
    """
    This is the public object that the rest of the application can use.

    By using reload(), it reads the passwordstore credentials (this takes time,
    a few seconds!) and then keep the data in memory.
    """
    def __init__(self):
        BasePaswordManager.__init__(self)
        self.__creds = None
        self.__reloading = threading.Event()
        self.reload()

    def __reload(self):
        try:
            self.__creds = read_credentials()
        finally:
            self.__reloading.clear()

    def reload(self):
        if not self.__reloading.is_set():
            self.__reloading.set()
            th = threading.Thread(target=self.__reload)
            th.start()

    def credential_for_url(self, url):
        if not self.__reloading.is_set():
            return self.__creds.for_url(url)
