from .crawlerengine import HttpEngine
from .corebase import CatalogCrawlerBase
from bs4 import BeautifulSoup
from urllib.parse import urljoin

GARBAGE_TEXTS = [
    "夜读库更新速度全网最快",
    "夜读库更新速度最快",
    "小主，这个章节后面还有哦，请点击下一页继续阅读，后面更精彩！",
    "这章没有结束，请点击下一页继续阅读！",
]


class YedukuCrawlerCore(HttpEngine, CatalogCrawlerBase):

    def __init__(self, start_page: str, text_file: str, config: dict):
        HttpEngine.__init__(self, start_page)
        CatalogCrawlerBase.__init__(self, start_page, text_file, config)

    def _parse_catalog(self, catalog_page):
        chapter_list = []
        while True:
            catalog_page_html = self.session.get(catalog_page).text
            catalog_page_soup = BeautifulSoup(catalog_page_html, "html.parser")
            catalog_node_list = catalog_page_soup.find("ul", attrs={"class": "read"}).find_all("a")
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
            next_href_node = catalog_page_soup.find("div", attrs={"class": "pagelist"}).find("a", string="下一页")
            if next_href_node:
                catalog_page = urljoin(self.base_url, next_href_node.get("href"))
            else:
                break
        return chapter_list

    def _parse_content_page(self, content_page, isVIP=False):
        paragraph_node_list = []
        while True:
            content_page_html = self.session.get(content_page).text
            content_page_soup = BeautifulSoup(content_page_html, "html.parser")
            paragraph_node_list.extend(content_page_soup.find("div", attrs={"class": "content"}).find_all("p"))
            next_href_node = content_page_soup.find("div", attrs={"class": "pager"}).find("a", string="下一页")
            if next_href_node:
                content_page = urljoin(self.base_url, next_href_node.get("href"))
            else:
                break
        return "\n\u3000\u3000".join(
            paragraph_node.get_text()
            for paragraph_node in paragraph_node_list
            if "夜读库更新速度全网最快" not in paragraph_node.get_text()
        )

    def _clean_up_text(self, text):
        for garbage_text in GARBAGE_TEXTS:
            text = text.replace(garbage_text, "")
        return text
