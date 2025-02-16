# chapter_crawler.py
from playwright.async_api import async_playwright
import asyncio


class ChapterCrawler:
    def __init__(self):
        self.base_url = "https://www.pilishuwu.com"
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(user_agent=self.user_agent)
            self.page = await self.context.new_page()
        except Exception as e:
            print(f"启动浏览器时发生错误: {str(e)}")
            await self.close()
            raise

    async def close(self):
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"关闭浏览器时发生错误: {str(e)}")

    async def get_chapters(self, url, timeout=60000):
        """
        获取章节列表
        :param url: 完整的目录页面URL
        :param timeout: 超时时间（毫秒）
        :return: 章节列表
        """
        print(f"获取章节目录: {url}")

        try:
            self.page.set_default_timeout(timeout)
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)

            # 查找全部章节链接
            chapter_links = await self.page.query_selector_all('.works-chapter-item a')

            chapters = []
            for link in chapter_links:
                chapter = {
                    'title': await link.text_content(),
                    'url': f"{self.base_url}{await link.get_attribute('href')}"
                }
                chapters.append(chapter)
                print(f"标题: {chapter['title']}")
                print(f"链接: {chapter['url']}")
                print("-------------------")

            print(f"\n总共获取到 {len(chapters)} 个章节")
            return chapters

        except Exception as e:
            print(f"获取章节时发生错误: {str(e)}")
            return None

    async def get_content(self, url, timeout=60000):
        """
        获取章节内容
        :param url: 完整的章节页面URL
        :param timeout: 超时时间（毫秒）
        :return: 章节内容
        """
        print(f"获取章节内容: {url}")

        try:
            self.page.set_default_timeout(timeout)
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)

            # 获取章节内容
            content = await self.page.evaluate('''() => {
                const content = document.querySelector('.read-content');
                if (!content) return null;

                const paragraphs = Array.from(content.querySelectorAll('p'));
                return paragraphs
                    .map(p => p.textContent.trim())
                    .filter(text => text.length > 0)
                    .join('\\n\\n');
            }''')

            if not content:
                print("未找到章节内容")
                return None

            return content

        except Exception as e:
            print(f"获取章节内容时发生错误: {str(e)}")
            return None


# 测试代码
async def main_test():
    crawler = ChapterCrawler()
    try:
        await crawler.start()

        # 测试获取章节列表
        chapters_url = "https://www.pilishuwu.com/1/4545/menu/1.html"
        chapters = await crawler.get_chapters(chapters_url)

        if chapters and len(chapters) > 0:
            # 测试获取第一章内容
            first_chapter_url = chapters[0]['url']
            content = await crawler.get_content(first_chapter_url)
            if content:
                print("\n=== 第一章内容预览 ===")
                print(content[:200] + "...")
            else:
                print("获取章节内容失败")
        else:
            print("获取章节列表失败")

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main_test())