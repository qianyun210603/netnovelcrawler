class CountStopper:
    def __init__(self, maxcount=10000):
        self.count = 0
        self.maxcount = maxcount

    def __call__(self, chapter_info):
        self.count += 1
        return self.count > self.maxcount


class VipStopper:

    def __call__(self, chapter_info):
        return chapter_info["vip"]


class AfterChapterStarter:
    def __init__(self, start_chapter):
        self.start_chapter = start_chapter
        self.seen = False

    def __call__(self, chapter_info):
        if self.start_chapter in chapter_info["title"] or chapter_info["title"] in self.start_chapter:
            self.seen = True
        return self.seen
