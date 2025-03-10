"""
新闻列表面板

显示新闻列表，并处理新闻项选择事件。
"""

import logging
from datetime import datetime
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                            QListWidgetItem, QLabel, QTextBrowser, 
                            QSplitter, QHBoxLayout, QPushButton, QCheckBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class NewsItem(QListWidgetItem):
    """自定义新闻列表项类"""
    
    def __init__(self, news_data):
        """初始化新闻列表项
        
        Args:
            news_data: 新闻数据字典
        """
        super().__init__()
        self.news_data = news_data
        
        # 设置显示文本
        title = news_data.get('title', '无标题')
        source = news_data.get('source_name', '未知来源')
        date = news_data.get('pub_date', '')
        
        display_text = f"{title}\n[{source}] {date}"
        self.setText(display_text)
        
        # 设置字体
        font = QFont()
        font.setBold(True)
        self.setFont(font)


class NewsListPanel(QWidget):
    """新闻列表面板组件"""
    
    # 自定义信号：选择新闻项
    item_selected = pyqtSignal(dict)
    
    # 新增信号：新闻列表已更新
    news_updated = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger('news_analyzer.ui.news_list')
        self.current_news = []
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 标题标签
        title_label = QLabel("新闻列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 控制面板
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 5, 0, 5)

        # 添加排序按钮
        self.sort_button = QPushButton("按日期排序")
        self.sort_button.setFixedWidth(120)
        self.sort_button.setStyleSheet("""
            QPushButton {
                background-color: #ECEFF1;
                border: 1px solid #CFD8DC;
                border-radius: 4px;
                padding: 4px 8px;
                color: #455A64;
            }
            QPushButton:hover {
                background-color: #CFD8DC;
            }
        """)
        self.sort_button.clicked.connect(self._sort_by_date)
        control_layout.addWidget(self.sort_button)

        # 添加一个复选框，决定升序还是降序
        self.sort_order = QCheckBox("降序排列")
        self.sort_order.setChecked(True)  # 默认降序（最新的在前面）
        control_layout.addWidget(self.sort_order)

        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # 新闻列表
        self.news_list = QListWidget()
        self.news_list.setAlternatingRowColors(True)
        self.news_list.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self.news_list)
        
        # 新闻预览
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        splitter.addWidget(self.preview)
        
        # 设置分割器比例
        splitter.setSizes([400, 200])  # 列表:预览 高度比例
        
        # 状态标签
        self.status_label = QLabel("加载新闻...")
        layout.addWidget(self.status_label)
    
    def update_news(self, news_items):
        """更新新闻列表
        
        Args:
            news_items: 新闻条目列表
        """
        # 清空当前列表
        self.news_list.clear()
        
        # 保存新闻数据
        self.current_news = news_items
        
        # 添加新闻项到列表
        for news in news_items:
            item = NewsItem(news)
            self.news_list.addItem(item)
        
        # 更新状态标签
        count = len(news_items)
        self.status_label.setText(f"共 {count} 条新闻")
        
        # 清空预览
        self.preview.setHtml("")
        
        # 发送更新信号
        self.news_updated.emit(news_items)
        
        self.logger.debug(f"更新了新闻列表，共 {count} 条")

    def _parse_date(self, date_str):
        """
        解析多种格式的日期字符串为datetime对象，确保所有返回的对象都是不带时区信息的
        
        Args:
            date_str: 日期字符串
            
        Returns:
            datetime: 解析后的datetime对象（不带时区信息），如果解析失败返回datetime.min
        """
        if not date_str:
            return datetime.min
        
        # 常见的日期格式列表
        date_formats = [
            # RFC 822 格式 (常见于RSS Feed)
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S",
            # ISO 格式
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            # 常见日期格式
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d %b %Y %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d"
        ]
        
        # 尝试每一种格式
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # 移除时区信息，确保返回不带时区的datetime
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except ValueError:
                continue
        
        # 如果标准格式都失败，尝试使用正则表达式提取日期
        try:
            # 查找类似 YYYY-MM-DD 或 YYYY/MM/DD 的模式
            date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
            if date_match:
                year, month, day = map(int, date_match.groups())
                return datetime(year, month, day)
            
            # 尝试提取英文月份格式，如 "25 Dec 2023"
            month_names = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            
            month_pattern = r'(\d{1,2})\s+([a-zA-Z]{3})\s+(\d{4})'
            date_match = re.search(month_pattern, date_str, re.IGNORECASE)
            if date_match:
                day, month_str, year = date_match.groups()
                month = month_names.get(month_str.lower()[:3], 1)
                return datetime(int(year), month, int(day))
        except:
            pass
        
        # 所有方法都失败，返回最小日期
        return datetime.min
    
    def _sort_by_date(self):
        """按日期排序新闻列表，使用增强的日期解析算法"""
        if not self.current_news:
            return
            
        # 复制一份新闻列表，避免直接修改原始数据
        sorted_news = self.current_news.copy()
        
        # 按发布日期排序
        try:
            # 检查是否需要降序（最新的在前面）
            reverse_order = self.sort_order.isChecked()
            
            # 定义排序键函数，解析日期
            def get_date(news_item):
                date_str = news_item.get('pub_date', '')
                return self._parse_date(date_str)
            
            # 使用增强的日期解析进行排序
            sorted_news.sort(key=get_date, reverse=reverse_order)
            
            # 更新显示
            self.update_news(sorted_news)
            
            # 更新状态
            order_text = "降序" if reverse_order else "升序"
            self.status_label.setText(f"已按日期{order_text}排列 {len(sorted_news)} 条新闻")
            self.logger.debug(f"新闻列表已按日期{order_text}排序")
        
        except Exception as e:
            self.status_label.setText(f"排序失败: {str(e)}")
            self.logger.error(f"新闻排序失败: {str(e)}")
    
    def _on_item_clicked(self, item):
        """处理列表项点击事件
        
        Args:
            item: 被点击的列表项
        """
        # 获取新闻数据
        news_data = item.news_data
        
        # 更新预览
        self._update_preview(news_data)
        
        # 发送信号
        self.item_selected.emit(news_data)
        
        self.logger.debug(f"选择了新闻: {news_data.get('title', '')[:30]}...")
    
    def _update_preview(self, news_data):
        """更新新闻预览
        
        Args:
            news_data: 新闻数据字典
        """
        title = news_data.get('title', '无标题')
        source = news_data.get('source_name', '未知来源')
        date = news_data.get('pub_date', '未知日期')
        description = news_data.get('description', '无内容')
        link = news_data.get('link', '')
        
        # 创建HTML内容
        html = f"""
        <h2>{title}</h2>
        <p><strong>来源:</strong> {source} | <strong>日期:</strong> {date}</p>
        <hr>
        <p>{description}</p>
        """
        
        if link:
            html += f'<p><a href="{link}" target="_blank">阅读原文</a></p>'
        
        # 设置HTML内容
        self.preview.setHtml(html)