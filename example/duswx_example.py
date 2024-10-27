# -*- coding: utf-8 -*-
# @Time    : 2024/10/6 23:14
# @Author  : YQ Tsui
# @File    : duswx_example.py
# @Purpose :

from netnovelcrawler import Crawler

configs = (
    (
        r"J:\net_novels\crawler_ocr\with_sister",
        {
            "start_page": "http://www.duswx.com/du/5/5360/",
            "text_file": "我和妹子那些事.txt",
        },
    ),
)

if __name__ == "__main__":
    print("enter")
    mycrawler = Crawler(configs[0][0], **configs[0][1])
    print("Successfully created engine and logged in")
    mycrawler.crawl(sleep=1.2)
    print("Crawler completed!")
