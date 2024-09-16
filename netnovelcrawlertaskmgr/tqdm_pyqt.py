# -*- coding: utf-8 -*-
# @Time    : 2024/9/15 15:30
# @Author  : YQ Tsui
# @File    : tqdm_pyqt.py
# @Purpose :


from queue import Queue, Empty
from typing import Callable, Any

# from PyQt5 import QtTest
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, Qt
from PyQt6.QtWidgets import QProgressBar

__CONFIGURED = False


def setup_tqdm_pyqt():
    if not __CONFIGURED:
        tqdm_update_queue = Queue()
        perform_tqdm_pyqt_hack(tqdm_update_queue=tqdm_update_queue)
        return TQDMDataQueueReceiver(tqdm_update_queue)


def perform_tqdm_pyqt_hack(tqdm_update_queue: Queue):
    import tqdm  # pylint: disable=import-outside-toplevel

    # save original class into module
    tqdm.original_class = tqdm.std.tqdm
    parent = tqdm.std.tqdm

    class TQDMPatch(parent):
        """
        Derive from original class
        """

        def __init__(
            self,
            iterable=None,
            desc=None,
            total=None,
            leave=True,
            file=None,
            ncols=None,
            mininterval=0.1,
            maxinterval=10.0,
            miniters=None,
            ascii_=None,
            disable=False,
            unit="it",
            unit_scale=False,
            dynamic_ncols=False,
            smoothing=0.3,
            bar_format=None,
            initial=0,
            position=None,
            postfix=None,
            unit_divisor=1000,
            write_bytes=None,
            lock_args=None,
            nrows=None,
            colour=None,
            delay=0,
            gui=False,
            **kwargs,
        ):
            self.tqdm_update_queue = tqdm_update_queue
            super(TQDMPatch, self).__init__(
                iterable,
                desc,
                total,
                leave,
                file,  # no change here
                ncols,
                mininterval,
                maxinterval,
                miniters,
                ascii_,
                disable,
                unit,
                unit_scale,
                False,  # change param ?
                smoothing,
                bar_format,
                initial,
                position,
                postfix,
                unit_divisor,
                gui,
                **kwargs,
            )
            self.tqdm_update_queue.put({"do_reset": True, "pos": self.pos or 0})

        # def update(self, n=1):
        #     super(TQDMPatch, self).update(n=n)
        #     custom stuff ?

        def refresh(self, nolock=False, lock_args=None):
            super(TQDMPatch, self).refresh(nolock=nolock, lock_args=lock_args)
            d = self.format_dict
            d["pos"] = self.pos
            self.tqdm_update_queue.put(d)

        def close(self):
            self.tqdm_update_queue.put({"close": True, "pos": self.pos})
            super(TQDMPatch, self).close()

    # change original class with the patched one, the original still exists
    tqdm.std.tqdm = TQDMPatch
    tqdm.tqdm = TQDMPatch  # may not be necessary
    # for tqdm.auto users, maybe some additional stuff is needed ?


class TQDMDataQueueReceiver(QObject):
    s_tqdm_object_received_signal = pyqtSignal(object)

    def __init__(self, q: Queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = q
        self._active = False

    @pyqtSlot()
    def run(self):
        self._active = True
        while self._active:
            try:
                o = self.queue.get(timeout=1)
            except Empty:
                continue
            self.s_tqdm_object_received_signal.emit(o)


class QTQDMProgressBar(QProgressBar):
    def __init__(self, name: Any, tqdm_signal: pyqtSignal, parent=None):
        super(QTQDMProgressBar, self).__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVisible(True)
        self.setStyleSheet(
            """
            QProgressBar {
                height: 24px;  /* Set the height of the progress bar */
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f3f3f3;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                width: 16px;
            }
        """
        )
        self.name = name
        tqdm_signal.connect(self.do_it)

    def do_it(self, e):
        if not isinstance(e, dict):
            return
        do_reset = e.get("do_reset", False)  # different from close, because we want visible=true
        initial = e.get("initial", 0)
        total = e.get("total", 0)
        n = e.get("n", -1)
        desc = e.get("prefix", None)
        text = e.get("text", None)
        do_close = e.get("close", False)  # different from do_reset, we want visible=false
        if do_reset:
            self.reset()
        if do_close:
            self.reset()
        self.setMinimum(initial)
        self.setMaximum(total)
        if n >= 0:
            self.setValue(n)
        if desc:
            self.setFormat(f"{desc} %v/%m | %p%")
        elif text:
            self.setFormat(text)
        else:
            self.setFormat("%v/%m | %p")


class LongProcedureWorker(QObject):
    started = pyqtSignal(bool)
    finished = pyqtSignal(bool)

    def __init__(self, identifier: Any, func: Callable):
        super(LongProcedureWorker, self).__init__()
        self.id = identifier
        self.func = func

    @pyqtSlot()
    def run(self):
        self.started.emit(True)
        self.func()
        self.finished.emit(True)
