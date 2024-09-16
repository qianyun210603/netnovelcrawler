import os
import re
import base64
from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
from io import BytesIO
from ..utils.ocr_util import flatten_pinyin, horizontal_cut_for_ocr
from .corebase import CatalogCrawlerBase
from .crawlerengine import SeleniumEngine
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions


class SfAcgCrawlerCore(SeleniumEngine, CatalogCrawlerBase):

    def __init__(self, start_page: str, text_file: str, config: dict):
        super(SfAcgCrawlerCore, self).__init__(start_page, text_file, config)
        self.remove_pinyin_config = dict(min_thresh=2, min_width_pinyin=8, min_width_text=20, ratio_prev_max=0.3)

    def _auto_login(self, login_info, login_page):
        # 需要考虑自动滑动验证码
        self.driver.get(login_page)
        self.driver.execute_script("""Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) """)
        self.driver.execute_script("""window.navigator.chrome = { runtime: {},  }; """)
        self.driver.execute_script("""Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });""")
        self.driver.execute_script(
            """Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], });"""
        )

    def _logged_in_condition(self):
        return expected_conditions.text_to_be_present_in_element((By.TAG_NAME, "tbody"), "恭喜您，登录成功")

    def _gen_image_process_config(self, config, chapter_title, isVIP):
        if not isVIP:
            return ()
        if config["image_process"] == "save":
            if not os.path.exists(config["image_folder"]):
                os.mkdir(config["image_folder"])
            return "save", os.path.join(config["image_folder"], chapter_title + "{}.png")
        raise NotImplementedError("Unknow image processing method")

    def _parse_catalog(self, catalog_page):

        def _get_chapter_info(chapter):
            href = chapter.find_element_by_tag_name("a")
            return {
                "title": re.sub("\u3000+", " ", href.text).lstrip("VIP\n"),
                "link": href.get_attribute("href"),
                "vip": "VIP" in href.text,
            }

        self.driver.get(catalog_page)

        volumnlist = self.driver.find_elements_by_class_name("story-catalog")

        all_chapter_list = []
        for volumn in volumnlist:
            volumn_title = volumn.find_element_by_class_name("catalog-title").text
            if bool(volumn_title):
                volumn_title = re.sub("\u3000+", " ", volumn_title)
                all_chapter_list.append({"title": volumn_title})
            chapterlist = volumn.find_element_by_class_name("catalog-list").find_elements_by_tag_name("li")
            all_chapter_list.extend([_get_chapter_info(chapter) for chapter in chapterlist])

        return all_chapter_list

    def _parse_content_page(self, content_page, isVIP=False, image_processing=()):
        self.driver.get(content_page)
        if not isVIP:
            chapter_contents = self.driver.find_element_by_id("ChapterBody")
            paragraphs = chapter_contents.find_elements_by_tag_name("p")
            return "\n　　".join(paragraph.text for paragraph in paragraphs)
        else:
            chapter_contents = self.driver.find_element_by_id("ChapterBody")
            bookimage_elem = chapter_contents.find_element_by_id("vipImage")
            base64str = self.driver.execute_script(
                """
                var c = document.createElement('canvas');
                var ctx = c.getContext('2d');
                var img = document.getElementById('{}');
                c.height=img.naturalHeight;
                c.width=img.naturalWidth;
                ctx.drawImage(img, 0, 0,img.naturalWidth, img.naturalHeight);
                var base64String = c.toDataURL();
                return base64String;
            """.format(
                    bookimage_elem.get_attribute("id")
                )
            )
            _, base64data = re.search("data:image/(?P<ext>.*?);base64,(?P<data>.*)", base64str, re.DOTALL).groups()
            bio = BytesIO(base64.b64decode(base64data))
            return Image.open(bio)

    def _preprocess_figure_for_ocr(self, fig):

        # Step 1. Convert RGBA to RGB
        color = (255, 255, 255)
        fig.load()  # needed for split()
        background = Image.new("RGB", fig.size, color)
        background.paste(fig, mask=fig.split()[3])  # 3 is the alpha channel

        # Step 2. Convert to ndarray and Binarize
        pixel_array = np.array(background)
        mask = (
            (np.abs(pixel_array[:, :, 0] + 255 - pixel_array[:, :, 1]) > 255 + 30)
            | (np.abs(pixel_array[:, :, 1] + 255 - pixel_array[:, :, 2]) > 30 + 255)
            | (np.abs(pixel_array[:, :, 2] + 255 - pixel_array[:, :, 0]) > 30 + 255)
            | (pixel_array > 225).any(axis=2)
        )

        # Step 3. Filter out isolated single pixel
        mask = generic_filter(mask, lambda x: x[4] == 1 or sum(x) == 8, size=3)

        # Step 4. Remove header pinyin
        flatten_pinyin(mask, mask.shape[1] - mask.sum(axis=1), **self.remove_pinyin_config)

        # Step 5. Filter out isolated single pixel again
        mask = generic_filter(mask, lambda x: x[4] == 1 or sum(x) == 8, size=3)

        return horizontal_cut_for_ocr(mask, 6000)
