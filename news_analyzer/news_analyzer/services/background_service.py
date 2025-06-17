"""
后台服务模块 - 使用QThread实现异步任务
"""

import logging
from PyQt5.QtCore import QThread, pyqtSignal


class BackgroundService(QThread):
    """后台服务基类"""
    
    progress_signal = pyqtSignal(int, str)  # 进度百分比, 状态消息
    finished_signal = pyqtSignal(object)    # 任务结果
    error_signal = pyqtSignal(str)          # 错误消息
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('news_analyzer.services.background')
        self._is_running = False
    
    def run(self):
        """线程主循环"""
        self._is_running = True
        try:
            self.progress_signal.emit(0, "任务开始")
            result = self.execute()
            self.finished_signal.emit(result)
            self.progress_signal.emit(100, "任务完成")
        except Exception as e:
            self.logger.error(f"后台任务执行失败: {str(e)}")
            self.error_signal.emit(str(e))
        finally:
            self._is_running = False
    
    def execute(self):
        """子类需要实现的具体任务逻辑"""
        raise NotImplementedError("子类必须实现execute方法")
    
    def stop(self):
        """停止任务"""
        self._is_running = False
        self.quit()


class RSSFetchService(BackgroundService):
    """RSS获取服务"""
    
    def __init__(self, rss_collector):
        super().__init__()
        self.rss_collector = rss_collector
    
    def execute(self):
        """执行RSS获取任务"""
        total_sources = len(self.rss_collector.sources)
        results = []
        
        for i, source in enumerate(self.rss_collector.sources):
            if not self._is_running:
                break
            
            try:
                self.progress_signal.emit(
                    int((i + 1) / total_sources * 100),
                    f"正在获取 {source['name']}"
                )
                
                items = self.rss_collector._fetch_rss(source)
                results.extend(items)
                
                self.logger.info(f"从 {source['name']} 获取了 {len(items)} 条新闻")
            except Exception as e:
                self.logger.error(f"获取 {source['name']} 失败: {str(e)}")
        
        return results
