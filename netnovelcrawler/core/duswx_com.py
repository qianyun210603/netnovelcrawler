# -*- coding: utf-8 -*-
# @Time    : 2024/10/6 22:31
# @Author  : YQ Tsui
# @File    : duswx_com.py
# @Purpose :

from .crawlerengine import HttpEngine
from .corebase import CatalogCrawlerBase
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class DuswxComCrawlerCore(HttpEngine, CatalogCrawlerBase):

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

        catalog_page_html = self.session.get(catalog_page).text
        catalog_page_soup = BeautifulSoup(catalog_page_html, "html.parser")
        div_blocks = catalog_page_soup.find("ul", attrs={"id": "newlist"}).find_all("div")
        div_blocks.sort(key=lambda x: int(x.attrs["data-id"]))
        chapter_list = [
            {
                "title": node.get_text(),
                "link": urljoin(catalog_page, node.get("href")),
                "vip": False,
            }
            for div_block in div_blocks
            for node in div_block.find_all("a")
        ]

        return chapter_list

    def _parse_content_page(self, content_page, isVIP=False):
        content_page_html = self.session.get(content_page).text
        content_page_soup = BeautifulSoup(content_page_html, "html.parser")
        content_div = content_page_soup.find("div", attrs={"id": "txt"})
        dd_blocks = sorted(content_div.find_all("dd"), key=lambda x: int(x.attrs["data-id"]))
        content = "\u3000\u3000" + "\n\u3000\u3000".join(
            [p.text for dd_block in dd_blocks if dd_block.attrs["data-id"] != "999" for p in dd_block.find_all("p")]
        )
        return content
