# novel_ui.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                             QScrollArea, QLabel, QFrame, QStackedWidget,
                             QMessageBox, QProgressBar, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage, QFont
import requests
from PIL import Image
from io import BytesIO
import json
from pathlib import Path

# 导入你的爬虫和阅读器
from main import main as crawler_main
from read import ChapterReader
from bookshelf import BookshelfManager


class ContentThread(QThread):
    """章节内容获取线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, url, force_refresh=False):
        super().__init__()
        self.url = url
        self.force_refresh = force_refresh
        self.reader = ChapterReader()

    def run(self):
        try:
            self.progress.emit("正在获取章节内容...")
            content = self.reader.get_chapter_content(self.url, self.force_refresh)
            if content:
                self.finished.emit(content)
            else:
                self.error.emit("获取章节内容失败")
        except Exception as e:
            self.error.emit(str(e))


class SearchThread(QThread):
    """搜索线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword

    def run(self):
        try:
            self.progress.emit("正在搜索...")
            results = crawler_main(self.keyword)
            if results:
                self.finished.emit(results)
            else:
                self.error.emit("未找到相关书籍")
        except Exception as e:
            self.error.emit(str(e))


class NovelUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_book = None
        self.current_chapter_index = 0
        self.reader = ChapterReader()
        self.bookshelf = BookshelfManager()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("轻小说阅读器")
        self.setGeometry(100, 100, 450, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QWidget {
                font-family: "Microsoft YaHei", sans-serif;
            }
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3c55a5;
            }
            QPushButton:pressed {
                background-color: #2c3e8c;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #dcdde1;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a69bd;
            }
            QTextEdit {
                border: none;
                background-color: white;
                padding: 10px;
                font-size: 14px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QLabel {
                color: #2f3542;
            }
        """)

        # 创建堆叠窗口部件
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 创建工具栏
        self.create_toolbar()

        # 创建各个页面
        self.create_search_page()
        self.create_bookshelf_page()
        self.create_reader_page()

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("导航")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #4a69bd;
                spacing: 5px;
                padding: 5px;
            }
            QToolBar QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 4px;
                min-width: 80px;
                padding: 5px 10px;
            }
            QToolBar QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)

        # 搜索按钮
        search_action = QPushButton("搜索")
        search_action.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        toolbar.addWidget(search_action)

        # 书架按钮
        bookshelf_action = QPushButton("书架")
        bookshelf_action.clicked.connect(self.show_bookshelf)
        toolbar.addWidget(bookshelf_action)

    def create_bookshelf_page(self):
        """创建书架页面"""
        bookshelf_page = QWidget()
        layout = QVBoxLayout(bookshelf_page)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QLabel("我的书架")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2f3542;
            padding: 10px;
            background-color: white;
            border-radius: 4px;
        """)
        layout.addWidget(title)

        # 书架内容
        self.bookshelf_scroll = QScrollArea()
        self.bookshelf_scroll.setWidgetResizable(True)
        self.bookshelf_content = QWidget()
        self.bookshelf_layout = QVBoxLayout(self.bookshelf_content)
        self.bookshelf_layout.setSpacing(10)
        self.bookshelf_scroll.setWidget(self.bookshelf_content)
        layout.addWidget(self.bookshelf_scroll)

        self.stacked_widget.addWidget(bookshelf_page)

    # 在 NovelUI 类中修改以下方法

    def show_bookshelf(self):
        """显示书架"""
        # 刷新书架数据
        self.bookshelf.refresh()

        # 清空当前书架显示
        while self.bookshelf_layout.count():
            item = self.bookshelf_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取所有书籍并显示
        books = self.bookshelf.get_all_books()
        if not books:
            # 显示空书架提示
            empty_label = QLabel("书架空空如也，快去搜索添加书籍吧！")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #a4b0be;
                    font-size: 16px;
                    padding: 20px;
                    background-color: white;
                    border-radius: 4px;
                }
            """)
            self.bookshelf_layout.addWidget(empty_label)
        else:
            # 按添加时间排序（如果有）
            books.sort(key=lambda x: x.get('name', ''))
            for book in books:
                book_card = self.create_book_card(book)
                self.bookshelf_layout.addWidget(book_card)

        self.stacked_widget.setCurrentIndex(1)  # 切换到书架页面

    def create_book_card(self, book: dict) -> QFrame:
        """创建书籍卡片"""
        card = QFrame()
        layout = QHBoxLayout(card)

        # 书籍信息区域
        info_layout = QVBoxLayout()

        # 书名
        title = QLabel(book.get('name', '未知'))
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2f3542;
        """)
        info_layout.addWidget(title)

        # 状态和章节信息
        status_text = [
            f"状态：{book.get('status', '未知')}",
            f"章节数：{len(book.get('chapters', []))}"
        ]
        status = QLabel('\n'.join(status_text))
        status.setStyleSheet("""
            color: #747d8c;
            font-size: 14px;
        """)
        info_layout.addWidget(status)

        layout.addLayout(info_layout)

        # 按钮区域
        button_layout = QVBoxLayout()

        # 阅读按钮
        read_btn = QPushButton("开始阅读")
        read_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3c55a5;
            }
        """)
        read_btn.clicked.connect(lambda: self.start_reading(book))
        button_layout.addWidget(read_btn)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e84118;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c23616;
            }
        """)
        delete_btn.clicked.connect(lambda: self.remove_from_bookshelf(book))
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # 卡片样式
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            QFrame:hover {
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
        """)

        return card

    def add_to_bookshelf(self, book: dict):
        """添加到书架"""
        if self.bookshelf.add_book(book):
            QMessageBox.information(self, "提示", "已添加到书架")
            self.show_bookshelf()
        else:
            QMessageBox.warning(self, "错误", "添加到书架失败")

    def remove_from_bookshelf(self, book: dict):
        """从书架删除"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除《{book.get('name', '未知')}》吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.bookshelf.remove_book(book['id']):
                QMessageBox.information(self, "提示", "删除成功")
                self.show_bookshelf()
            else:
                QMessageBox.warning(self, "错误", "删除失败")

    def start_reading(self, book: dict):
        """开始阅读"""
        self.current_book = book

        # 获取阅读进度
        progress = self.bookshelf.get_reading_progress(book['id'])
        if progress:
            self.current_chapter_index = progress['last_read_chapter']
        else:
            self.current_chapter_index = 0

        # 加载章节
        if book.get('chapters'):
            self.load_chapter(book['chapters'][self.current_chapter_index])
            self.stacked_widget.setCurrentIndex(2)  # 切换到阅读页面

    def create_search_page(self):
        search_page = QWidget()
        layout = QVBoxLayout(search_page)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 搜索区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入书名搜索")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #dcdde1;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a69bd;
            }
        """)

        self.search_button = QPushButton("搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3c55a5;
            }
        """)
        self.search_button.clicked.connect(self.search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #dcdde1;
                height: 4px;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4a69bd;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 搜索结果区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        self.stacked_widget.addWidget(search_page)

    # 在 NovelUI 类中添加以下代码

    def create_reader_page(self):
        reader_page = QWidget()
        layout = QVBoxLayout(reader_page)

        # 章节标题
        self.chapter_title = QLabel()
        self.chapter_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        """)
        layout.addWidget(self.chapter_title)

        # 章节内容
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.setStyleSheet("""
            QTextEdit {
                padding: 20px;
                font-family: "思源宋体", "Source Han Serif", serif;
                font-size: 24px;
                line-height: 3;
                background-color: #fafafa;
                border: none;
                text-indent: 4em;
            }
        """)
        layout.addWidget(self.content_view)

        # 底部导航按钮
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一章")
        self.next_btn = QPushButton("下一章")
        self.menu_btn = QPushButton("目录")
        self.return_btn = QPushButton("返回")

        for btn in [self.prev_btn, self.next_btn, self.menu_btn, self.return_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 50px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:disabled {
                    background-color: #BDBDBD;
                }
            """)

        self.prev_btn.clicked.connect(self.prev_chapter)
        self.next_btn.clicked.connect(self.next_chapter)
        self.menu_btn.clicked.connect(self.show_chapter_menu)
        self.return_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        # 添加按钮到导航布局，并设置间距
        nav_layout.addStretch()  # 左侧弹性空间
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addSpacing(10)  # 按钮之间的间距
        nav_layout.addWidget(self.next_btn)
        nav_layout.addSpacing(20)  # 导航按钮和功能按钮之间的间距
        nav_layout.addWidget(self.menu_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.return_btn)
        nav_layout.addStretch()  # 右侧弹性空间

        # 底部导航区域
        nav_widget = QWidget()
        nav_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #e0e0e0;
                padding: 10px;
            }
        """)
        nav_widget.setLayout(nav_layout)
        layout.addWidget(nav_widget)

        self.stacked_widget.addWidget(reader_page)

    def show_chapter_menu(self):
        """显示章节目录对话框"""
        if not self.current_book or not self.current_book.get('chapters'):
            return

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("章节目录")
        dialog.setMinimumWidth(300)
        dialog.setMaximumHeight(600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f6fa;
            }
        """)

        # 创建布局
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # 创建容器窗口部件
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(5)

        # 添加章节按钮
        chapters = self.current_book['chapters']
        for i, chapter in enumerate(chapters):
            btn = QPushButton(chapter['title'])
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    border: none;
                    background: white;
                    border-radius: 4px;
                    color: #2f3542;
                }
                QPushButton:hover {
                    background: #f1f2f6;
                }
            """)

            # 标记当前章节
            if i == self.current_chapter_index:
                btn.setStyleSheet(btn.styleSheet() + """
                    QPushButton {
                        background: #4a69bd;
                        color: white;
                        font-weight: bold;
                    }
                """)

            # 绑定点击事件
            btn.clicked.connect(lambda checked, index=i: self.jump_to_chapter(index, dialog))
            container_layout.addWidget(btn)

        # 设置滚动区域的内容
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # 显示对话框
        dialog.exec_()

    def jump_to_chapter(self, index: int, dialog: QDialog = None):
        """跳转到指定章节"""
        if 0 <= index < len(self.current_book['chapters']):
            self.current_chapter_index = index
            self.load_chapter(self.current_book['chapters'][index])
            if dialog:
                dialog.close()

    def search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入搜索关键词")
            return

        # 显示进度条
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.search_button.setEnabled(False)

        # 开始搜索
        self.search_thread = SearchThread(keyword)
        self.search_thread.finished.connect(self.handle_search_results)
        self.search_thread.error.connect(self.handle_error)
        self.search_thread.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.search_thread.start()

    def handle_search_results(self, books):
        try:
            print(f"开始处理搜索结果，共 {len(books)} 本书")
            
            self.progress_bar.hide()
            self.search_button.setEnabled(True)
            
            # 清空之前的结果
            while self.scroll_layout.count():
                item = self.scroll_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 设置滚动区域的背景色
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    background-color: white;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                   background-color: white;
                }
            """)

            # 显示新的结果
            for book in books:
                # 创建卡片容器
                book_card = QFrame()
                card_layout = QVBoxLayout(book_card)
                card_layout.setSpacing(8)  # 减小内部间距
                card_layout.setContentsMargins(10, 10, 10, 10)  # 减小边距
                card_layout.setAlignment(Qt.AlignCenter)

                # 封面图片
                cover_label = QLabel()
                cover_label.setFixedSize(160, 220)  # 稍微缩小封面尺寸
                cover_label.setStyleSheet("""
                    QLabel {
                        background-color: #ffffff;
                        border-radius: 4px;
                    }
                """)
                cover_label.setAlignment(Qt.AlignCenter)

                # 从book_id_info.json中获取封面URL
                if 'cover' in book:
                    self.load_cover_image(cover_label, book['cover'])
                else:
                    cover_label.setText("暂无封面")

                card_layout.addWidget(cover_label, alignment=Qt.AlignCenter)

                # 书籍标题
                title = QLabel(book.get('name', '未知'))
                title.setStyleSheet("""
                    QLabel {
                        font-size: 18px;
                        font-weight: bold;
                        color: #333333;
                        padding: 5px;
                    }
                """)
                title.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(title)

                # 信息容器
                info_container = QWidget()
                info_layout = QVBoxLayout(info_container)
                info_layout.setSpacing(5)

                # 状态
                status = QLabel(f"状态：{book.get('status', '未知')}")
                status.setStyleSheet("color: #666666; font-size: 14px;")
                status.setAlignment(Qt.AlignCenter)
                info_layout.addWidget(status)

                # 章节数
                if 'chapters' in book:
                    chapter_count = QLabel(f"共 {len(book['chapters'])} 章")
                    chapter_count.setStyleSheet("color: #666666; font-size: 14px;")
                    chapter_count.setAlignment(Qt.AlignCenter)
                    info_layout.addWidget(chapter_count)

                card_layout.addWidget(info_container)

                # 阅读按钮
                read_btn = QPushButton("开始阅读")
                read_btn.setFixedSize(120, 40)
                read_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a69bd;
                        color: white;
                        border: none;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #3c55a5;
                    }
                """)
                read_btn.clicked.connect(lambda _, b=book: self.start_reading(b))
                card_layout.addWidget(read_btn, alignment=Qt.AlignCenter)

                # 设置卡片样式
                book_card.setStyleSheet("""
                    QFrame {
                        background-color: #ffffff;
                        border-radius: 8px;
                        padding: 10px;
                        margin: 5px;
                        border: 1px solid #e0e0e0;
                    }
                """)

                # 添加到主布局
                self.scroll_layout.addWidget(book_card, alignment=Qt.AlignCenter)

        except Exception as e:
            print(f"处理搜索结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_cover_image(self, label: QLabel, url: str):
        """异步加载封面图片"""
        class ImageWorker(QObject):
            finished = pyqtSignal(QPixmap)
            error = pyqtSignal(str)

            def __init__(self, url):
                super().__init__()
                self.url = url

            def run(self):
                try:
                    response = requests.get(self.url)
                    image = QImage()
                    image.loadFromData(response.content)
                    scaled_image = image.scaled(200, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pixmap = QPixmap.fromImage(scaled_image)
                    self.finished.emit(pixmap)
                except Exception as e:
                    self.error.emit(str(e))

        def on_image_loaded(pixmap):
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            # 清理线程和worker
            thread.quit()
            thread.wait()
            worker.deleteLater()
            thread.deleteLater()

        def on_error(error_msg):
            label.setText("加载失败")
            label.setAlignment(Qt.AlignCenter)
            print(f"加载封面图片失败: {error_msg}")
            # 清理线程和worker
            thread.quit()
            thread.wait()
            worker.deleteLater()
            thread.deleteLater()

        # 创建线程和worker
        thread = QThread()
        worker = ImageWorker(url)
        worker.moveToThread(thread)
        
        # 连接信号
        worker.finished.connect(on_image_loaded)
        worker.error.connect(on_error)
        thread.started.connect(worker.run)
        
        # 保持worker的引用（防止被垃圾回收）
        label.thread = thread
        label.worker = worker
        
        # 启动线程
        thread.start()

    def start_reading(self, book: dict):
        """开始阅读书籍"""
        try:
            self.current_book = book
            self.current_chapter_index = 0

            if not book.get('chapters'):
                QMessageBox.warning(self, "错误", "未找到章节信息")
                return

            # 尝试加载第一章
            chapter = book['chapters'][self.current_chapter_index]
            print(f"正在加载章节: {chapter['title']}")  # 调试信息

            self.load_chapter(chapter)
            self.stacked_widget.setCurrentIndex(2)  # 切换到阅读页面

        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载书籍失败: {str(e)}")

    def load_chapter(self, chapter):
        """加载章节内容"""
        try:
            # 清空当前内容并显示加载提示
            self.content_view.clear()
            self.content_view.setPlainText("正在加载章节内容...")

            # 更新章节标题
            self.chapter_title.setText(f"正在阅读：{chapter['title']}")
            print(f"加载章节URL: {chapter['url']}")  # 调试信息

            # 异步加载章节内容
            self.content_thread = ContentThread(chapter['url'])
            self.content_thread.finished.connect(self.show_chapter_content)
            self.content_thread.error.connect(self.handle_error)
            self.content_thread.start()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载章节失败: {str(e)}")

    def show_chapter_content(self, content):
        """显示章节内容"""
        if not content:
            self.content_view.setPlainText("加载章节内容失败")
            return

        # 处理段落缩进
        paragraphs = content.split('\n')
        indented_content = '\n'.join(['　　' + p.strip() for p in paragraphs if p.strip()])

        # 设置章节内容
        self.content_view.setPlainText(indented_content)

        # 更新上一章/下一章按钮状态
        self.prev_btn.setEnabled(self.current_chapter_index > 0)
        self.next_btn.setEnabled(
            self.current_chapter_index < len(self.current_book['chapters']) - 1
        )

    def prev_chapter(self):
        """上一章"""
        if self.current_chapter_index > 0:
            self.current_chapter_index -= 1
            self.load_chapter(self.current_book['chapters'][self.current_chapter_index])

    def next_chapter(self):
        """下一章"""
        if self.current_chapter_index < len(self.current_book['chapters']) - 1:
            self.current_chapter_index += 1
            self.load_chapter(self.current_book['chapters'][self.current_chapter_index])

    def handle_error(self, error_msg):
        """错误处理"""
        self.progress_bar.hide()
        self.search_button.setEnabled(True)
        QMessageBox.warning(self, "错误", str(error_msg))

class ContentThread(QThread):
    """章节内容获取线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.reader = ChapterReader()  # 使用你之前的 ChapterReader 类

    def run(self):
        try:
            content = self.reader.get_chapter_content(self.url)
            if content:
                self.finished.emit(content)
            else:
                self.error.emit("获取章节内容失败")
        except Exception as e:
            self.error.emit(str(e))

def main():
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")

    window = NovelUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()