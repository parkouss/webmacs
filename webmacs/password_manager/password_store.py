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


from . import BasePaswordManager, Credentials, PasswordManagerNotReady
from ..task import Task
from .. import variables

from PyQt6.QtCore import QProcess

import os
import logging
import glob


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


class ReadCredentialsTask(Task):
    def __init__(self):
        Task.__init__(self)
        self.__names = None
        # one proc at a time, otherwise authentication might fail;;
        self.__proc = None
        self.__output = b""
        self.__credentials = PassCredentials()

    def start(self):
        self.__names = [os.path.splitext(fname)[0] for fname in
                        glob.glob("**/*.gpg", recursive=True,
                                  root_dir=pass_store_path.value)]

        self.__process_next()

    def __process_next(self):
        self.__output = b""
        if not self.__names:
            self.finished.emit()
            return

        self.__name = name = self.__names.pop(0)
        self.__proc = QProcess()
        self.__proc.finished.connect(self.__process_finished)
        self.__proc.readyReadStandardOutput.connect(self.__process_read)
        logging.info(f"Running external command: pass show {name}")
        self.__proc.start("pass", ["show", name])

    def __process_finished(self, code, status):
        if status == QProcess.ExitStatus.CrashExit:
            self.set_error_message("The pass process crashed.")
            self.finished.emit()
        elif code != 0:
            self.set_error_message(f"The pass process exited with {code}.")
            self.finished.emit()
        else:
            lines = self.__output.decode("utf-8").splitlines()
            passwd = lines[0].rstrip()
            fields = {}
            for line in lines[1:]:
                try:
                    k, v = line.split(":", 1)
                except ValueError:
                    pass
                else:
                    fields[k.rstrip()] = v.strip()
                username = fields.pop("login", None)
                self.__credentials.add_credential(self.__name, fields.pop("url", None),
                                                  Credentials(username, passwd, fields))
            self.__process_next()

    def __process_read(self):
        self.__output += bytes(self.__proc.readAllStandardOutput())

    def credentials(self):
        return self.__credentials

    def abort(self):
        if self.__proc:
            self.__proc.finished.disconnect(self.__process_finished)
            self.__proc.kill()
            self.__proc.waitForFinished(300)


class Pass(BasePaswordManager):
    """
    This is the public object that the rest of the application can use.

    By using reload(), it reads the passwordstore credentials (this takes time,
    a few seconds!) and then keep the data in memory.
    """
    def __init__(self):
        BasePaswordManager.__init__(self)
        self.__creds = None
        self.__reloading = False
        self.reload()

    def __on_reloaded(self):
        self.__reloading = False
        task = self.sender()
        if not task.error():
            self.__creds = task.credentials()

    def reload(self):
        from ..application import app as _app
        if not self.__reloading:
            self.__reloading = True

            app = _app()
            task = ReadCredentialsTask()
            task.finished.connect(self.__on_reloaded)
            app.task_runner.run(task)

    def credential_for_url(self, url):
        if self.__reloading:
            raise PasswordManagerNotReady(
                "passwordstore not ready - still reading configuration.")
        return self.__creds.for_url(url)
