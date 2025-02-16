# bookshelf.py
import json
from pathlib import Path
import time
from typing import Dict, List, Optional
import logging
import glob


class BookshelfManager:
    def __init__(self):
        self.books: Dict = self._load_bookshelf()

    def _load_bookshelf(self) -> Dict:
        """从本地文件加载书架数据"""
        books = {}
        try:
            # 查找所有 book_*_info.json 文件
            book_files = glob.glob('book_*_info.json')
            for file_path in book_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        book_data = json.load(f)
                        if book_data and 'id' in book_data:
                            books[book_data['id']] = book_data
                except Exception as e:
                    logging.error(f"读取文件 {file_path} 失败: {str(e)}")

            logging.info(f"成功加载 {len(books)} 本书")
            return books
        except Exception as e:
            logging.error(f"加载书架失败: {str(e)}")
            return {}

    def add_book(self, book: Dict) -> bool:
        """添加书籍到本地"""
        try:
            if not book or 'id' not in book:
                return False

            # 保存到本地文件
            filename = f'book_{book["id"]}_info.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(book, f, ensure_ascii=False, indent=2)

            # 更新内存中的数据
            self.books[book['id']] = book
            return True
        except Exception as e:
            logging.error(f"添加书籍失败: {str(e)}")
            return False

    def remove_book(self, book_id: str) -> bool:
        """从本地删除书籍"""
        try:
            filename = f'book_{book_id}_info.json'
            file_path = Path(filename)
            if file_path.exists():
                file_path.unlink()  # 删除文件

            if book_id in self.books:
                del self.books[book_id]
            return True
        except Exception as e:
            logging.error(f"删除书籍失败: {str(e)}")
            return False

    def get_book(self, book_id: str) -> Optional[Dict]:
        """获取书籍信息"""
        return self.books.get(book_id)

    def get_all_books(self) -> List[Dict]:
        """获取所有书籍"""
        return list(self.books.values())

    def refresh(self):
        """刷新书架数据"""
        self.books = self._load_bookshelf()