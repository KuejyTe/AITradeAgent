"""
日志配置和结构化日志记录
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外的上下文
        if hasattr(record, "context"):
            log_data["context"] = record.context

    return json.dumps(log_data, ensure_ascii=False)
class StructuredLogger:
"""结构化日志记录器"""

def __init__(self, name: str):
    """
    初始化日志记录器
    
    Args:
        name: 日志记录器名称
    """
    self.logger = logging.getLogger(name)

def _log(self, level: int, message: str, **context):
    """记录日志"""
    extra = {"context": context} if context else {}
    self.logger.log(level, message,extra=extra)

def debug(self, message: str, **context):
    """记录DEBUG级别日志"""
    self._log(logging.DEBUG, message, **context)

def info(self, message: str, **context):
    """记录INFO级别日志"""
    self._log(logging.INFO, message, **context)

def warning(self, message: str, **context):
    """记录WARNING级别日志"""
    self._log(logging.WARNING, message, **context)

def error(self, message: str, **context):
    """记录ERROR级别日志"""
    self._log(logging.ERROR, message, **context)

def critical(self, message: str, **context):
    """记录CRITICAL级别日志"""
    self._log(logging.CRITICAL, message, **context)
def setup_logging(
log_level: str = "INFO",
log_file: str = "logs/app.log",
enable_console: bool = True
):
"""
配置日志系统

Args:
    log_level: 日志级别
    log_file: 日志文件路径
    enable_console: 是否启用控制台输出
"""
# 创建日志目录
log_path = Path(log_file)
log_path.parent.mkdir(parents=True, exist_ok=True)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, log_level.upper()))

# 清除现有处理器
root_logger.handlers.clear()

# 文件处理器
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10,
    encoding='utf-8'
)
file_handler.setFormatter(StructuredFormatter())
root_logger.addHandler(file_handler)

# 控制台处理器
if enable_console:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    root_logger.addHandler(console_handler)

# 错误日志单独文件
error_handler = logging.handlers.RotatingFileHandler(
'logs/error.log',
maxBytes=10 * 1024 * 1024,
backupCount=5,
encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(StructuredFormatter())
root_logger.addHandler(error_handler)

不同模块的日志记录器
app_logger = StructuredLogger("app")
api_logger = StructuredLogger("api")
trading_logger = StructuredLogger("trading")
strategy_logger = StructuredLogger("strategy")
