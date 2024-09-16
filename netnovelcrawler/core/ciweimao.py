from .corebase import CatalogCrawlerBase
from .crawlerengine import SeleniumEngine
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from ..utils.screenshot_util import chrome_takeFullScreenshot
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
import numpy as np


class CiweimaoCrawlerCore(SeleniumEngine, CatalogCrawlerBase):

    def __init__(self, start_page, text_file, config):
        super(CiweimaoCrawlerCore, self).__init__()
        CatalogCrawlerBase.__init__(self, start_page, text_file, config)

    def _auto_login(self, login_info, login_page):
        # 需要考虑自动滑动验证码
        raise NotImplementedError("verification code")

    def _logged_in_condition(self):
        return expected_conditions.visibility_of_any_elements_located((By.LINK_TEXT, "[退出]"))

    def _parse_catalog(self, catalog_page):

        def _get_chapter_info(chapter):
            href = chapter.find_element_by_tag_name("a")
            return {
                "title": href.text,
                "link": href.get_attribute("href"),
                "vip": bool(href.find_elements_by_tag_name("i")),
            }

        self.driver.get(catalog_page)

        volumnlist = self.driver.find_element_by_class_name("book-catalog").find_elements_by_class_name(
            "book-chapter-box"
        )

        all_chapter_list = []
        for volumn in volumnlist:
            volumn_title = volumn.find_element_by_class_name("sub-tit").text
            if bool(volumn_title):
                all_chapter_list.append({"title": volumn_title})
            chapterlist = volumn.find_elements_by_tag_name("li")
            all_chapter_list.extend([_get_chapter_info(chapter) for chapter in chapterlist])

        return all_chapter_list

    def _set_reading_config(self):
        self.driver.delete_cookie("bookReadTheme")
        new_booktheme = {
            "domain": ".www.ciweimao.com",
            "expiry": int((datetime.today() + timedelta(7)).timestamp()),
            "httpOnly": False,
            "name": "bookReadTheme",
            "path": "/",
            "secure": False,
            "value": "white%2C0%2C30%2Cundefined%2Ctsu-hide%2C0",
        }
        self.driver.add_cookie(new_booktheme)

    def _parse_content_page(self, content_page, isVIP=False):

        self.driver.get(content_page)
        if not isVIP:

            def get_text_from_paragraph(driver, paragraph):
                return driver.execute_script(
                    """
                return jQuery(arguments[0]).contents().filter(function() {
                    return this.nodeType == Node.TEXT_NODE;
                }).text();
                """,
                    paragraph,
                )

            chapter_contents = self.driver.find_element_by_id("J_BookRead")
            paragraphs = chapter_contents.find_elements_by_class_name("chapter")
            return "\n".join(get_text_from_paragraph(self.driver, paragraph) for paragraph in paragraphs)
        else:
            bookimage = self.driver.find_element_by_id("realBookImage")
            pos = {**bookimage.location, **bookimage.size, **{"scale": 1}}
            png = chrome_takeFullScreenshot(self.driver, pos)
            imfile = BytesIO(png)
            img = Image.open(imfile)
            imdata = np.array(img)
            imdata[(imdata[:, :, 0] > 215) & (imdata[:, :, 1] > 220)] = np.ones(4) * 255
            img = Image.fromarray(imdata)
            return img
