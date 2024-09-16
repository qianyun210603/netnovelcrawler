# -*- coding: utf-8 -*-
# @Time    : 2024/9/16 10:16
# @Author  : YQ Tsui
# @File    : n22biqu_com.py
# @Purpose :
import time

from .crawlerengine import HttpEngine
from .corebase import CatalogCrawlerBase
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


class n22BiquComCrawlerCore(HttpEngine, CatalogCrawlerBase):

    def __init__(self, start_page: str, text_file: str, config: dict):
        HttpEngine.__init__(self, start_page)
        CatalogCrawlerBase.__init__(self, start_page, text_file, config)

        self.session.headers.update(
            {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "Connection": "keep-alive",
                "User-agent": "Mozilla/5.0 (Windows NT 10.0; WOW 64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36 QIHU 360SE",
            }
        )

    def _parse_catalog(self, catalog_page):
        chapter_list = []
        while True:
            catalog_page_html = self.session.get(catalog_page).text
            catalog_page_soup = BeautifulSoup(catalog_page_html, "html.parser")
            uls = catalog_page_soup.find_all("ul", attrs={"class": "section-list fix"})
            if not uls:
                break
            ul = uls[-1]
            catalog_node_list = ul.find_all("a")
            chapter_list.extend(
                [
                    {
                        "title": node.get_text(),
                        "link": urljoin(self.base_url, node.get("href")),
                        "vip": False,
                    }
                    for node in catalog_node_list
                ]
            )
            next_href_node = catalog_page_soup.find("div", attrs={"class": "index-container"}).find(
                "a", string="下一页"
            )
            if next_href_node:
                catalog_page = urljoin(self.base_url, next_href_node.get("href"))
            else:
                break
        return chapter_list

    def _parse_content_page(self, content_page, isVIP=False):
        parts = []
        while True:
            content_page_html = self.session.get(content_page).text
            content_page_soup = BeautifulSoup(content_page_html, "html.parser")
            paragraph_div = content_page_soup.find(
                "div",
                attrs={
                    "class": "content",
                    "id": "content",
                },
            )
            if not paragraph_div:
                if "502 Bad Gateway" in content_page_html:
                    time.sleep(15)
                    continue
            paragraphs = paragraph_div.find_all("p")
            parts.extend([paragraph.text for paragraph in paragraphs])
            next_href_node = content_page_soup.find("div", attrs={"class": "section-opt m-bottom-opt"}).find(
                "a", attrs={"id": "next_url"}, string=re.compile(r" *下一页")
            )
            if next_href_node:
                content_page = urljoin(self.base_url, next_href_node.get("href"))
            else:
                break
        return "\n\u3000\u3000".join(parts)

    def _clean_up_text(self, text):
        text = re.sub(r"((\n *)|(\r))\xa0\xa0\xa0\xa0 ?", "\n\u3000\u3000", text)
        return text
