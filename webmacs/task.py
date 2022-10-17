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

import logging

from PyQt6.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot

from . import call_later


class Task(QObject):
    """
    A long running task.

    Note it is designed to be asynchronous - using signals, and if any thread
    is needed, QThreadPool might be used but each subclass must deal with
    concurrency.
    """
    finished = Signal()
    description = None

    def __init__(self):
        QObject.__init__(self)
        self.__error = None

    @Slot()
    def start(self):
        """
        Start the task.
        """

    @Slot()
    def abort(self):
        """
        Abort the task.
        """

    def error(self):
        """
        True if there was an error.
        """
        return bool(self.__error)

    def error_message(self):
        """
        Description of the error if any.
        """
        return self.__error

    def set_error(self, message):
        self.__error = message

    def __str__(self):
        return self.description or self.__class__.__name__


class TaskRunner(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.running_tasks = set()

    def run(self, task):
        """
        Run the task in the next main loop iteration.
        """
        task.finished.connect(self._on_task_finished)
        call_later(task.start)
        logging.info(f"Starting task {task}")
        self.running_tasks.add(task)

    @Slot()
    def stop(self):
        for task in self.running_tasks:
            task.abort()

    def _on_task_finished(self):
        task = self.sender()
        if not task.error():
            logging.info(f"Task {task}: finished.")
        else:
            logging.error(f"Task {task}: Error {task.error_message()}")

        self.running_tasks.remove(task)
