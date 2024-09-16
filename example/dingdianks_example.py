from netnovelcrawler import Crawler

configs = (
    (
        r"J:\net_novels\crawler_ocr\tokyokanjubaosha",
        {
            "start_page": "https://www.dingdianks.com/xs/19778/",
            "text_file": "东京：开局薄纱雌小鬼.txt",
        },
    ),
)

if __name__ == "__main__":
    print("enter")
    mycrawler = Crawler(configs[0][0], configs[0][1])
    print("Successfully created engine and logged in")
    mycrawler.crawl(sleep=10)
    print("Crawler completed!")
