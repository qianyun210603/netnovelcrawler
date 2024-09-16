from netnovelcrawler import Crawler

configs = (
    (
        r"J:\net_novels\crawler_ocr\zhenjingwangfeifanpai",
        {
            "start_page": "https://m.yeduku.net/84957/",
            "text_file": "震惊，我的王妃怎么可能是反派.txt",
        },
    ),
)

if __name__ == "__main__":
    print("enter")
    mycrawler = Crawler(configs[0][0], configs[0][1])
    print("Successfully created engine and logged in")
    mycrawler.crawl(sleep=10)
    print("Crawler completed!")
