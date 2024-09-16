# -*- coding: utf-8 -*-
# @Time    : 2024/9/15 16:52
# @Author  : YQ Tsui
# @File    : netnovelcrawlertaskmgr.py
# @Purpose :
from PyQt6 import QtWidgets
from netnovelcrawlertaskmgr.taskmgr import TaskMgr
from netnovelcrawlertaskmgr.taskmgrui import TasksWindow
import sys


def run_mgr():
    app = QtWidgets.QApplication(sys.argv)
    taskmgr = TaskMgr()
    ex = TasksWindow(taskmgr)
    sys.exit(app.exec())


if __name__ == "__main__":
    run_mgr()
