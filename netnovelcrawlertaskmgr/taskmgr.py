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
        self.task_dict = {}
        self._load_tasks()

    def _load_tasks(self):
        yaml = YAML()
        if self.task_file.exists():
            with self.task_file.open("r", encoding="utf-8") as f:
                task_dict = yaml.load(f)
                if task_dict:
                    self.task_dict.update(task_dict)

    def _save_tasks(self):
        yaml = YAML()
        with self.task_file.open("w", encoding="utf-8") as f:
            yaml.dump(self.task_dict, f)

    def add_task(self, name, task_info):
        self.task_dict[name] = task_info
        self._save_tasks()

    def delete_task(self, task_name):
        self.task_dict.pop(task_name)
        self._save_tasks()

    def update_task(self, task_name, task_info):
        self.task_dict[task_name] = task_info
        self._save_tasks()
