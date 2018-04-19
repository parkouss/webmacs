import logging

from PyQt5.QtCore import QRunnable, QObject, QThreadPool, pyqtSignal as Signal


class Runner(QObject):
    finished = Signal()

    def auto_delete(self):
        return True

    def run(self):
        raise NotImplementedError


class Runnable(QRunnable):
    def __init__(self, runner):
        QRunnable.__init__(self)
        assert isinstance(runner, Runner)
        assert runner.parent() is None
        self.runner = runner

    def run(self):
        try:
            self.runner.run()
        except Exception:
            logging.exception("Exception while handling thread runner %s."
                              % self.runner)
        finally:
            self.runner.finished.emit()
            if self.runner.auto_delete():
                self.runner.deleteLater()


def run(runner):
    QThreadPool.globalInstance().start(
        Runnable(runner)
    )
