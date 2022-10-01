import logging

from PyQt6.QtCore import QRunnable, QObject, QThreadPool, QEvent


class RunnableFinishedEvent(QEvent):
    TYPE = QEvent.registerEventType()

    def __init__(self, error, data):
        QEvent.__init__(self, self.TYPE)
        self.error = error
        self.data = data


class Runner(QObject):
    description = None

    def __init__(self, on_finished=None):
        QObject.__init__(self)
        self._on_finished = on_finished

    def __str__(self):
        return self.description or self.__class__.__name__

    def customEvent(self, evt):
        if evt.type() == RunnableFinishedEvent.TYPE:
            try:
                self.finished(evt.error, evt.data)
            except Exception:
                logging.exception("Error while finalizing task %s", self)
            finally:
                Runnable.RUNNING_TASKS.remove(self)
                self.deleteLater()
                logging.debug("Task %s finished.", self)

    def finished(self, result, data):
        if self._on_finished:
            self._on_finished(result, data)

    def run_in_thread(self):
        raise NotImplementedError


class Runnable(QRunnable):
    # python garbage collector issue - we need to keep runners
    # referenced until we are done with them.
    RUNNING_TASKS = []

    def __init__(self, runner):
        QRunnable.__init__(self)
        assert isinstance(runner, Runner)
        assert runner.parent() is None
        self.runner = runner
        self.RUNNING_TASKS.append(runner)

    def run(self):
        from .application import app  # noqa

        error = False
        result = None

        try:
            result = self.runner.run_in_thread()
        except Exception:
            error = True
            logging.exception("Exception while handling thread runner %s."
                              % self.runner)
        finally:
            evt = RunnableFinishedEvent(error, result)
            app().postEvent(self.runner, evt)


def run(runner):
    logging.debug("Starting task %s...", runner)
    QThreadPool.globalInstance().start(
        Runnable(runner)
    )
