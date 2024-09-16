# -*- coding: utf-8 -*-
# @Time    : 2024/9/15 13:47
# @Author  : YQ Tsui
# @File    : taskmgrui.py
# @Purpose :
import copy


from .taskmgr import TaskMgr
from netnovelcrawler import Crawler

from PyQt6 import QtWidgets, QtCore, QtGui
from .tqdm_pyqt import QTQDMProgressBar, setup_tqdm_pyqt, LongProcedureWorker


class TaskFrame(QtWidgets.QFrame):

    def __init__(self, task_info: dict, parent=None):
        super(TaskFrame, self).__init__(parent)
        task_info = copy.deepcopy(task_info)
        self.name: str = task_info.pop("name")
        self.path: str = task_info.pop("path")
        self.start_page: str = task_info.pop("start_page")
        self.task_configs: dict = task_info
        self.init_ui()
        self.thread = None
        self.crawler = None
        self.worker = None

    def init_ui(self):

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Maximum)
        self.setFixedWidth(550)
        self.setStyleSheet(
            """
            QFrame {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            }
        """
        )  # Set card-like appearance

        info_str = f"书名：{self.name}\n目录页：{self.start_page}\n工作路径：{self.path}"
        info_label = QtWidgets.QLabel(info_str, parent=self)

        self.start_button = QtWidgets.QPushButton("\u25B6", parent=self)
        self.start_button.clicked.connect(self.run_task)
        self.start_button.setFixedWidth(60)

        other_config_button = QtWidgets.QPushButton("\u2699", parent=self)
        other_config_button.clicked.connect(self.show_configs)
        other_config_button.setEnabled(bool(self.task_configs))
        other_config_button.setFixedWidth(60)

        vbox_btn = QtWidgets.QVBoxLayout()
        vbox_btn.addWidget(self.start_button)
        vbox_btn.addWidget(other_config_button)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(info_label)
        hbox.addLayout(vbox_btn)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addLayout(hbox)
        self.setLayout(self.vbox)

    def show_configs(self):
        config_str = "\n".join(f"{fname}: {fvalue}" for fname, fvalue in self.task_configs.items())
        QtWidgets.QMessageBox.information(
            self,
            "任务设置",
            config_str,
            buttons=QtWidgets.QMessageBox.StandardButton.NoButton,
            defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton,
        )

    @QtCore.pyqtSlot()
    def run_task(self):

        self.thread_tqdm_update_queue_listener = QtCore.QThread()
        # must be done before any TQDM import
        self.tqdm_update_receiver = setup_tqdm_pyqt()
        self.tqdm_update_receiver.moveToThread(self.thread_tqdm_update_queue_listener)
        self.thread_tqdm_update_queue_listener.started.connect(self.tqdm_update_receiver.run)
        self.thread_tqdm_update_queue_listener.finished.connect(self.thread_tqdm_update_queue_listener.deleteLater)

        self.thread_tqdm_update_queue_listener.start()
        self.progress_bar = QTQDMProgressBar(
            name=self.name, tqdm_signal=self.tqdm_update_receiver.s_tqdm_object_received_signal, parent=self
        )
        self.crawler = Crawler(self.path, self.start_page, self.name + ".txt", **self.task_configs)
        self.worker = LongProcedureWorker(identifier=self.name, func=self.crawler.crawl)
        self.vbox.addWidget(self.progress_bar)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.started.connect(self.block_all)

        self.worker.finished.connect(self.on_task_finish)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_task_finish(self):
        self.cleanup_progress_bar()
        self.tqdm_update_receiver._active = False
        self.tqdm_update_receiver.deleteLater()

        self.allow_all()
        self.worker.deleteLater()
        self.thread_tqdm_update_queue_listener.quit()
        self.thread.quit()

    def cleanup_progress_bar(self):
        if self.progress_bar is not None:
            self.progress_bar.close()
            self.vbox.removeWidget(self.progress_bar)
            del self.progress_bar
            self.progress_bar = None

    def block_all(self):
        parent = self.parent()
        for task_frame in parent.findChildren(TaskFrame):
            task_frame.start_button.setEnabled(False)

    def allow_all(self):
        parent = self.parent()
        for task_frame in parent.findChildren(TaskFrame):
            task_frame.start_button.setEnabled(True)


class ConfigEditor(QtWidgets.QDialog):

    IMAGE_PROCESS_MAP = {
        "无图片": "none",
        "保存": "save",
        "OCR": "ocr",
    }

    def __init__(self, task_info: dict = None):
        super(ConfigEditor, self).__init__()
        if task_info is not None and not (
            isinstance(task_info, dict) and "name" in task_info and "path" in task_info and "start_page" in task_info
        ):
            raise ValueError("task_info must be a dict with keys 'name', 'path' and 'start_page'")

        self.task_info = {} if task_info is None else task_info
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("任务设置")
        self.setFixedSize(400, 300)

        vbox = QtWidgets.QVBoxLayout()

        if not self.task_info:
            label_name = QtWidgets.QLabel("书名：")
            self.textedit_name = QtWidgets.QLineEdit()
            label_path = QtWidgets.QLabel("工作路径：")
            self.textedit_path = QtWidgets.QLineEdit()
            label_start_page = QtWidgets.QLabel("目录页：")
            self.textedit_start_page = QtWidgets.QLineEdit()
            grid_layout = QtWidgets.QGridLayout()
            grid_layout.addWidget(label_name, 0, 0)
            grid_layout.addWidget(self.textedit_name, 0, 1)
            grid_layout.addWidget(label_path, 1, 0)
            grid_layout.addWidget(self.textedit_path, 1, 1)
            grid_layout.addWidget(label_start_page, 2, 0)
            grid_layout.addWidget(self.textedit_start_page, 2, 1)
            vbox.addLayout(grid_layout)

        need_login = self.task_info.get("need_login", True)
        if need_login:
            self.need_login_label = QtWidgets.QLabel("需要登录")
            self.need_login_cb = QtWidgets.QCheckBox()
            self.need_login_cb.setChecked(need_login)
            username_label = QtWidgets.QLabel("用户名：")
            self.username_edit = QtWidgets.QLineEdit()
            password_label = QtWidgets.QLabel("密码：")
            self.password_edit = QtWidgets.QLineEdit()
            self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            username, passwd = self.task_info.get("login_info", ("", ""))
            self.username_edit.setText(username)
            self.password_edit.setText(passwd)
            self.need_login_cb.stateChanged.connect(self.username_edit.setEnabled)
            self.need_login_cb.stateChanged.connect(self.password_edit.setEnabled)
            self.need_login_cb.stateChanged.connect(username_label.setVisible)
            self.need_login_cb.stateChanged.connect(password_label.setVisible)
            self.need_login_cb.stateChanged.connect(self.username_edit.setVisible)
            self.need_login_cb.stateChanged.connect(self.password_edit.setVisible)
            grid_layout2 = QtWidgets.QGridLayout()
            grid_layout2.addWidget(self.need_login_label, 0, 0)
            grid_layout2.addWidget(self.need_login_cb, 0, 1)
            grid_layout2.addWidget(username_label, 1, 0)
            grid_layout2.addWidget(self.username_edit, 1, 1)
            grid_layout2.addWidget(password_label, 2, 0)
            grid_layout2.addWidget(self.password_edit, 2, 1)
            vbox.addLayout(grid_layout2)

        grid_layout3 = QtWidgets.QGridLayout()
        image_handler_label = QtWidgets.QLabel("图片处理方式")
        self.image_handler_cb = QtWidgets.QComboBox()
        self.image_handler_cb.addItems(["无图片", "保存", "OCR"])
        image_folder_label = QtWidgets.QLabel("图片保存路径")
        self.image_folder_edit = QtWidgets.QLineEdit()
        self.image_folder_edit.setDisabled(True)
        self.image_handler_cb.currentIndexChanged.connect(self.on_image_handler_change)
        grid_layout3.addWidget(image_handler_label, 0, 0)
        grid_layout3.addWidget(self.image_handler_cb, 0, 1)
        grid_layout3.addWidget(image_folder_label, 1, 0)
        grid_layout3.addWidget(self.image_folder_edit, 1, 1)
        vbox.addLayout(grid_layout3)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        vbox.addWidget(button_box)

        self.setLayout(vbox)

    def on_image_handler_change(self, index):
        self.image_folder_edit.setDisabled(index == 0)

    def get_task_info(self):
        task_info = {}
        if not self.task_info:
            task_info["name"] = self.textedit_name.text()
            task_info["path"] = self.textedit_path.text()
            task_info["start_page"] = self.textedit_start_page.text()
        else:
            task_info.update(self.task_info)
        if self.need_login_cb.isChecked():
            task_info["need_login"] = True
            task_info["login_info"] = (self.username_edit.text(), self.password_edit.text())
        else:
            task_info["need_login"] = False

        image_process_method = self.IMAGE_PROCESS_MAP[self.image_handler_cb.currentText()]
        if image_process_method != "none":
            task_info["image_process"] = image_process_method
            task_info["image_folder"] = self.image_folder_edit.text()

        return task_info


class TasksWindow(QtWidgets.QMainWindow):

    def __init__(self, tasks_mgr: TaskMgr, parent=None) -> None:

        super().__init__(parent=parent)
        self.tasks_mgr = tasks_mgr
        self.init_ui()

    def init_ui(self):

        self.setWindowTitle("任务管理")
        self.setFixedWidth(1200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)

        self.menu_bar = self.menuBar()
        self.menu_bar.setNativeMenuBar(False)
        action: QtGui.QAction = QtGui.QAction("添加任务", self)
        action.triggered.connect(self.add_task)
        self.menu_bar.addAction(action)

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self.gbox = QtWidgets.QGridLayout()
        container: QtWidgets.QWidget = QtWidgets.QWidget(parent=scroll_area)

        for idx, task_info in enumerate(self.tasks_mgr.task_list):
            task_frame = TaskFrame(task_info, parent=container)
            self.gbox.addWidget(task_frame, idx // 2, idx % 2, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        container.setLayout(self.gbox)
        container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)

        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        self.show()

    def add_task(self):
        config_editor = ConfigEditor()
        if config_editor.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            task_info = config_editor.get_task_info()
            self.tasks_mgr.add_task(task_info)
            task_frame = TaskFrame(task_info, parent=self.centralWidget().widget())
            idx = len(self.tasks_mgr.task_list) - 1
            self.gbox.addWidget(task_frame, idx // 2, idx % 2, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
