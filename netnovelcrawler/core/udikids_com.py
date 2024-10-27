# -*- coding: utf-8 -*-
# @Time    : 2024/10/27 11:55
# @Author  : YQ Tsui
# @File    : udikids_com.py.py
# @Purpose :

import time

from .crawlerengine import HttpEngine
from .corebase import CatalogCrawlerBase
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


class UdikidsComCrawlerCore(HttpEngine, CatalogCrawlerBase):

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

        catalog_page_html = self.session.get(catalog_page).text
        catalog_page_soup = BeautifulSoup(catalog_page_html, "html.parser")
        catalog_div = catalog_page_soup.find("div", attrs={"id": "list"})
        temp_node_list = catalog_div.find("dl").find_all()
        start_parse = False
        for node in temp_node_list:
            if node.name == "dt":
                if "全部" in node.get_text():
                    start_parse = True
                else:
                    continue
            if start_parse and node.name == "a":
                node_rel = node.get("rel")
                if node_rel == "chapter" or isinstance(node_rel, list) and "chapter" in node_rel:
                    chapter_list.append(
                        {
                            "title": node.get_text(),
                            "link": urljoin(catalog_page, node.get("href")),
                            "vip": False,
                        }
                    )
        return chapter_list

    def _parse_content_page(self, content_page, isVIP=False):
        parts = []
        while True:
            content_page_html = self.session.get(content_page).text
            content_page_soup = BeautifulSoup(content_page_html, "html.parser")
            content_div = content_page_soup.find("div", attrs={"id": "booktxt"})
            if not content_div:
                if "502 Bad Gateway" in content_page_html:
                    time.sleep(15)
                    continue
            paragraphs = content_div.find_all("p")
            parts.extend([paragraph.text for paragraph in paragraphs])
            next_href_node = content_page_soup.find("div", attrs={"class": "bottem2"}).find(
                "a", attrs={"id": "next_url"}, string=re.compile(r" *下一页 *")
            )
            if next_href_node:
                content_page = urljoin(self.base_url, next_href_node.get("href"))
            else:
                break
        return "\n\u3000\u3000".join(parts)
