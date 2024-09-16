import abc
import os.path
import pickle
import time
import json
from abc import abstractmethod
from typing import Callable
from tqdm.auto import tqdm

from ..utils.ocr_util import submitOCRRequest, combineText


class CrawlerBase(abc.ABC):

    def __init__(self, start_page: str, text_file: str, config: dict):
        self.start_page = start_page
        self.text_file = text_file
        self.config = config

    def login(self, login_info: dict, login_page: str):
        pass

    @abstractmethod
    def crawl(self, **kwargs):
        raise NotImplementedError("implement in derived class")

    def _set_reading_config(self):
        pass


class CatalogCrawlerBase(CrawlerBase):

    @abstractmethod
    def _parse_catalog(self, catalog_page):
        raise NotImplementedError("implement in derived class")

    @abstractmethod
    def _parse_content_page(self, contentPage, isVIP=False):
        raise NotImplementedError("implement in derived class")

    def _clean_up_text(self, text):
        return text

    @staticmethod
    def _get_status():
        if os.path.exists("status.bin"):
            with open("status.bin", "rb") as f:
                return pickle.load(f)
        else:
            return {}

    @staticmethod
    def _save_status(status):
        with open("status.bin", "wb") as f:
            pickle.dump(status, f)

    def crawl(self, sleep: float = 1, starter: Callable[[dict], bool] = None, stopper: Callable[[dict], bool] = None):
        all_chapters = self._parse_catalog(self.start_page)
        chapters_status = self._get_status()
        prev_no_content = False
        self._set_reading_config()
        with open(self.text_file, "a", encoding="utf-8") as out_file:
            if any(chapter_info.get("vip", False) for chapter_info in all_chapters):
                if not os.path.exists(self.config["image_folder"]):
                    os.mkdir(self.config["image_folder"])

            try:
                with tqdm(total=len(all_chapters)) as pbar:
                    for chapter_info in all_chapters:
                        if chapters_status.get(chapter_info["title"], False):
                            continue
                        if starter is not None and not starter(chapter_info):
                            continue
                        if stopper is not None and stopper(chapter_info):
                            break
                        if not prev_no_content:
                            out_file.write("\n\n")
                        pbar.set_description("Processing %s" % chapter_info["title"])
                        prev_no_content = chapter_info.get("link", None) is None

                        if chapter_info.get("link", None) is not None:
                            content = self._parse_content_page(
                                chapter_info["link"],
                                chapter_info["vip"],
                            )
                            if not chapter_info["vip"]:
                                out_file.write(chapter_info["title"] + "\n")
                                content = self._clean_up_text(content)
                                out_file.write(content)
                                chapters_status[chapter_info["title"]] = True
                            elif self.config["image_process"] == "save":
                                out_file.write(chapter_info["title"] + "\n")
                                content.save(
                                    os.path.join(self.config["image_folder"], chapter_info["title"] + ".png"), "PNG"
                                )
                                out_file.write("@vip_image=vip_image/{}".format(chapter_info["title"]))
                                chapters_status[chapter_info["title"]] = True
                            elif "ocr" in self.config["image_process"]:
                                out_file.write(chapter_info["title"] + "\n")
                                content.save(
                                    os.path.join(self.config["image_folder"], chapter_info["title"] + ".png"), "PNG"
                                )
                                contents = self._preprocess_figure_for_ocr(content)
                                for idx, content in enumerate(contents):
                                    if self.config["image_process"] == "ocr":
                                        for i in range(10):
                                            try:
                                                html = submitOCRRequest(content)
                                                if html:
                                                    break
                                            except Exception:
                                                pass
                                            finally:
                                                time.sleep(60)
                                        with open(
                                            os.path.join(
                                                self.config["image_folder"], chapter_info["title"] + str(idx) + ".txt"
                                            ),
                                            "w",
                                            encoding="utf-8",
                                        ) as f:
                                            f.write(html)
                                        resultdic = json.loads(html)
                                        contentocr = combineText(resultdic["prism_wordsInfo"])
                                        out_file.write(contentocr)
                                    else:
                                        content.save(
                                            os.path.join(
                                                self.config["image_folder"], chapter_info["title"] + str(idx) + ".png"
                                            ),
                                            "PNG",
                                        )
                                chapters_status[chapter_info["title"]] = True
                        time.sleep(sleep)
                        pbar.update(1)
            finally:
                self._save_status(chapters_status)

    def _preprocess_figure_for_ocr(self, fig):
        return [fig]
