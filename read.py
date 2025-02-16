# read.py
from playwright.sync_api import sync_playwright
import time
import logging
from typing import Optional, List
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChapterReader:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        """获取缓存文件路径"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def _load_from_cache(self, url: str) -> Optional[str]:
        """从缓存加载章节内容"""
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
                if time.time() - cache_data['timestamp'] < 86400:  # 24小时缓存
                    return cache_data['content']
            except Exception as e:
                logger.error(f"读取缓存失败: {str(e)}")
        return None

    def _save_to_cache(self, url: str, content: str) -> None:
        """保存内容到缓存"""
        try:
            cache_path = self._get_cache_path(url)
            cache_data = {
                'url': url,
                'content': content,
                'timestamp': time.time()
            }
            cache_path.write_text(json.dumps(cache_data, ensure_ascii=False), encoding='utf-8')
        except Exception as e:
            logger.error(f"保存缓存失败: {str(e)}")

    def get_chapter_content(self, url: str, force_refresh: bool = False) -> Optional[str]:
        """获取章节内容"""
        if not force_refresh:
            cached_content = self._load_from_cache(url)
            if cached_content:
                logger.info(f"从缓存加载章节内容: {url}")
                return cached_content

        logger.info(f"开始获取章节内容: {url}")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
                )
                context = browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                page.set_default_timeout(30000)  # 30秒超时

                # 访问页面
                page.goto(url, wait_until='networkidle')
                time.sleep(2)  # 等待内容加载

                # 获取正文内容
                content = page.evaluate('''() => {
                    const content = document.querySelector('.read-content');
                    if (!content) return null;

                    const paragraphs = Array.from(content.querySelectorAll('p'));
                    return paragraphs
                        .map(p => p.textContent.trim())
                        .filter(text => text.length > 0)
                        .join('\\n\\n');
                }''')

                if not content:
                    logger.error("未找到章节内容")
                    return None

                # 保存到缓存
                self._save_to_cache(url, content)

                return content

            except Exception as e:
                logger.error(f"获取章节内容时发生错误: {str(e)}")
                return None

            finally:
                try:
                    if 'browser' in locals():
                        browser.close()
                except Exception as e:
                    logger.error(f"关闭浏览器时发生错误: {str(e)}")

    def get_multiple_chapters(self, urls: List[str], force_refresh: bool = False) -> List[Optional[str]]:
        """批量获取多个章节的内容"""
        return [self.get_chapter_content(url, force_refresh) for url in urls]


def main():
    """测试章节阅读功能"""
    reader = ChapterReader()

    # 测试章节URL
    test_url = "https://www.pilishuwu.com/1/4545/read/1699599.html"

    # 获取章节内容
    content = reader.get_chapter_content(test_url)

    if content:
        # 保存到文件
        output_file = Path('output') / 'chapter_content.txt'
        output_file.parent.mkdir(exist_ok=True)

        with output_file.open('w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"内容已保存到 {output_file}")
    else:
        logger.error("获取章节内容失败")


if __name__ == "__main__":
    main()