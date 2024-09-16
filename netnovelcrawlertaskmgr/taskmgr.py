# -*- coding: utf-8 -*-
# @Time    : 2024/9/15 12:10
# @Author  : YQ Tsui
# @File    : taskmgr.py
# @Purpose :

from pathlib import Path

from ruamel.yaml import YAML


def get_config_path():
    config_path = Path(__file__).parent.joinpath("crawling_tasks.yaml")
    return config_path


class TaskMgr:
    def __init__(self):
        self.task_file = Path(get_config_path())
        self.task_list = []
        self._load_tasks()

    def _load_tasks(self):
        yaml = YAML()
        if self.task_file.exists():
            with self.task_file.open("r", encoding="utf-8") as f:
                task_list = yaml.load(f)
                if task_list:
                    self.task_list.extend(task_list)

    def _save_tasks(self):
        yaml = YAML()
        with self.task_file.open("w", encoding="utf-8") as f:
            yaml.dump(self.task_list, f)

    def add_task(self, task_info):
        self.task_list.append(task_info)
        self._save_tasks()

    def delete_task(self, task_id):
        self.task_list.pop(task_id)
        self._save_tasks()
