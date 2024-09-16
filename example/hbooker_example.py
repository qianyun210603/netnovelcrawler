from netnovelcrawler import Crawler
from netnovelcrawler.utils.starter_stopper import CountStopper

configs = (
    (
        r"J:\net_novels\crawler_ocr\xianzunmodi",
        {
            "start_page": "https://www.ciweimao.com/chapter-list/100257021/book_detail",
            "login_info": ("test_login", "test_pwd"),
            "image_folder": "vip_images",
            "image_process": "ocr",
            "text_file": "我可是要做仙尊和魔帝的男人.txt",
        },
    ),
)
# '/home/booksword/sister_lover'
if __name__ == "__main__":
    print("enter")
    mycrawler = Crawler(configs[0][0], None)  # configs[0][1])
    print("Successfully created engine and logged in")
    mycrawler.crawl(sleep=10)
    print("Crawler completed!")
