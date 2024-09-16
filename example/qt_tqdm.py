# This is derived from my own stackoverflow question and answer
# Question: https://stackoverflow.com/questions/55050685/how-to-correctly-redirect-stdout-logging-and-tqdm-into-a-pyqt-widget
# Answer  : https://stackoverflow.com/a/74091829/7237062
#
# IMPROVEMENTS here:
# - captures up to 10 TQDM progress bars
#
# ------------- LICENSE -------------
#  Stack overflow content is supposed to be CC BY-SA 4.0 license: https://creativecommons.org/licenses/by-sa/4.0/
#  so this applies to the question and answer above

import contextlib
import logging
import sys
from abc import ABC, abstractmethod
from queue import Queue
from typing import Dict

from PyQt6 import QtTest
from PyQt6.QtCore import PYQT_VERSION_STR, pyqtSignal, pyqtSlot, QObject, Qt, QT_VERSION_STR, QThread
from PyQt6.QtWidgets import QApplication, QGridLayout, QPlainTextEdit, QProgressBar, QToolButton, QVBoxLayout, QWidget

__CONFIGURED = False


def setup_tqdm_pyqt():
    if not __CONFIGURED:
        tqdm_update_queue = Queue()
        perform_tqdm_pyqt_hack(tqdm_update_queue=tqdm_update_queue)
        return TQDMDataQueueReceiver(tqdm_update_queue)


def perform_tqdm_pyqt_hack(tqdm_update_queue: Queue):
    import tqdm

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
            ascii=None,
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
            print("TQDM Patch called")  # check it works
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
                ascii,
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
            print(self.pos)
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

    @pyqtSlot()
    def run(self):
        while True:
            o = self.queue.get()
            # noinspection PyUnresolvedReferences
            self.s_tqdm_object_received_signal.emit(o)


class QTQDMProgressBar(QProgressBar):
    def __init__(self, parent, pos: int, tqdm_signal: pyqtSignal):
        super(QTQDMProgressBar, self).__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVisible(True)
        self.setMaximumHeight(15)
        self.setMinimumHeight(10)
        self.pos = pos
        # noinspection PyUnresolvedReferences
        tqdm_signal.connect(self.do_it)

    def do_it(self, e):
        if not isinstance(e, dict):
            return
        pos = e.get("pos", None)
        if pos != self.pos:
            return
        do_reset = e.get("do_reset", False)  # different from close, because we want visible=true
        initial = e.get("initial", 0)
        total = e.get("total", None)
        n = e.get("n", None)
        desc = e.get("prefix", None)
        text = e.get("text", None)
        do_close = e.get("close", False)  # different from do_reset, we want visible=false
        if do_reset:
            self.reset()
        if do_close:
            self.reset()
        # self.setVisible(not do_close)
        if initial:
            self.setMinimum(initial)
        else:
            self.setMinimum(0)
        if total:
            self.setMaximum(total)
        else:
            self.setMaximum(0)
        if n:
            self.setValue(n)
        if desc:
            self.setFormat(f"{desc} %v/%m | %p %")
        elif text:
            self.setFormat(text)
        else:
            self.setFormat("%v/%m | %p")


def long_procedure(identifier: int, launch_count: int):
    # emulate late import of modules
    from tqdm.auto import tqdm
    from tqdm.contrib.logging import logging_redirect_tqdm

    __logger = logging.getLogger("long_procedure")
    __logger.setLevel(logging.DEBUG)
    tqdm_object = tqdm(range(10), unit_scale=True, dynamic_ncols=True)
    tqdm_object.set_description(f"long_procedure [id {identifier}] Launch count: [{launch_count}]")
    # with logging_redirect_tqdm():
    for i in tqdm_object:
        QtTest.QTest.qWait(1500)
        __logger.info(f"[id {identifier} | count{launch_count}] step {i}")


class QtLoggingHelper(ABC):
    @abstractmethod
    def transform(self, msg: str):
        raise NotImplementedError()


class QtLoggingBasic(QtLoggingHelper):
    def transform(self, msg: str):
        return msg


class QtLoggingColoredLogs(QtLoggingHelper):
    def __init__(self):
        # offensive programming: crash if necessary if import is not present
        pass

    def transform(self, msg: str):
        import coloredlogs.converter

        msg_html = coloredlogs.converter.convert(msg)
        return msg_html


class QTextEditLogger(logging.Handler, QObject):
    appendText = pyqtSignal(str)

    def __init__(
        self,
        logger_: logging.Logger,
        formatter: logging.Formatter,
        text_widget: QPlainTextEdit,
        # table_widget: QTableWidget,
        parent: QWidget,
    ):
        super(QTextEditLogger, self).__init__()
        super(QObject, self).__init__(parent=parent)
        self.text_widget = text_widget
        self.text_widget.setReadOnly(True)
        # self.table_widget = table_widget
        try:
            self.helper = QtLoggingColoredLogs()
            self.appendText.connect(self.text_widget.appendHtml)
            logger_.info("Using QtLoggingColoredLogs")
        except ImportError:
            self.helper = QtLoggingBasic()
            self.appendText.connect(self.text_widget.appendPlainText)
            logger_.warning("Using QtLoggingBasic")
        # logTextBox = QTextEditLogger(self)
        # You can format what is printed to text box
        self.setFormatter(formatter)
        logger_.addHandler(self)
        # You can control the logging level
        self.setLevel(logging.DEBUG)

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        display_msg = self.helper.transform(msg=msg)
        self.appendText.emit(display_msg)
        # self.add_row(record)


class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.setLevel(logging.DEBUG)
        layout = QVBoxLayout()
        self.setMinimumWidth(650)
        self.thread_tqdm_update_queue_listener = QThread()
        # must be done before any TQDM import
        self.tqdm_update_receiver = setup_tqdm_pyqt()
        self.tqdm_update_receiver.moveToThread(self.thread_tqdm_update_queue_listener)
        self.thread_tqdm_update_queue_listener.started.connect(self.tqdm_update_receiver.run)
        self.pb_dict: Dict[int, QTQDMProgressBar] = {}
        self.btn_dict: Dict[int, QToolButton] = {}
        self.worker_dict: Dict[int, LongProcedureWorker] = {}
        self.thread_dict: Dict[int, QThread] = {}
        for col_idx in range(10):
            pb = QTQDMProgressBar(
                self, pos=col_idx, tqdm_signal=self.tqdm_update_receiver.s_tqdm_object_received_signal
            )
            worker = LongProcedureWorker(identifier=col_idx)
            thread = QThread()
            thread.setObjectName(f"Thread {col_idx}")
            btn = QToolButton(self)
            btn.setText(f"Long processing {col_idx}")
            btn.clicked.connect(thread.start)
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.started.connect(btn.setDisabled)
            worker.finished.connect(btn.setEnabled)
            worker.finished.connect(thread.quit)
            self.pb_dict[col_idx] = pb
            self.btn_dict[col_idx] = btn
            self.worker_dict[col_idx] = worker
            self.thread_dict[col_idx] = thread
        self.thread_tqdm_update_queue_listener.start()
        self.plain_text_edit_logger = QPlainTextEdit(self)
        LOG_FMT = "{thread:7d}-{threadName:10.10} | {asctime} | {levelname:10s} | {message}"
        try:
            import coloredlogs

            FORMATTER = coloredlogs.ColoredFormatter(fmt=LOG_FMT, style="{")
        except ImportError:
            FORMATTER = logging.Formatter(fmt=LOG_FMT, style="{")

        self.logging_ = QTextEditLogger(
            logger_=logging.getLogger(),  # root logger, to intercept every log of app
            formatter=FORMATTER,
            text_widget=self.plain_text_edit_logger,
            parent=self,
        )

        self.widget_btns = QWidget(self)
        q_grid_layout = QGridLayout(self.widget_btns)
        self.widget_btns.setLayout(q_grid_layout)
        for idx in sorted(self.btn_dict.keys(), reverse=True):
            b = self.btn_dict[idx]
            j = int(idx % (len(self.btn_dict.values()) / 2))
            i = int(idx // (len(self.btn_dict.values()) / 2))
            q_grid_layout.addWidget(b, i, j)
        layout.addWidget(self.widget_btns)
        layout.addWidget(self.plain_text_edit_logger)
        for pb in self.pb_dict.values():
            layout.addWidget(pb)
        self.setLayout(layout)
        import tqdm

        self.__logger.info(f"tqdm {tqdm.__version__}")
        self.__logger.info(f"Qt={QT_VERSION_STR}; PyQt={PYQT_VERSION_STR}")
        with contextlib.suppress(ImportError):
            import coloredlogs
        self.__logger.info(f"coloredlogs {coloredlogs.__version__}")
        self.show()


class LongProcedureWorker(QObject):
    started = pyqtSignal(bool)
    finished = pyqtSignal(bool)

    def __init__(self, identifier: int):
        super(LongProcedureWorker, self).__init__()
        # self._main_app = main_app
        self.id = identifier
        self.launch_count = 0

    @pyqtSlot()
    def run(self):
        self.launch_count += 1
        self.started.emit(True)
        long_procedure(self.id, self.launch_count)
        self.finished.emit(True)

    def deleteLater(self):
        print("deleting LongProcedureWorker")
        super(LongProcedureWorker, self).deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = MainApp()
    sys.exit(app.exec())
