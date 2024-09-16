from collections import namedtuple
import pkgutil
import urllib.request
import urllib.parse
import json
import time
import base64
import numpy as np
from PIL import Image
from io import BytesIO

Size = namedtuple("Size", "width height")
# 请求头
headers = json.loads(pkgutil.get_data(__package__, "appheader.json"))


def posturl(url, data={}):
    try:
        params = json.dumps(data).encode(encoding="UTF8")
        req = urllib.request.Request(url, params, headers)
        with urllib.request.urlopen(req) as r:
            html = r.read()
        return html.decode("utf8")
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read().decode("utf8"))
    time.sleep(1)


def submitOCRRequest(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = str(base64.b64encode(buffered.getvalue()), "utf-8")
    url_request = "https://ocrapi-document.taobao.com/ocrservice/document"
    param = {"img": img_str}
    return posturl(url_request, data=param)


def combineText(prism_words, left_margin=0):
    words = [elem["word"] for elem in prism_words]
    wordslb = [elem["pos"][0]["x"] for elem in prism_words]
    wordsrb = [elem["pos"][1]["x"] for elem in prism_words]
    minlb = min(wordslb)
    charwidthestinp = np.array([(rb - lb) / len(w) for w, lb, rb in zip(words, wordslb, wordsrb)])
    boundary = (
        int(2 * charwidthestinp.mean() - charwidthestinp.std()),
        int(3 * charwidthestinp.mean() + charwidthestinp.std()) - 1,
    )
    if boundary[0] <= minlb - left_margin <= boundary[1]:
        text = "\n".join(words)
    else:
        text = words[0]
        for w, lb in zip(words[1:], wordslb[1:]):
            if boundary[0] <= lb - left_margin <= boundary[1]:
                text += "\n" + w
            else:
                text += w
    return text


class OCRManager:

    def __init__(self, outputbuffer, size_limit, margin, background, tolerence):
        self.outputbuffer = outputbuffer
        self.size_limit = Size(*size_limit)
        self.margin = Size(*margin)
        self.background = background
        self.tolerance = tolerence
        self.content_height_lim = self.size_limit.height - self.margin.height
        self._reset()

    def _reset(self, full_reset=True):
        self.target = Image.new(
            "RGBA", (self.size_limit.width, self.size_limit.height), self.background
        )  # pylint: disable=attribute-defined-outside-init
        self.curr_start = self.margin.height // 2
        self.target_info = []
        if full_reset:
            self.chapter_queue = {}
            self.prevChapter = None

    def _crop_image(self, im, crop_start, crop_height):
        background = np.array(self.background)
        w, h = im.size
        if w > self.size_limit.width - self.margin.width:
            raise ValueError("Image too wide")
        if h - crop_start < crop_height:
            im_c = im.crop([0, crop_start, w, h])
            return im_c, True
        imdata = np.array(im)
        print(imdata.shape)
        trialline = crop_start + crop_height
        while (
            trialline >= crop_start and (np.linalg.norm(imdata[trialline] - background, axis=1) > self.tolerance).any()
        ):
            trialline -= 1
        gapbottom = trialline
        while (
            trialline >= crop_start and (np.linalg.norm(imdata[trialline] - background, axis=1) <= self.tolerance).all()
        ):
            trialline -= 1
        if trialline <= crop_start:
            return None, False
        gaptop = trialline
        gapmid = (gapbottom + gaptop) // 2
        im_c = im.crop([0, crop_start, w, gapmid])
        return im_c, False

    def push_chapter(self, chapter_name, image):
        self.chapter_queue.update({chapter_name: {"contents": [], "is_complete": False}})
        max_w = 0
        crop_start = 0
        while True:
            im_c, cropcomplete = self._crop_image(image, crop_start, self.content_height_lim - self.curr_start)
            if im_c is None:
                self.target = self.target.crop([0, 0, max_w + self.margin.width, self.size_limit.height])
                html = submitOCRRequest(self.target)
                resultdic = json.loads(html)
                for chapname, chap_limit in self.target_info:
                    self.chapter_queue[chapname]["contents"].extend(
                        elem for elem in resultdic["prism_wordsInfo"] if elem["pos"][3]["y"] < chap_limit
                    )
                    if self.prevChapter is not None and self.prevChapter != chapname:
                        self.chapter_queue[self.prevChapter]["is_complete"] = True
                        self.outputbuffer.write(chapter_name + "\n")
                        self.outputbuffer.write(
                            combineText(self.chapter_queue[self.prevChapter]["contents"], self.margin.width // 2)
                        )
                        del self.chapter_queue[self.prevChapter]
                    self.prevChapter = chapname
                self._reset(False)
                im_c, cropcomplete = self._crop_image(image, crop_start, self.content_height_lim - self.curr_start)
            crop_start += im_c.size[1]
            self.target.paste(
                im_c,
                (
                    self.margin.width // 2,
                    self.curr_start,
                    self.margin.width // 2 + im_c.size[0],
                    self.curr_start + im_c.size[1],
                ),
            )
            max_w = max(max_w, im_c.size[0])
            self.curr_start += im_c.size[1]
            self.target_info.append((chapter_name, self.curr_start))
            if cropcomplete:
                break

    def flush(self):
        html = submitOCRRequest(self.target)
        resultdic = json.loads(html)
        for chapname, chap_limit in self.target_info:
            self.chapter_queue[chapname]["contents"].extend(
                elem for elem in resultdic["prism_wordsInfo"] if elem["pos"][3]["y"] < chap_limit
            )
            self.chapter_queue[chapname]["is_complete"] = True
            self.outputbuffer.write(chapname + "\n")
            self.outputbuffer.write(combineText(self.chapter_queue[chapname]["contents"], self.margin.width // 2))
        self._reset()


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    return "\u4e00" <= uchar <= "\u9fa5"


def is_number(uchar):
    """判断一个unicode是否是数字"""
    return "\u0030" <= uchar <= "\u0039"


def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    return ("\u0041" <= uchar <= "\u005a") or ("\u0061" <= uchar <= "\u007a")


def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    return not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar))


def B2Q(uchar):
    """半角转全角"""
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7E:
        # 不是半角字符就返回原来的字符
        return uchar
    if inside_code == 0x0020:
        # 除了空格其他的全角半角的公式为:半角=全角-0xfee0
        inside_code = 0x3000
    else:
        inside_code += 0xFEE0
        return chr(inside_code)


def Q2B(uchar):
    """全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xFEE0
    if inside_code < 0x0020 or inside_code > 0x7E:
        # 转完之后不是半角字符返回原来的字符
        return uchar
    return chr(inside_code)


def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])


def stringB2Q(ustring):
    """把字符串全角转半角"""
    return "".join([B2Q(uchar) for uchar in ustring])


def flatten_pinyin(
    original_figure, projection_array, min_thresh=2, min_width_pinyin=8, min_width_text=20, ratio_prev_max=0.3
):
    begin = 0
    row_count = 0
    prev_maximum = 0
    for i in range(len(projection_array)):  # pylint: disable=consider-using-enumerate
        if projection_array[i] > min_thresh and begin == 0:
            begin = i
            prev_maximum = projection_array[i]
            row_count += 1
            if row_count % 2:
                while projection_array[begin] > 0:
                    begin -= 1
        elif projection_array[i] > max(min_thresh, ratio_prev_max * prev_maximum * (row_count % 2)) and begin != 0:
            prev_maximum = max(projection_array[i], prev_maximum)
        elif (
            begin != 0
            and projection_array[i] <= max(min_thresh, ratio_prev_max * prev_maximum * (row_count % 2))
            and projection_array[i] <= projection_array[i + 1]
            and projection_array[i] <= projection_array[i - 1]
        ):
            min_width = min_width_pinyin if row_count % 2 else min_width_text
            if i - begin >= min_width:
                if row_count % 2:
                    original_figure[begin:i, :] = True
                begin = 0
                prev_maximum = 0
        elif projection_array[i] <= max(min_thresh, ratio_prev_max * prev_maximum * (row_count % 2)) or begin == 0:
            continue
        else:
            print(
                "unknown status: begin = {}, i = {}, prev_max = {}, proj[i] = {}".format(
                    begin, i, prev_maximum, projection_array[i]
                )
            )


def horizontal_cut_for_ocr(img_data, cut_height, min_thresh=0):
    all_cut_figures = []
    projection = img_data.shape[1] - img_data.sum(axis=1)
    cut = 0
    while projection.shape[0] - cut - cut_height > 0:
        end = cut + cut_height
        while end > 0 and projection[end] > min_thresh:
            end -= 1
        begin = end
        while begin > 0 and projection[begin] <= min_thresh:
            begin -= 1
        new_cut = (begin + end) // 2
        all_cut_figures.append(Image.fromarray(img_data[cut:new_cut, :]))
        cut = new_cut

    all_cut_figures.append(Image.fromarray(img_data[cut:, :]))
    return all_cut_figures
