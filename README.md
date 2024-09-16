## 爬取小说网站并生成TXT

目前支持
- 欢乐书客/刺猬猫
- sf轻小说

用法：

```python
config = (
    r'D:\net_novels\crawler_ocr\lord',
    {
        'start_page': 'https://ccc.xxxx.com/Novel/xxxxxx/',
        'login_info': ('test_login', 'test_pwd'),
        'image_folder': 'vip_images',
        'image_process': 'ocr',
        'text_file': 'xxx.txt',
    }
)
from netnovelcrawler import Crawler
from netnovelcrawler.utils.starter_stopper import AfterChapterStarter, CountStopper

mycrawler = Crawler(*config)
mycrawler.crawl(starter=AfterChapterStarter("10. 某章节"), stopper=CountStopper(50))
```

#### 绕过滑块验证反爬虫机制

######修改chromedriver.exe
- 文本编辑器打开chromedriver.exe
- 找到`cdc_`字符串
- 等长替换$cdc_lasutopfhvcZLmcfl
- 保存

