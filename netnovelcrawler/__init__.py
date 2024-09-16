import copy
import os
import pickle

from typing import Callable
from .core.crawlercorefactory import CRAWLER_CORES


class Crawler:

    def __init__(self, work_dir: str, start_page: str = None, text_file: str = None, **kwargs):
        """
        Params:
        ================================================
        work_dir: string(path)
        工作目录，用于存放获取的文本，图片，以及Crawler的配置等

        start_page: string(url)(必须)
        爬行起始页面

        text_file: string(path)(必须)
        用于存储获取的内容的文本文件，或图片索引

        kwargs:
            login_info: tuple of string(可选)
            登录信息
            image_process: {'save', 'ocr'}(可选)
            对图片处理方式
            image_folder: string(path)(可选)
            如image_process='save'，此项为保存的目录
        """
        if not os.path.exists(work_dir):
            os.mkdir(work_dir)
        os.chdir(work_dir)
        if start_page is None or text_file is None:
            config = self._get_config()
            start_page = config.pop("start_page", start_page)
            if start_page is None:
                raise ValueError("start_page is required")
            text_file = config.pop("text_file", text_file)
            if text_file is None:
                raise ValueError("text_file is required")
        temp_config = copy.deepcopy(kwargs)
        temp_config["start_page"] = start_page
        temp_config["text_file"] = text_file
        self._save_config(temp_config)
        login_info = kwargs.pop("login_info", None)

        self.core = self._get_crawler_core(start_page, text_file, kwargs, login_info)

    @staticmethod
    def _get_crawler_core(start_page: str, text_file: str, config: dict, login_info: tuple = None):
        """
        get customized core for different sites
        """
        module_name, core_class_name, login_page = CRAWLER_CORES[start_page.split("/", 3)[2]]
        module = __import__(module_name, fromlist=True)
        core_class = getattr(module, core_class_name)
        core = core_class(start_page, text_file, config)
        if login_info is not None:
            core.login(login_info, login_page)
        return core

    @staticmethod
    def _get_config():
        with open("config.bin", "rb") as f:
            return pickle.load(f)

    @staticmethod
    def _save_config(config):
        with open("config.bin", "wb") as f:
            pickle.dump(config, f)

    def crawl(self, sleep: float = 1, starter: Callable[[dict], bool] = None, stopper: Callable[[dict], bool] = None):
        """
        Params:
        ================================================
        sleep: float
        页面刷新间隔时间
        """

        self.core.crawl(sleep, starter=starter, stopper=stopper)
