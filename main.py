from playwright.async_api import async_playwright
import asyncio
import time
import json
import os
import sys

from chapter_crawler import ChapterCrawler

# Windows 平台设置
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


async def get_chapters_async(url, max_retries=3, timeout=60000):
    crawler = None
    try:
        crawler = ChapterCrawler()
        retry_count = 0

        while retry_count < max_retries:
            try:
                await crawler.start()
                chapters = await crawler.get_chapters(url, timeout=timeout)
                return chapters
            except Exception as e:
                retry_count += 1
                print(f"第 {retry_count} 次尝试失败: {str(e)}")
                if retry_count < max_retries:
                    print(f"等待 5 秒后重试...")
                    await asyncio.sleep(5)
            finally:
                if crawler:
                    await crawler.close()

        print("达到最大重试次数，获取章节失败")
        return None
    except Exception as e:
        print(f"获取章节过程中发生错误: {str(e)}")
        return None


async def get_book_info(book_name):
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            page.set_default_timeout(60000)

            search_url = f"https://www.pilishuwu.com/search/0/{book_name}/1.html"
            print(f"正在获取书籍信息: {search_url}")

            try:
                await page.goto(search_url, wait_until='networkidle')
                await asyncio.sleep(2)
            except Exception as e:
                print(f"访问页面时发生错误: {str(e)}")
                return None

            book_elements = await page.query_selector_all('.mod_book_list li')
            print(f"\n找到 {len(book_elements)} 本书")

            books = []
            for book in book_elements:
                try:
                    book_info = {}

                    # 获取书籍链接和标题
                    link = await book.query_selector('a.mod_book_cover')
                    if link:
                        href = await link.get_attribute('href')
                        book_info['url'] = f"https://www.pilishuwu.com{href}"
                        book_info['id'] = href.split('/')[2]
                        book_info['title'] = await link.get_attribute('title')

                    # 获取封面图片
                    img = await book.query_selector('img.img100x133')
                    if img:
                        book_info['cover'] = f"https://www.pilishuwu.com{await img.get_attribute('src')}"

                    # 获取最新章节
                    update_elem = await book.query_selector('.mod_book_update')
                    if update_elem:
                        book_info['latest_chapter'] = await update_elem.text_content()

                    # 获取书名
                    name_elem = await book.query_selector('.mod_book_name a')
                    if name_elem:
                        book_info['name'] = await name_elem.text_content()

                    # 获取状态
                    status_elem = await book.query_selector('.novel_process2')
                    if status_elem:
                        book_info['status'] = await status_elem.text_content()

                    # 获取章节信息（带重试机制）
                    if book_info.get('id'):
                        url = book_info['url']
                        menu_url = url.replace('/info.html', '/menu/1.html')
                        print(menu_url)
                        chapters = await get_chapters_async(menu_url)
                        if chapters:
                            book_info['chapters'] = chapters

                    books.append(book_info)

                    # 打印书籍信息
                    print("\n=== 书籍信息 ===")
                    print(f"ID: {book_info.get('id', 'N/A')}")
                    print(f"书名: {book_info.get('name', 'N/A')}")
                    print(f"标题: {book_info.get('title', 'N/A')}")
                    print(f"状态: {book_info.get('status', 'N/A')}")
                    print(f"最新章节: {book_info.get('latest_chapter', 'N/A')}")
                    print(f"封面链接: {book_info.get('cover', 'N/A')}")
                    print(f"书籍链接: {book_info.get('url', 'N/A')}")
                    if 'chapters' in book_info:
                        print(f"章节数量: {len(book_info['chapters'])}")
                    print("==============")

                except Exception as e:
                    print(f"处理书籍时发生错误: {str(e)}")
                    continue

            return books

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
    finally:
        if browser:
            await browser.close()


async def main_async(book_name):
    try:
        books = await get_book_info(book_name)

        if books:
            print(f"\n总共获取到 {len(books)} 本书的信息")

            # 保存到文件
            for book in books:
                filename = f'book_{book["id"]}_info.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(book, f, ensure_ascii=False, indent=2)
                print(f"书籍信息已保存到 {filename}")
        else:
            print("未找到任何书籍信息")

        return books  # 返回获取到的图书信息
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")
        return None


def main(book_name):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        books = loop.run_until_complete(main_async(book_name))
        return books  # 返回获取到的图书信息
    except Exception as e:
        print(f"程序执行失败: {str(e)}")
        return None
    finally:
        loop.close()


if __name__ == "__main__":
    try:
        book_name = input("请输入要搜索的书名: ")
        main(book_name)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行失败: {str(e)}")